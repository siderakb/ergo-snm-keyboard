"""Bosses that hold the core board's free X ends against rocking about Y.

The core board hangs from the main board on its two 2x10 headers only (both near the middle in X), so a push at either X
end tips it about Y. Bottom plate bosses stand under both X ends (facing the F.Cu face, which looks down) and top case
bosses hang from the skin onto both X ends of the +Y strip, the only part of the core board the main board does not
cover. Both stop CORE_SUPPORT_GAP short of the board.

Each boss is a zone (params.CORE_SUPPORT_*_ZONES, KiCad coordinates of the core board, one per X end) less everything
it must not touch, grown by CORE_SUPPORT_CLEAR: the courtyards of the parts on that face, the through-hole pads (their
pins stick out of both faces), the placeholders without a courtyard (slide switch), the board edge; the main board for
the top bosses, the battery door pocket for the bottom ones. Thin or small leftovers are dropped.
"""

import functools
import math

from shapely.geometry import MultiPoint, Point, Polygon, box
from shapely.ops import unary_union

import params
import pcb_ref
from geometry import outline_in_case, to_case

BOARD = "core_board_e73"


def _unfitted(hand):
    """Refs whose footprint carries no part for `hand`: the other hand's USB-C / switch slots, and J7 unless fitted."""
    slots = {r for refs in (params.CORE_USB_REFS, params.CORE_SWITCH_REFS) for v in refs.values() for r in v}
    fitted = set(params.CORE_USB_REFS.get(hand, ())) | set(params.CORE_SWITCH_REFS.get(hand, ()))
    return (slots - fitted) | (set() if params.CORE_J7_POPULATED else {"J7"})


def _fp_geometry(hand):
    """[(layer, courtyard Polygon | None, [pad Polygon])] of the fitted core board footprints in the case frame (TH pads
    only; an unfitted footprint's pads are flush with the board, so a boss may sit on them)."""
    out = []
    skip = _unfitted(hand)
    for fp in pcb_ref._children(pcb_ref.load_board(params.BOARD_SOURCE[BOARD]), "footprint"):
        if next((p[2] for p in pcb_ref._children(fp, "property") if p[1] == "Reference"), "?") in skip:
            continue
        at = pcb_ref._children(fp, "at")[0]
        ox, oy, r = float(at[1]), float(at[2]), math.radians(float(at[3]) if len(at) > 3 else 0.0)
        c, s = math.cos(r), math.sin(r)
        case = lambda p, ox=ox, oy=oy, c=c, s=s: to_case(BOARD, ox + p[0] * c + p[1] * s, oy - p[0] * s + p[1] * c, hand=hand)[:2]
        crt, pads = [], []
        for g in fp:
            if not (isinstance(g, list) and g):
                continue
            if g[0].startswith("fp_") and any(isinstance(e, list) and e[0] == "layer" and "CrtYd" in e[1] for e in g):
                if g[0] == "fp_rect":                                    # two corners: add the other two
                    (x0, y0), (x1, y1) = (pcb_ref._xy(pcb_ref._children(g, k)[0]) for k in ("start", "end"))
                    crt += [case((x0, y1)), case((x1, y0))]
                for key in ("start", "end", "center", "mid"):
                    crt += [case(pcb_ref._xy(e)) for e in pcb_ref._children(g, key)]
                for pn in pcb_ref._children(g, "pts"):
                    crt += [case(pcb_ref._xy(e)) for e in pcb_ref._children(pn, "xy")]
            elif g[0] == "pad" and g[2] in ("thru_hole", "np_thru_hole"):
                size = pcb_ref._children(g, "size")[0]
                d = max(float(size[1]), float(size[2]))
                pads.append(Point(case(pcb_ref._xy(pcb_ref._children(g, "at")[0]))).buffer(d / 2))
        layer = pcb_ref._children(fp, "layer")[0][1]
        out.append((layer, MultiPoint(crt).convex_hull if len(crt) > 2 else None, pads))
    return out


def _zone(hand, kx0, ky0, kx1, ky1):
    return MultiPoint([to_case(BOARD, x, y, hand=hand)[:2] for x in (kx0, kx1) for y in (ky0, ky1)]).envelope


def _board(hand, name):
    return Polygon(max(outline_in_case(name, hand), key=lambda l: Polygon(l).area))


def _regions(hand, zones, face, extra):
    """Plan polygons: each zone less the obstacles of `face` ("F.Cu" / "B.Cu") and `extra`, grown by CORE_SUPPORT_CLEAR."""
    clear = params.CORE_SUPPORT_CLEAR
    blocked = list(extra)
    for layer, crt, pads in _fp_geometry(hand):
        blocked += pads
        if layer == face and crt is not None:
            blocked.append(crt)
    blocked = unary_union(blocked).buffer(clear)
    inside = _board(hand, BOARD).buffer(-clear)
    m = params.CORE_SUPPORT_MIN_W / 2
    out = []
    for z in zones:
        region = _zone(hand, *z).intersection(inside).difference(blocked)
        region = region.buffer(-m, join_style="mitre").buffer(m, join_style="mitre")      # drops parts thinner than MIN_W
        out += [g for g in getattr(region, "geoms", [region])
                if g.geom_type == "Polygon" and g.area >= params.CORE_SUPPORT_MIN_AREA]
    return out


@functools.lru_cache(maxsize=None)
def top_regions(hand):
    from placeholders import core_board_placeholders

    extra = [_board(hand, "main_board")]
    for label, shape in core_board_placeholders(hand).items():
        if label.startswith("switch_"):                                  # B.Cu, no courtyard in the footprint
            bb = shape.bounding_box()
            extra.append(box(bb.min.X, bb.min.Y, bb.max.X, bb.max.Y))
    return tuple(_regions(hand, params.CORE_SUPPORT_TOP_ZONES, "B.Cu", extra))


@functools.lru_cache(maxsize=None)
def bottom_regions(hand):
    import batterydoor

    x0, y0, x1, y1 = batterydoor.layout(hand)["pocket"]
    g = params.BATTERY_POCKET_CLEAR
    return tuple(_regions(hand, params.CORE_SUPPORT_BOTTOM_ZONES, "F.Cu", [box(x0 - g, y0 - g, x1 + g, y1 + g)]))


def core_faces_z():
    """(upper face Z, lower face Z) of the core board: B.Cu up, BOARD_GAP below the main board's lower face (Z = 0)."""
    return -params.BOARD_GAP, -params.BOARD_GAP - params.PCB_T


def top_bosses(hand):
    """Solids hanging from the skin underside (overlapping it by 0.5) to CORE_SUPPORT_GAP above the core board."""
    from build123d import Pos, Solid
    from topcase import _face

    top = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T + 0.5
    bottom = core_faces_z()[0] + params.CORE_SUPPORT_GAP
    return [Pos(0, 0, bottom) * Solid.extrude(_face(p), (0, 0, top - bottom)) for p in top_regions(hand)]


def bottom_bosses(hand):
    """Solids from below the plate's outer face up to CORE_SUPPORT_GAP under the core board (the caller trims them)."""
    from build123d import Pos, Solid
    from topcase import _face, floor_z

    top = core_faces_z()[1] - params.CORE_SUPPORT_GAP
    out = []
    for p in bottom_regions(hand):
        base = min(floor_z(hand, x, y) for x, y in p.exterior.coords) - 1.0
        out.append(Pos(0, 0, base) * Solid.extrude(_face(p), (0, 0, top - base)))
    return out
