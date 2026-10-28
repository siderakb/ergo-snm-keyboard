"""Bottom case: a plate inside the top case walls, with feet columns and support pillars.

Its outer face follows `topcase.below_floor`, BOTTOM_RECESS up from the bottom edge of the walls, so the seam only shows
from below. The M2.5 screws go up through it into the nuts at the lower ends of the top case posts (heads in shallow
counterbores). Feet columns stand perpendicular to the tented desk plane (`desk_plane`); support pillars rise through the
main board's mounting holes to the skin underside. The plate carries the battery door (batterydoor.py). The right hand
uses the left feet and ribs mirrored (params.MIRROR_X), except the thumb foot, which stands under the trackball pod.
"""

import functools

import numpy as np
from build123d import Align, Box, Cone, Cylinder, Location, Plane, Pos
from shapely.geometry import MultiPolygon
from shapely.geometry import box as sbox

import batterydoor
import outline
import params
import pcb_ref
import topcase
from geometry import mirror_shape, mirror_x, to_case
from topcase import _along, below_floor, floor_z, post_axis


def bottom_outline(hand):
    """Plan outline of the plate: the inner face of the top case walls, less the side clearance."""
    return outline.case_outline_polygon(hand).buffer(-params.BOTTOM_WALL - params.PLATE_SIDE_CLEAR)


@functools.lru_cache(maxsize=None)
def desk_plane(hand):
    """(unit normal, d) of the desk in the case frame, n . p = d: tilted by TENT_ANGLE about Y with the inner side up
    (+X on the left hand, -X on the right), as
    high as the lowest point of the case allows (the walls' bottom edge along the outline, plus pads and clearance). The right
    hand's lowest point is the trackball pod; the left hand takes the right hand's desk plane mirrored (user: both halves the same
    height, so the left feet are as much longer than they would need to be as the pod makes the right ones)."""
    t = np.radians(params.TENT_ANGLE)
    n = np.array((np.sin(t) * (1.0 if hand == "left" else -1.0), 0.0, np.cos(t)))
    if hand == "left":                                   # mirror X -> MIRROR_X - X: n . p = d  <->  n' . p' = d + sin(t) * MIRROR_X
        return n, float(desk_plane("right")[1] + np.sin(t) * params.MIRROR_X)
    ring = outline.case_outline_polygon(hand).exterior
    pts = [ring.interpolate(s) for s in np.arange(0.0, ring.length, 1.0)]
    low = min(n @ np.array((p.x, p.y, floor_z(hand, p.x, p.y, -params.BOTTOM_RECESS, pod=False))) for p in pts)
    if hand == "right":                                  # the trackball pod hangs below the walls
        import trackball

        low = min([low] + [float(n @ p) for p in trackball.lowest_points()])
    return n, float(low - params.FOOT_END_T - params.FOOT_MIN_CLEAR)


def _foot_axes(hand, on_door):
    """[(top point, desk normal, desk d)] of the feet columns: the axis runs from `top` down along -n."""
    n, d = desk_plane(hand)
    out = []
    for i, (x, y) in enumerate(params.FEET_LEFT):
        if hand == "right":
            import trackball

            x, y = trackball.foot_xy() if i == params.THUMB_FOOT else (mirror_x(x), y)
        if batterydoor.on_door(hand, x, y) != on_door:
            continue
        # start inside the plate, low enough that the tilted top disc stays under its inner face
        sink = params.FOOT_D / 2 * np.sin(np.radians(params.TENT_ANGLE)) + 0.1
        z = batterydoor.levels(hand)["nest"] if on_door else floor_z(hand, x, y, params.BOTTOM_WALL)     # (a foot may stand under the nest)
        out.append((np.array((x, y, z - sink)), n, d))
    return out


def _floor_normal(hand, x, y, e=1.0):
    fx = (floor_z(hand, x + e, y) - floor_z(hand, x - e, y)) / (2 * e)
    fy = (floor_z(hand, x, y + e) - floor_z(hand, x, y - e)) / (2 * e)
    v = np.array((-fx, -fy, 1.0))
    return v / np.linalg.norm(v)


def foot_flares(hand, on_door=False):
    """Conical flares at the column roots (the strengthening for the long thin columns), as raw cones: clip them to the
    plate envelope (or the door slab). The wide end sits just inside the floor, tilted like the column axis."""
    r, rw = params.FOOT_D / 2, params.FOOT_D / 2 + params.FOOT_FLARE_R
    out = []
    for top, n, _ in _foot_axes(hand, on_door):
        x, y = top[0], top[1]
        rel = np.arccos(np.clip(n @ _floor_normal(hand, x, y), -1.0, 1.0))        # axis against the floor normal
        h = 0.3 + rw * np.sin(rel)                                                # lowest rim point 0.3 above the floor
        p0 = top + n * ((floor_z(hand, x, y) + h / n[2] - top[2]) / n[2])
        out.append(Location(Plane(origin=tuple(p0), z_dir=tuple(-n))) * Cone(rw, r, params.FOOT_FLARE_L, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out


def feet(hand, on_door=False):
    """Feet columns: from the plate's inner face (or the battery door's top) down along the desk normal to FOOT_END_T
    above the desk, with a FOOT_PAD_D rubber pad recess in the end. on_door picks the feet standing on the battery door."""
    out = []
    for top, n, d in _foot_axes(hand, on_door):
        length = n @ top - (d + params.FOOT_END_T)
        plane = Plane(origin=tuple(top), z_dir=tuple(-n))
        column = Location(plane) * Cylinder(params.FOOT_D / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
        r, depth = (params.FOOT_PAD_D + params.FOOT_PAD_RECESS_CLEAR) / 2, params.FOOT_PAD_RECESS
        recess = Location(plane) * Pos(0, 0, length - depth) * Cylinder(r, depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        out.append(column - recess)
    return out


def button_holes(hand):
    """Vertical holes through the bottom plate over the fitted tact button's centre (main board lower face), both hands."""
    from assembly import load_boards
    from geometry import location

    board = next(b for b in load_boards(hand) if b.label == "main_board")
    holes = []
    for c in board.children:
        if c.label.startswith("SW_SPST_TL3342"):
            bb = (location("main_board", hand) * c).bounding_box()
            x, y = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
            holes.append(Pos(x, y, -60.0) * Cylinder(params.BUTTON_HOLE_D / 2, 120.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return holes


def label_centre(hand):
    x, y = params.LABEL_CENTRE
    return (x, y) if hand == "right" else (params.MIRROR_X - x, y)


def label_text(hand):
    """The raised label (params.LABEL_*) on the plate's inner face, standing LABEL_HEIGHT above it; reads correctly looking down on
    the face (X to the right), both hands (the left one at the mirrored spot)."""
    from build123d import FontStyle, Text, extrude

    x, y = label_centre(hand)
    plane = Plane(origin=(x, y, floor_z(hand, x, y, params.BOTTOM_WALL) - 0.1), x_dir=(1, 0, 0), z_dir=(0, 0, 1))   # normal up, X right, Y up
    text = Text(chr(10).join(params.LABEL_LINES), params.LABEL_SIZE, font_style=FontStyle.BOLD)
    return Location(plane) * extrude(text, amount=params.LABEL_HEIGHT + 0.1)


def support_holes(hand):
    """{ref: (x, y)} of the main-board mounting holes used for support pillars, in the case frame."""
    holes = {r: (x, y) for r, x, y in pcb_ref.mounting_holes(pcb_ref.load_board(params.BOARD_SOURCE["main_board"]))}
    return {r: tuple(to_case("main_board", *holes[r], 0.0, hand=hand)[:2]) for r in params.SUPPORT_HOLES}


def pillars(hand):
    """Pillar body from the plate up to PILLAR_TOP_Z (below the sockets), a pin through the hole to the skin underside with a
    45 degree shoulder at its root and a chamfered tip."""
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    out = []
    mn = (Align.CENTER, Align.CENTER, Align.MIN)
    r, c = params.PIN_D / 2, params.PIN_TIP_CHAMFER
    for x, y in support_holes(hand).values():
        inner = floor_z(hand, x, y, params.BOTTOM_WALL)
        # sunk deep: the caller trims everything below the outer face (a ramp drops it by up to the body's radius)
        base = min(floor_z(hand, x + params.PILLAR_D / 2 * np.cos(a), y + params.PILLAR_D / 2 * np.sin(a))
                   for a in np.linspace(0, 2 * np.pi, 16, endpoint=False)) - 0.5
        if params.PILLAR_TOP_Z > base:
            out.append(Pos(x, y, base) * Cylinder(params.PILLAR_D / 2, params.PILLAR_TOP_Z - base, align=mn))
        z0 = min(base, params.PILLAR_TOP_Z)
        out.append(Pos(x, y, z0) * Cylinder(r, skin_under - c - z0, align=mn))
        out.append(Pos(x, y, skin_under - c - 0.01) * Cone(r, r - c, c + 0.01, align=mn))
        top = params.PILLAR_TOP_Z + params.PIN_SHOULDER_UP
        s = min(params.PIN_SHOULDER, top - inner)
        if s > 0.05:
            out.append(Pos(x, y, top - s) * Cone(r + s, r, s + 0.01, align=mn))
    return out


def ribs(hand):
    """Ribs on the plate's inner face (left): an edge rim along the +Y and +X plate edge on the deep level, and a bar across
    the strip between the battery opening and the pocket's +Y end, with a gap for the wire. Posts are kept clear.
    Right hand: the left ribs mirrored."""
    if hand == "right":
        return [mirror_shape(r) for r in ribs("left")]
    f, lay, z = topcase.floor_profile(hand), batterydoor.layout(hand), batterydoor.levels(hand)
    plate = bottom_outline(hand)
    from assembly import load_boards

    core = next(b for b in load_boards(hand) if b.label == "core_board_e73").bounding_box()
    x_start, y_flat = max(f["x_pts"][4][0], core.max.X + 1.0), f["y_flat"]          # clear of the core board's USB-C at +Y
    band = plate.difference(plate.buffer(-params.RIB_T)).intersection(sbox(x_start, y_flat, x_start + 500, 500))
    band = MultiPolygon([g for g in getattr(band, "geoms", [band]) if g.geom_type == "Polygon" and g.area > 1.0])
    z0 = z["bottom"] + params.BOTTOM_WALL - 0.1
    slab = Pos(0, 0, z0 + (params.EDGE_RIB_H + 0.1) / 2) * Box(1000, 1000, params.EDGE_RIB_H + 0.1)
    edge = topcase._prism(band) & slab
    pocket = batterydoor._box(lay["pocket"], z["bottom"] - 5.0, z["ceiling"], grow=params.BATTERY_POCKET_CLEAR)
    edge = edge - pocket                                                             # the pocket (and the sliding door) stays free
    px0, _, px1, _ = lay["pocket"]
    px0 = max(px0, x_start)                                                          # nor under the USB-C
    y0 = lay["opening"][3] + params.STRIP_RIB_GAP
    strip = batterydoor._box((px0, y0, px1, y0 + params.RIB_T), z["rim"] - 0.1, z["rim"] + params.STRIP_RIB_H)
    cx, w = (lay["holder"][0] + lay["holder"][2]) / 2, params.STRIP_RIB_NOTCH_W / 2
    strip = strip - batterydoor._box((cx - w, y0 - 1.0, cx + w, y0 + params.RIB_T + 1.0), z["rim"] - 1.0, z["rim"] + params.STRIP_RIB_H + 1.0)
    out = []
    for rib in (edge, strip):
        for x, y in topcase.post_positions(hand):
            rib = rib - Pos(x, y, -50) * Cylinder(params.BOSS_D / 2 + 0.3, 100)
        out.append(rib)
    return out


def bottom_case(hand=None):
    hand = hand or params.HAND
    envelope = outline.plan_prism(hand, bottom_outline(hand)) & below_floor(hand, params.BOTTOM_WALL, pod=False)
    outer_below = below_floor(hand, pod=False)
    body = envelope - outer_below
    zone = envelope                                      # where feet and flares may be: the plate, and the pod's shell
    if hand == "right":                                  # the trackball pod hangs below the plate
        import trackball

        shell = trackball.pod_shell()
        for w in trackball.fpc_windows():                # cable windows through the plate ring and the pod wall
            shell = shell - w
        body = body - trackball.pod_cavity() - trackball.fpc_windows()[0] - trackball.fpc_windows()[1] + shell
        zone = envelope - trackball.pod_cavity() + shell
    rim = batterydoor.plate_rim(hand) & topcase._prism(bottom_outline(hand))      # the lap stays on the plate
    for x, y in topcase.post_positions(hand):                       # the top case posts stand on the plate
        rim = rim - Pos(x, y, -50) * Cylinder(params.BOSS_D / 2 + 0.3, 100)
    body = body + rim
    for c in batterydoor.plate_cuts(hand):
        body = body - c
    for rib in ribs(hand):
        body = body + rib
    for flare in foot_flares(hand):
        body = body + (flare & zone)
    for x, y in topcase.post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        body = body - _along(top, n, t - 1.0, params.BOTTOM_WALL + 2.0, params.BOTTOM_SCREW_CLEAR_D / 2)
    for c in topcase.screw_counterbores(hand):
        body = body - c
    for c in button_holes(hand):
        body = body - c
    label = label_text(hand)
    if label is not None:
        body = body + label
    if hand == "right":                                  # board standoffs; the board screws come up through the pod floor
        import trackball

        for s in trackball.standoffs():
            body = body + s
        for c in trackball.mount_cuts():
            body = body - c
    for part in feet(hand):                              # on a ramp the column's flat top would stick out of the inner face
        body = body + (part & zone)
    for part in pillars(hand):                           # ... and a pillar's flat base out of the outer face
        body = body + (part - outer_below)
    solids = sorted(body.solids(), key=lambda s: s.volume)
    assert all(s.volume < 0.1 for s in solids[:-1]), "bottom case falls apart"
    return solids[-1]                                    # drops boolean slivers (counterbore against a ramp)


def battery_door(hand=None):
    """The battery door (locked position) with its feet."""
    hand = hand or params.HAND
    body = batterydoor.door(hand)
    z = batterydoor.levels(hand)
    slab = batterydoor._box(batterydoor.layout(hand)["door"], z["bottom"] - 20.0, z["top"])        # flares stay on the door
    slab = slab - batterydoor.nest(hand)                                                           # the holder sits in the nest
    if batterydoor.post_notch(hand):
        slab = slab - batterydoor.post_notch(hand)
    for flare in foot_flares(hand, on_door=True):
        body = body + (flare & slab)
    above = batterydoor._box((-500.0, -500.0, 500.0, 500.0), z["bottom"] - 200.0, z["nest"])        # nothing above the nest floor
    for part in feet(hand, on_door=True):
        body = body + (part & above)
    return body
