"""Top case draft, part 2: side walls and screw posts on top of the skin from outline.py.

The shell hangs SEAM_DEPTH below the top surface (measured along the plane normal, so it follows the
folded main/thumb surface). The walls are BOTTOM_WALL thick, flush with the outline. Screw posts sit in the
free corners between the PCB outlines and the wall; each has a nut pocket open at the seam and a blind
screw hole up to the skin.
"""

import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import polylabel, unary_union
from build123d import Align, Box, Cylinder, Rot, Face, Location, Plane, Pos, Solid, Wire

import params
import outline
import pcb_ref
from geometry import local_to_case, location, outline_in_case

_BIG = outline._BIG


def _face(poly):
    def wire(ring):
        return Wire.make_polygon([(x, y, 0) for x, y in list(ring.coords)[:-1]], close=True)

    return Face(wire(poly.exterior), [wire(r) for r in poly.interiors])


def _prism(poly):
    """Vertical prism of a plan region (PCB keep-outs: the boards themselves are not cut at an angle)."""
    solids = [Pos(0, 0, -100) * Solid.extrude(_face(g), (0, 0, 200)) for g in getattr(poly, "geoms", [poly])]
    return sum(solids[1:], solids[0])


def _planes(hand):
    thumb_p, thumb_n = outline.plate_plane(outline.thumb_board(hand), hand)
    main_p, main_n = np.array((0.0, 0.0, params.PCB_T + params.PLATE_TOP_TO_PCB_TOP)), np.array((0.0, 0.0, 1.0))
    return (main_p, main_n), (thumb_p, thumb_n)


def _under(hand, shift):
    """Everything below both top planes, each moved `shift` down along its normal."""
    (mp, mn), (tp, tn) = _planes(hand)
    return outline._half_space(mp, mn, shift) & outline._half_space(tp, tn, shift)


def pcb_union(hand):
    """Plan footprint of everything that must not touch a post: main and core board and the thumb area."""
    polys = []
    for board in ("main_board", "core_board_e73"):
        loops = outline_in_case(board, hand)
        polys.append(Polygon(max(loops, key=lambda l: Polygon(l).area)))
    board = outline.thumb_board(hand)
    polys.append(MultiPoint(outline._board_plan_points(board, hand, params.THUMB_BOARDS[board]["x_range"])).convex_hull.buffer(params.THUMB_TILT_MARGIN, join_style="mitre"))
    return unary_union(polys)


def post_positions(hand, count=params.BOSS_COUNT, step=0.5):
    """Screw post centres: farthest-point spread over the free area around the PCBs (grid `step`)."""
    r = params.BOSS_D / 2
    inner = outline.case_outline_polygon(hand).buffer(-params.BOTTOM_WALL)
    free = inner.buffer(-(r - 1.0)).difference(pcb_union(hand).buffer(params.BOSS_PCB_CLEAR + r))
    x0, y0, x1, y1 = free.bounds
    cand = [(x, y) for x in np.arange(x0, x1, step) for y in np.arange(y0, y1, step) if free.contains(Point(x, y))]
    if not cand:
        return []
    cand = np.array(cand)
    chosen = [cand[np.argmax(np.hypot(cand[:, 0] - cand[:, 0].mean(), cand[:, 1] - cand[:, 1].mean()))]]
    while len(chosen) < count:
        d = np.min([np.hypot(cand[:, 0] - c[0], cand[:, 1] - c[1]) for c in chosen], axis=0)
        if d.max() < 2 * r:
            break
        chosen.append(cand[np.argmax(d)])
    out = [tuple(float(v) for v in c) for c in chosen]
    if hand == "left":
        out += [_strip_centre(hand, c) for c in params.BOSS_EXTRA_LEFT]
    return out


def _strip_centre(hand, near, reach=8.0):
    """Centre of the widest part of the strip between the PCB clearance and the case outline, near `near`."""
    strip = outline.case_outline_polygon(hand).difference(pcb_union(hand).buffer(params.BOSS_PCB_CLEAR))
    strip = strip.intersection(Point(near).buffer(reach))
    pole = max(getattr(strip, "geoms", [strip]), key=lambda g: g.area)
    p = polylabel(pole, 0.05)
    return (p.x, p.y)


def _seam_point_and_normal(hand, x, y):
    """Point on the seam surface under plan position (x, y) and the unit normal of the local top plane."""
    (mp, mn), (tp, tn) = _planes(hand)
    z = lambda p, n: p[2] - (n[0] * (x - p[0]) + n[1] * (y - p[1])) / n[2]
    p, n = (mp, mn) if z(mp, mn) <= z(tp, tn) else (tp, tn)    # the lower plane is the top surface there
    point = np.array((x, y, z(p, n)))
    return point - params.SEAM_DEPTH * n, n


def walls(hand):
    outer = outline.case_outline_polygon(hand)
    ring = outer.difference(outer.buffer(-params.BOTTOM_WALL))
    shell = (outline.plan_prism(hand, ring) & _under(hand, 0.0)) - _under(hand, params.SEAM_DEPTH)
    for c in pockets(hand):
        shell = shell - c
    return shell


def pockets(hand):
    """Nut pockets and screw holes of every post (also cut out of the wall where a pocket overlaps it)."""
    cuts = []
    r_nut = (params.NUT_M25_OD + params.NUT_POCKET_CLEAR) / 2
    for x, y in post_positions(hand):
        seam, n = _seam_point_and_normal(hand, x, y)
        plane = Plane(origin=tuple(seam - 1.0 * n), z_dir=tuple(n))
        nut_depth = params.NUT_M25_H + 0.5
        hole_len = params.SEAM_DEPTH - params.PLATE_T - 0.5
        cuts.append(Location(plane) * Cylinder(r_nut, 1.0 + nut_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(Location(plane) * Cylinder(params.SCREW_M25_CLEAR_D / 2, 1.0 + hole_len, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return cuts


def posts(hand):
    """Post bodies (fused to the skin) with the nut pockets and screw holes cut out."""
    body = None
    zone = _under(hand, params.PLATE_T) - _under(hand, params.SEAM_DEPTH)   # touches the skin underside; fused later
    for x, y in post_positions(hand):
        cyl = Pos(x, y, 0) * Cylinder(params.BOSS_D / 2, 200, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        body = cyl if body is None else body + cyl
    if body is None:
        return None
    keep_out = pcb_union(hand).buffer(params.BOSS_PCB_CLEAR)     # trims bosses that do not fit whole
    body = body & zone & outline.plan_prism(hand, outline.case_outline_polygon(hand)) - _prism(keep_out)
    for c in pockets(hand):
        body = body - c
    return body


def key_cutouts(hand):
    """Square Choc housing openings (SWITCH_BODY + CUTOUT_COMP) through the skin, one per switch of the main
    board and the thumb board, each along its own plate normal (so the tilted thumb keys are cut square)."""
    side = params.SWITCH_BODY + params.CUTOUT_COMP
    thumb = outline.thumb_board(hand)
    x_lo, x_hi = params.THUMB_BOARDS[thumb]["x_range"]
    cuts = []
    for board in ("main_board", thumb):
        z_top = -params.PLATE_TOP_TO_PCB_TOP if hand == "left" else params.PCB_T + params.PLATE_TOP_TO_PCB_TOP
        for _, x, y, rot in pcb_ref.switches(pcb_ref.load_board(params.BOARD_SOURCE[board])):
            if board == thumb and not x_lo <= x <= x_hi:
                continue
            box = Box(side, side, 2 * params.PLATE_T + 2.0)
            cuts.append(location(board, hand) * Pos(x, -y, z_top) * Rot(0, 0, -rot) * box)
    return cuts


def relief_cutouts(hand):
    """Pockets in the skin underside over every PCB part that stands taller than PLATE_PCB_GAP on the plate
    side: the bounding box of the part above the board face, grown by RELIEF_XY_CLEAR and topped
    RELIEF_Z_CLEAR above the part. Taken from the placed STEP models, so the 2x10 socket pins are included."""
    from assembly import load_boards      # assembly imports this module for its viewer

    face, s = (0.0, -1.0) if hand == "left" else (params.STEP_PCB_T, 1.0)    # plate-side face, direction away from the PCB
    thumb = outline.thumb_board(hand)
    cuts = []
    for placed in load_boards(hand):
        if placed.label not in ("main_board", thumb):
            continue
        local = location(placed.label, hand).inverse() * placed
        slab = Pos(0, 0, face + s * 50) * Box(2000, 2000, 100)
        for child in local.children:
            bb = child.bounding_box()
            reach = (face - bb.min.Z) if s < 0 else (bb.max.Z - face)
            if reach <= params.PLATE_PCB_GAP - params.RELIEF_Z_CLEAR + 1e-6:
                continue
            for solid in child.solids():
                piece = solid & slab
                if not piece or piece.volume < 1e-6:
                    continue
                b = piece.bounding_box()
                h = (face - b.min.Z) if s < 0 else (b.max.Z - face)
                if h <= params.PLATE_PCB_GAP - params.RELIEF_Z_CLEAR:
                    continue
                c = params.RELIEF_XY_CLEAR
                depth = h + params.RELIEF_Z_CLEAR
                box = Box(b.size.X + 2 * c, b.size.Y + 2 * c, depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                z0 = face - 1.0 if s > 0 else face - depth      # 1 mm overlap on the PCB side, `depth` the other way
                cuts.append(location(placed.label, hand) * Pos((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2, z0) * box)
    return cuts


def led_slots(hand):
    """Light-guide slot over each LED (the one fitted on the plate-side face): LED footprint plus
    RELIEF_XY_CLEAR wide, running along the board Y axis to the nearest key opening it is in line with."""
    from assembly import load_boards

    side = params.SWITCH_BODY + params.CUTOUT_COMP
    depth = params.PLATE_T - params.LED_SLOT_SKIN
    face, s = (0.0, -1.0) if hand == "left" else (params.STEP_PCB_T, 1.0)
    cuts = []
    for placed in load_boards(hand):
        if placed.label != "main_board":
            continue
        keys = [(x, -y) for _, x, y, _ in pcb_ref.switches(pcb_ref.load_board(params.BOARD_SOURCE["main_board"]))]
        local = location("main_board", hand).inverse() * placed
        for child in local.children:
            if not child.label.startswith("LED_"):
                continue
            b = child.bounding_box()
            if (b.min.Z + b.max.Z) / 2 * s < face * s:        # the LED footprint is fitted on both faces: only the plate-side one
                continue
            lx, ly = (b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2
            best = None
            for kx, ky in keys:
                if abs(kx - lx) >= side / 2:
                    continue
                d = 1.0 if ky > ly else -1.0
                edge = ky - d * side / 2
                if best is None or abs(edge - ly) < abs(best[1] - ly):
                    best = (d, edge)
            if best is None:
                continue
            d, edge = best
            c = params.RELIEF_XY_CLEAR
            far = (b.min.Y - c) if d > 0 else (b.max.Y + c)
            end = edge + d * 0.5                                  # reaches into the opening
            y0, y1 = sorted((far, end))
            box = Box(b.size.X + 2 * c, y1 - y0, depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
            z0 = face - 1.0 if s > 0 else face - depth
            cuts.append(location("main_board", hand) * Pos(lx, (y0 + y1) / 2, z0) * box)
    return cuts


def top_skin_keyed(hand):
    skin = outline.top_skin(hand)
    for c in key_cutouts(hand) + relief_cutouts(hand) + led_slots(hand):
        skin = skin - c
    return skin


def top_case(hand=None):
    """Skin + walls + posts as one fused solid, with the nut pockets and screw holes cut."""
    hand = hand or params.HAND
    body = top_skin_keyed(hand) + walls(hand)
    p = posts(hand)
    if p is not None:
        body = body + p      # walls and posts are already cut by the pockets; the skin stays whole above them
    return body


def top_case_draft(hand=None):
    """Separate pieces for viewing: skin, walls, posts (colours in viz.py)."""
    hand = hand or params.HAND
    out = {"top_skin": top_skin_keyed(hand), "top_walls": walls(hand)}
    p = posts(hand)
    if p is not None:
        out["top_posts"] = p
    return out
