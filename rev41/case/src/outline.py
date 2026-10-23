"""Top case outline draft: one exterior skin over the whole keyboard half.

The top case is a cosmetic part, so its plan outline does not follow the PCB steps: it is the convex
hull of the main board, the core board and the thumb area, grown by OUTLINE_OFFSET. The top surface is the
lower of two planes -- the flat main plate plane and the tilted thumb plane -- so they meet along a crease;
the skin is that surface and the same surface PLATE_T lower. No walls, key holes or cut-outs yet.
"""

import math

import numpy as np
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union
from build123d import Box, Face, Kind, Location, Plane, Pos, Solid, Wire

import params
import pcb_ref
from geometry import location, placement, to_case

OUTLINE_OFFSET = params.BOTTOM_CLEAR + params.BOTTOM_WALL   # PCB edge -> outer wall face: 0.5 + 2.0
_BIG = 2000.0
CONCAVE_FILLET = 2.5      # one radius for every corner (convex and concave) of the left-hand outline


def _hull(points):
    """Convex hull (counter-clockwise) of (x, y) points, Andrew's monotone chain."""
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def thumb_board(hand):
    return "thumb_2x3" if hand == "left" else "thumb_1x2"


def _board_plan_points(board, hand, x_range=None):
    """Plan (X, Y) points of a board's outline (corners of the x range for the thumb panel)."""
    source = params.BOARD_SOURCE[board]
    loops = pcb_ref.outline_loops(pcb_ref.load_board(source))
    if x_range:
        y0 = min(y for l in loops for _, y in l)
        y1 = max(y for l in loops for _, y in l)
        pts = [(x, y) for x in x_range for y in (y0, y1)]
    else:
        pts = [p for l in loops for p in l]
    return [to_case(board, x, y, hand=hand)[:2] for x, y in pts]


def case_outline_points(hand=None):
    """Points whose convex hull is the top case plan outline: PCB outlines, thumb area, trackball hole."""
    hand = hand or params.HAND
    pts = _board_plan_points("main_board", hand) + _board_plan_points("core_board_e73", hand)
    board = thumb_board(hand)
    pts += _board_plan_points(board, hand, params.THUMB_BOARDS[board]["x_range"])
    if hand == "right":                      # the trackball replaces the inner 2x2 keys
        cx, cy, _ = params.BALL_HOLE_CENTER_RIGHT
        r = params.BALL_HOLE_D / 2
        pts += [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    return pts


def _left_outline_polygon(offset=OUTLINE_OFFSET, fillet=CONCAVE_FILLET):
    """Left hand: main + core board area, the thumb area and a narrow bridge between them, grown by
    `offset`, concave corners rounded with `fillet` (a closing). Not the convex hull of everything."""
    hand = "left"
    main_pts = _board_plan_points("main_board", hand)
    # the main board's bottom edge is one straight line parallel to X: add its two bottom corners
    x_lo, x_hi, y_lo = min(p[0] for p in main_pts), max(p[0] for p in main_pts), min(p[1] for p in main_pts)
    main_area = MultiPoint(main_pts + _board_plan_points("core_board_e73", hand) + [(x_lo, y_lo), (x_hi, y_lo)]).convex_hull
    board = thumb_board(hand)
    thumb_pts = _board_plan_points(board, hand, params.THUMB_BOARDS[board]["x_range"])
    thumb_area = MultiPoint(thumb_pts).convex_hull.buffer(params.THUMB_TILT_MARGIN, join_style="mitre")
    # the thumb walls are cut perpendicular to the tilted plate, so at depth they lean towards the main board:
    # push the downhill end out by that lean at the PCB underside
    _, n = plate_plane(board, hand)
    lean = (params.PLATE_TOP_TO_PCB_TOP + params.PCB_T) * math.hypot(n[0], n[1]) / n[2]
    fall = np.array(n[:2]) / math.hypot(n[0], n[1])
    thumb_area = MultiPoint(list(thumb_area.exterior.coords) + [(x + lean * fall[0], y + lean * fall[1]) for x, y in thumb_area.exterior.coords]).convex_hull
    thumb_pts = list(thumb_area.exterior.coords)[:-1]       # the grown corners: the bridge lines must lie on its edges
    # bridge: the thumb corners on the main side plus the main board's right-edge bottom corner and the
    # point of that edge level with the upper thumb corner (not the main hull's far-away vertices)
    thumb_inner = sorted(thumb_pts, key=lambda p: np.hypot(p[0] - main_area.centroid.x, p[1] - main_area.centroid.y))[:2]
    y_up = min(max(p[1] for p in thumb_inner), max(p[1] for p in main_pts))
    bridge = MultiPoint([(x_hi, y_lo), (x_hi, y_up)] + thumb_inner).convex_hull
    # the thumb area's lower long edge is extended up to the main board's bottom line (fills the notch)
    a = min(thumb_inner, key=lambda p: p[1])
    b = min((p for p in thumb_pts if p not in thumb_inner), key=lambda p: np.hypot(p[0] - a[0], p[1] - a[1]))
    q = (a[0] + (y_lo - a[1]) * (b[0] - a[0]) / (b[1] - a[1]), y_lo)
    fill = MultiPoint([q, a, (x_hi, y_lo)]).convex_hull
    # likewise the upper long edge is extended back to the main board's right edge line
    a2 = max(thumb_inner, key=lambda p: p[1])
    b2 = min((p for p in thumb_pts if p not in thumb_inner), key=lambda p: np.hypot(p[0] - a2[0], p[1] - a2[1]))
    q2 = (x_hi, a2[1] + (x_hi - a2[0]) * (b2[1] - a2[1]) / (b2[0] - a2[0]))
    fill2 = MultiPoint([q2, a2, (x_hi, a2[1])]).convex_hull
    # sharp offset first, then every corner (convex and concave) gets the same radius
    grown = unary_union([main_area, thumb_area, bridge, fill, fill2]).buffer(offset, join_style="mitre", mitre_limit=10)
    rounded = grown.buffer(-fillet, quad_segs=16).buffer(fillet, quad_segs=16)
    return rounded.buffer(fillet, quad_segs=16).buffer(-fillet, quad_segs=16)


def case_outline_polygon(hand=None, offset=OUTLINE_OFFSET):
    """Plan outline of the top case as a shapely polygon (already grown by `offset`)."""
    hand = hand or params.HAND
    if hand == "left":
        return _left_outline_polygon(offset)
    return Polygon(_hull(case_outline_points(hand))).buffer(offset, quad_segs=16)


def plate_plane(board, hand):
    """(point, upward unit normal) of the plate top plane over a thumb board."""
    R, _ = placement(board, hand)
    zs_top = -params.PLATE_TOP_TO_PCB_TOP if hand == "left" else params.PCB_T + params.PLATE_TOP_TO_PCB_TOP
    from geometry import local_to_case
    point = np.array(local_to_case(board, 0.0, 0.0, zs_top, hand=hand))
    n = R[:, 2] * (-1.0 if hand == "left" else 1.0)     # local +Z points down for the flipped (left) board
    return point, n / np.linalg.norm(n)


def _half_space(point, normal, shift=0.0):
    """Solid occupying everything below the plane through `point` (normal pointing up), moved down by shift."""
    n = np.asarray(normal, float)
    x_dir = np.cross(n, (0.0, 0.0, 1.0))
    x_dir = (1.0, 0.0, 0.0) if np.linalg.norm(x_dir) < 1e-9 else tuple(x_dir / np.linalg.norm(x_dir))
    origin = tuple(np.asarray(point, float) - shift * n)
    return Location(Plane(origin=origin, x_dir=x_dir, z_dir=tuple(n))) * Pos(0, 0, -_BIG / 2) * Box(_BIG, _BIG, _BIG)


def _planes(hand):
    thumb_p, thumb_n = plate_plane(thumb_board(hand), hand)
    main_p, main_n = np.array((0.0, 0.0, params.PCB_T + params.PLATE_TOP_TO_PCB_TOP)), np.array((0.0, 0.0, 1.0))
    return (main_p, main_n), (thumb_p, thumb_n)


def _crease_point(hand):
    (mp, mn), (tp, tn) = _planes(hand)
    return np.linalg.solve(np.array([mn, tn, np.cross(mn, tn)]), np.array([mn @ mp, tn @ tp, 0.0]))


def _ring_wire(ring, z_of):
    return Wire.make_polygon([(x, y, z_of(x, y)) for x, y in list(ring.coords)[:-1]], close=True)


def plan_prism(hand, poly):
    """Plan region `poly` as a solid: a vertical prism under the main plate plane and, on the thumb side of
    the crease (the bisector plane of the two top planes), a prism perpendicular to the tilted thumb plane,
    so the thumb walls and the seam meet the plate at 90 degrees."""
    (mp, mn), (tp, tn) = _planes(hand)
    z_thumb = lambda x, y: tp[2] - ((x - tp[0]) * tn[0] + (y - tp[1]) * tn[1]) / tn[2]
    out = None
    for g in getattr(poly, "geoms", [poly]):
        vertical = Pos(0, 0, -100) * Solid.extrude(Face(_ring_wire(g.exterior, lambda x, y: 0.0), [_ring_wire(r, lambda x, y: 0.0) for r in g.interiors]), (0, 0, 200))
        face = Face(_ring_wire(g.exterior, z_thumb), [_ring_wire(r, z_thumb) for r in g.interiors])
        tilted = Pos(*(-100 * tn)) * Solid.extrude(face, tuple(200 * tn))
        c = _crease_point(hand)
        part = (vertical & _half_space(c, tn - mn)) + (tilted & _half_space(c, mn - tn))
        out = part if out is None else out + part
    return out


def top_skin(hand=None, offset=OUTLINE_OFFSET):
    """The exterior top skin (plate thickness PLATE_T): below both planes, above the same planes lowered."""
    hand = hand or params.HAND
    outline = case_outline_polygon(hand, offset)
    prism = plan_prism(hand, outline)
    (main_p, main_n), (thumb_p, thumb_n) = _planes(hand)

    def below(shift):
        return prism & _half_space(main_p, main_n, shift) & _half_space(thumb_p, thumb_n, shift)

    return below(0.0) - below(params.PLATE_T)


def top_case_draft(hand=None):
    hand = hand or params.HAND
    return {"top_skin": top_skin(hand)}
