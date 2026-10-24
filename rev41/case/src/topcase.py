"""Top case draft, part 2: side walls and screw posts on top of the skin from outline.py.

The walls run from the top surface all the way down, BOTTOM_RECESS past the outer face of the bottom plate, which sits
inside them (the seam only shows from below). The plate faces follow the folded main/thumb surface: the lower of a
plane parallel to each top plane. Screw posts sit in the free corners between the PCB outlines and the wall and run
down to the plate's inner face; each has a nut pocket open at its lower end and a blind screw hole above it.
"""

import functools

import numpy as np
from shapely.geometry import LineString, MultiPoint, Point, Polygon
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
    if hand == "left":                                        # the posts run down beside the battery holder
        from placeholders import battery_holder

        bb = battery_holder(hand).bounding_box()
        polys.append(Polygon([(bb.min.X, bb.min.Y), (bb.max.X, bb.min.Y), (bb.max.X, bb.max.Y), (bb.min.X, bb.max.Y)]))
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


@functools.lru_cache(maxsize=None)
def floor_profile(hand):
    """Outer face of the bottom plate. Main side: the shallower (higher) of two stepped profiles, one along Y (deep from the
    +Y wall to past the battery holder tail) and one along X (shallow at -X, the core board level in the middle, deep
    under the battery holder), each with BOTTOM_RAMP_ANGLE ramps; (s, z) corner points sorted by s.
    Thumb side: the plane parallel to the thumb plate, thumb_depth below it along its normal (lower envelope)."""
    from assembly import load_boards
    from placeholders import battery_holder, core_board_placeholders

    (_, _), (tp, tn) = _planes(hand)
    clear, wall = params.BOTTOM_CLEAR, params.BOTTOM_WALL
    run = lambda dz: dz / np.tan(np.radians(params.BOTTOM_RAMP_ANGLE))
    bat = battery_holder(hand).bounding_box()
    z_deep = bat.min.Z - clear - wall
    z_shallow = -(params.HOTSWAP_SOCKET_PROTRUSION + clear + wall)
    core = [b for b in load_boards(hand) if b.label == "core_board_e73"][0].bounding_box()
    z_core = min([core.min.Z] + [s.bounding_box().min.Z for s in core_board_placeholders(hand).values()]) - clear - wall
    y_flat = bat.min.Y - params.BOTTOM_DEEP_MARGIN
    # each lower level starts this far before its parts; the extra wall keeps the plate's inner (offset) corner clear too
    x_core = core.min.X - clear - wall
    x_deep = bat.min.X - clear - wall
    # screw heads must sit on a flat level, never on a ramp: a ramp moves off a post (or gets steeper)
    heads = [x for x, y in post_positions(hand) if y > y_flat]
    h = params.SCREW_HEAD_CBORE_D / 2 + 1.0
    x1 = x_core - run(z_shallow - z_core)                 # shallow -> core ramp: x1 .. x_core
    for px in heads:
        if px - h < x_core and px + h > x1:
            x1 = px + h                                   # the post stays on the shallow level
    x2 = x_deep - run(z_core - z_deep)                    # core -> deep ramp: x2 .. x_deep
    for px in heads:
        if px - h < x_deep and px + h > x2:
            x_deep = px - h                               # the post goes onto the deep level
            x2 = x_deep - run(z_core - z_deep)
    x2 = max(x2, core.max.X + clear)                      # steeper rather than into the core board
    assert x1 < x_core - 1.0 and x2 < x_deep - 1.0, "no room for the X ramps"
    big = 1000.0
    x_pts = [(-big, z_shallow), (x1, z_shallow), (x_core, z_core), (x2, z_core), (x_deep, z_deep), (big, z_deep)]
    y_pts = [(-big, z_shallow), (y_flat - run(z_shallow - z_deep), z_shallow), (y_flat, z_deep), (big, z_deep)]
    board = next(b for b in load_boards(hand) if b.label == outline.thumb_board(hand))
    reach = max(float((tp - np.array((v.X, v.Y, v.Z))) @ tn) for v in board.vertices())
    reach = max(reach, params.PLATE_TOP_TO_PCB_TOP + params.PCB_T + params.HOTSWAP_SOCKET_PROTRUSION)   # STEP has no sockets
    return {"x_pts": x_pts, "y_pts": y_pts, "z_deep": z_deep, "z_core": z_core, "z_shallow": z_shallow,
            "y_flat": y_flat, "thumb_depth": reach + clear + wall}


def _lifted(pts, lift):
    """Profile polyline moved by `lift` perpendicular to each segment (up for lift > 0), as sorted (s, z) points."""
    if abs(lift) < 1e-9:
        return list(pts)
    line = LineString(pts).offset_curve(lift, join_style="mitre")      # left of the +s direction is +z
    return sorted(line.coords)


def _profile_below(pts, axis, bounds, lift):
    """Solid below the lifted profile, extruded across the case (the profile runs along `axis`, 'x' or 'y')."""
    x0, y0, x1, y1 = bounds
    p = _lifted(pts, lift)
    ring = p + [(p[-1][0], -300.0), (p[0][0], -300.0)]
    if axis == "x":
        face = Face(Wire.make_polygon([(s, y0 - 5.0, z) for s, z in ring], close=True))
        return Solid.extrude(face, (0, y1 - y0 + 10.0, 0))
    face = Face(Wire.make_polygon([(x0 - 5.0, s, z) for s, z in ring], close=True))
    return Solid.extrude(face, (x1 - x0 + 10.0, 0, 0))


def below_floor(hand, lift=0.0):
    """Everything below the bottom plate's outer face raised by `lift`: below the higher of the X and Y profiles and
    below the thumb plane (see floor_profile). lift = BOTTOM_WALL is the plate's inner face, lift = -BOTTOM_RECESS the
    bottom edge of the top case walls."""
    (_, _), (tp, tn) = _planes(hand)
    f = floor_profile(hand)
    bounds = outline.case_outline_polygon(hand).bounds
    main = _profile_below(f["x_pts"], "x", bounds, lift) + _profile_below(f["y_pts"], "y", bounds, lift)
    return main & outline._half_space(tp, tn, f["thumb_depth"] - lift)


def floor_z(hand, x, y, lift=0.0):
    """Height of the floor surface raised by `lift` at plan position (x, y)."""
    f = floor_profile(hand)
    zx = np.interp(x, *zip(*_lifted(f["x_pts"], lift)))
    zy = np.interp(y, *zip(*_lifted(f["y_pts"], lift)))
    (_, _), (tp, tn) = _planes(hand)
    pt = tp - (f["thumb_depth"] - lift) * tn
    zt = pt[2] - (tn[0] * (x - pt[0]) + tn[1] * (y - pt[1])) / tn[2]
    return float(min(max(zx, zy), zt))


def post_axis(hand, x, y):
    """(top point, unit axis normal, length): the post under plan position (x, y) runs from the top surface down
    along the local top plane normal to the bottom plate's inner face."""
    (mp, mn), (tp, tn) = _planes(hand)
    z = lambda p, n: p[2] - (n[0] * (x - p[0]) + n[1] * (y - p[1])) / n[2]
    p, n = (mp, mn) if z(mp, mn) <= z(tp, tn) else (tp, tn)    # the lower plane is the top surface there
    top = np.array((x, y, z(p, n)))
    g = lambda t: (top - t * n)[2] - floor_z(hand, *(top - t * n)[:2], params.BOTTOM_WALL)
    lo, hi = 0.0, 80.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if g(mid) > 0 else (lo, mid)
    return top, n, float(hi)


def wall_openings(hand):
    """Openings through the top edge wall (+Y side) for the USB-C receptacles and the slide-switch handle: the
    part of each placeholder that reaches the wall, grown by WALL_OPEN_CLEAR (the handle slot also by the
    travel)."""
    from placeholders import core_board_placeholders

    from shapely.geometry import LineString

    outer = outline.case_outline_polygon(hand)
    c = params.WALL_OPEN_CLEAR
    cuts = []
    for label, shape in core_board_placeholders(hand).items():
        if not label.startswith(("usb_", "switch_")):
            continue
        bx = shape.bounding_box()
        ymax = outer.intersection(LineString([((bx.min.X + bx.max.X) / 2, -1000), ((bx.min.X + bx.max.X) / 2, 1000)])).bounds[3]
        y0, y1 = ymax - params.BOTTOM_WALL - 0.5, ymax + 1.0           # the +Y wall in front of this part
        probe = Pos(0, (y0 + y1) / 2 + 50, 0) * Box(2000, 100 + (y1 - y0), 2000)       # everything with Y > y0
        piece = shape & probe
        if not piece or piece.volume < 1e-6:
            continue
        b = piece.bounding_box()
        along = c + (params.SLIDE_SW_TRAVEL / 2 if label.startswith("switch_") else 0.0)
        cuts.append(Pos((b.min.X + b.max.X) / 2, (y0 + y1) / 2, (b.min.Z + b.max.Z) / 2)
                    * Box(b.size.X + 2 * along, y1 - y0, b.size.Z + 2 * c))
    return cuts


def walls(hand):
    """Outer walls from the top surface down to BOTTOM_RECESS below the bottom plate's outer face: the bottom plate sits
    inside them, so the seam only shows from below."""
    outer = outline.case_outline_polygon(hand)
    ring = outer.difference(outer.buffer(-params.BOTTOM_WALL))
    shell = outline.plan_prism(hand, ring) & _under(hand, 0.0) - below_floor(hand, -params.BOTTOM_RECESS)
    for c in pockets(hand) + wall_openings(hand) + screw_counterbores(hand):
        shell = shell - c
    return shell


def screw_counterbores(hand):
    """Head pockets under each post: SCREW_HEAD_SINK into the bottom plate and on down past the wall's bottom edge
    (posts close to the wall have the head partly under it)."""
    cuts = []
    for x, y in post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        start = t + params.BOTTOM_WALL - params.SCREW_HEAD_SINK
        cuts.append(_along(top, n, start, params.SCREW_HEAD_SINK + params.BOTTOM_RECESS + 1.0, params.SCREW_HEAD_CBORE_D / 2))
    return cuts


def _along(top, n, start, length, r):
    """Cylinder of radius r on the axis through `top` along -n, from `start` to `start + length` below `top`."""
    plane = Plane(origin=tuple(top - start * n), z_dir=tuple(-n))
    return Location(plane) * Cylinder(r, length, align=(Align.CENTER, Align.CENTER, Align.MIN))


def pockets(hand):
    """Nut pocket open at each post's lower end and the blind screw hole above it (also cut out of the wall where a
    pocket overlaps it)."""
    cuts = []
    r_nut = (params.NUT_M25_OD + params.NUT_POCKET_CLEAR) / 2
    nut_depth = params.NUT_M25_H + 0.5
    for x, y in post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        cuts.append(_along(top, n, t - nut_depth, nut_depth + 1.0, r_nut))
        hole = min(params.POST_HOLE_LEN, t - params.PLATE_T - 0.5)         # blind: stays 0.5 under the skin
        cuts.append(_along(top, n, t - hole, hole, params.SCREW_M25_CLEAR_D / 2))
    return cuts


def posts(hand):
    """Post bodies from the skin underside down to the bottom plate's inner face, with the pockets cut out."""
    body = None
    for x, y in post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        cyl = _along(top, n, -1.0, t + 1.0, params.BOSS_D / 2)
        body = cyl if body is None else body + cyl
    if body is None:
        return None
    keep_out = pcb_union(hand).buffer(params.BOSS_PCB_CLEAR)     # trims bosses that do not fit whole
    zone = _under(hand, params.PLATE_T) - below_floor(hand, params.BOTTOM_WALL)
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
