"""Right-hand trackball (R2): ball cup with the PMW3610 board under it, standing in a pod of the bottom plate.

Everything is built in the ball frame (`frame`): origin at the ball centre, x = u (uphill along the thumb plate, towards the
crease), y = v = n x u, z = n (thumb plate normal). Depths `w` below are along n from the ball centre.
The cup is a separate part: a spherical shell below BALL_CUP_RIM with three steel-ball seats and a seat block for the sensor
board. Four screws from below clamp pod floor (standoffs), board and shims to the cup.
"""

import functools

import numpy as np
from build123d import Align, Axis, Box, Compound, Cone, Cylinder, Location, Plane, Pos, Sphere, fillet, import_step

import geometry
import outline
import params

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
R = params.BALL_D / 2
W_BOARD = -(R + params.PMW3610_LENS_FACE_TO_SURFACE)          # board face toward the ball (nominal)
W_SENSOR = W_BOARD - params.PMW3610_BOARD_T                    # face with the IC and the FPC connector
W_SEAT = W_BOARD + params.SENSOR_SHIM_NOM                      # cup seat (shims fill the rest)
W_LOW = W_SENSOR - params.PMW3610_FPC_BOX[2]                   # lowest part of the module
W_POD_IN = W_LOW - params.BALL_POD_FLOOR_CLEAR                 # pod floor, inner face
W_POD_OUT = W_POD_IN - params.BOTTOM_WALL


@functools.lru_cache(maxsize=None)
def frame():
    """(c, u, v, n) of the ball frame in the right-hand case frame."""
    _, n = outline.plate_plane("thumb_1x2", "right")
    n = np.asarray(n, float)
    u = -np.array((n[0], n[1], 0.0))
    u -= (u @ n) * n
    u /= np.linalg.norm(u)
    return np.array(geometry.ball_center()), u, np.cross(n, u), n


def loc():
    c, u, _, n = frame()
    return Location(Plane(origin=tuple(c), x_dir=tuple(u), z_dir=tuple(n)))


def to_case(a, b, w):
    c, u, v, n = frame()
    return c + a * u + b * v + w * n


def _box(a0, a1, b0, b1, w0, w1):
    return Pos((a0 + a1) / 2, (b0 + b1) / 2, w0) * Box(a1 - a0, b1 - b0, w1 - w0, align=MIN)


def _seats(polar, azimuths):
    p, r = np.radians(polar), R + params.BEARING_BALL_D / 2
    return [np.array((r * np.sin(p) * np.cos(a), r * np.sin(p) * np.sin(a), -r * np.cos(p))) for a in np.radians(azimuths)]


def bearings():
    """Ball-frame centres of the three steel balls (touching the ball)."""
    return _seats(params.BEARING_POLAR, (0, 120, 240))


def alt_bearings():
    """The second set of seats (BEARING_POLAR_ALT, in the gaps of the first)."""
    return _seats(params.BEARING_POLAR_ALT, (60, 180, 300))


def pin_field():
    """(u0, u1, v0, v1) of U1's through-hole pins with their clearance (board local X -> v, -KiCad y -> u)."""
    cx, cy = params.PMW3610_BOARD_CENTRE
    x0, y0, x1, y1 = params.PMW3610_PIN_FIELD
    c = params.PMW3610_PIN_CLEAR
    return cy - y1 - c, cy - y0 + c, x0 - cx - c, x1 - cx + c


def board_holes():
    hx, hy = params.PMW3610_HOLES                                   # short (x) x long (y) side of the board
    return [(sa * hy / 2, sb * hx / 2) for sa in (-1, 1) for sb in (-1, 1)]      # long side along u


W_HEAD = W_POD_OUT + params.SENSOR_SCREW_HEAD_H - params.SENSOR_SCREW_PROUD           # screw head underside
W_TIP = W_HEAD + params.SENSOR_SCREW_L                                                # screw tip (nominal shim)
NUT_DEPTH = params.NUT_M25_H + 0.5


def _screw_post(a, b):
    """Nut pocket open at the seat and the blind hole above it, 0.5 past the screw tip."""
    nut = Pos(a, b, W_SEAT - 1.0) * Cylinder((params.NUT_M25_OD + params.NUT_POCKET_CLEAR) / 2, NUT_DEPTH + 1.0, align=MIN)
    w0 = W_SEAT + NUT_DEPTH - 0.01
    return [nut, Pos(a, b, w0) * Cylinder(params.SCREW_M25_CLEAR_D / 2, W_TIP + 0.5 - w0, align=MIN)]


@functools.lru_cache(maxsize=None)
def cup_local():
    """The cup in the ball frame."""
    r_in, r_out = R + params.BALL_CUP_GAP, R + params.BALL_CUP_GAP + params.BALL_CUP_WALL
    bu, bv = params.CUP_BLOCK
    body = Sphere(r_out) + _box(-bu / 2, bu / 2, -bv / 2, bv / 2, W_SEAT, params.CUP_BLOCK_TOP)
    for p in bearings() + alt_bearings():
        body = body + Pos(*p) * Sphere(params.BEARING_BOSS_D / 2)
    r_keep = params.BALL_POD_R_IN - params.BALL_POD_CLEAR    # nothing above the rim, nothing outside the pod's wall
    body = body & (Pos(0, 0, W_POD_IN - 1.0) * Cylinder(r_keep, -params.BALL_CUP_RIM - W_POD_IN + 1.0, align=MIN))
    body = body - Sphere(r_in)
    lu, lv = params.PMW3610_LENS_BOX
    c = params.LENS_WINDOW_CLEAR
    body = body - _box(-lu / 2 - c, lu / 2 + c, -lv / 2 - c, lv / 2 + c, W_SEAT - 1.0, 0.0)   # the sensor sees the ball
    body = body - _box(*pin_field(), W_SEAT - 1.0, W_SEAT + 2.0)                                # U1 pins on B.Cu
    for p in bearings() + alt_bearings():      # blind seat: the steel ball sits on its bottom, touching the ball
        k = p / np.linalg.norm(p)
        body = body - Location(Plane(origin=tuple(p - k * 2.0), z_dir=tuple(k))) * Cylinder(params.BEARING_HOLE_D / 2, 2.0 + params.BEARING_BALL_D / 2, align=MIN)
    for a, b in board_holes():
        for cut in _screw_post(a, b):
            body = body - cut
    return body


def cup():
    return loc() * cup_local()


def ball():
    return Pos(*geometry.ball_center()) * Sphere(R)


def steel_balls():
    return [loc() * Pos(*p) * Sphere(params.BEARING_BALL_D / 2) for p in bearings()]


def sensor_parts():
    """{label: Shape}: the PMW3610 board (STEP, B.Cu up at W_BOARD) and boxes for the parts without a model."""
    cx, cy = params.PMW3610_BOARD_CENTRE
    # board local X (short side) -> v, local Y (long side, -KiCad y) -> u, local Z (B.Cu -> F.Cu) -> -n
    c, u, v, n = frame()
    origin = to_case(0.0, 0.0, W_BOARD) - cx * v - (-cy) * u
    placed = Location(Plane(origin=tuple(origin), x_dir=tuple(v), z_dir=tuple(-n)))
    step = import_step(_step_path("pmw3610_board"))
    board = placed * Compound(children=[ch for ch in step.children if not ch.label.startswith("PinHeader")])   # FPC, no header
    iu, iv, ih = params.PMW3610_IC_BOX
    lu, lv = params.PMW3610_LENS_BOX
    fw, fd, fh = params.PMW3610_FPC_BOX
    fa = cy - params.PMW3610_FPC_REF_Y                               # J2 towards +u (local Y = -KiCad y)
    ia = cy - params.PMW3610_IC_REF_Y                                # the package is off the optical centre, away from J2
    return {"pmw3610_board": board,
            "pmw3610_ic": loc() * _box(ia - iu / 2, ia + iu / 2, -iv / 2, iv / 2, W_SENSOR - ih, W_SENSOR),
            "pmw3610_lens": loc() * _box(-lu / 2, lu / 2, -lv / 2, lv / 2, W_BOARD, W_BOARD + params.PMW3610_LENS_PROTRUSION),
            "pmw3610_fpc": loc() * _box(fa - fd / 2, fa + fd / 2, -fw / 2, fw / 2, W_SENSOR - fh, W_SENSOR)}


def _step_path(name):
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / "step" / f"{name}.step"


def _pod_size(lift):
    """(radius, bottom edge radius) of the pod's outer face lifted by `lift` (an offset surface: both shrink with the lift)."""
    return params.BALL_POD_R_IN + params.BOTTOM_WALL - lift, params.BALL_POD_FILLET + params.BOTTOM_WALL - lift


def pod_cut(lift=0.0):
    """What the pod takes away from `below_floor(right, lift)`: the round pod (outer face lifted by `lift`) and up."""
    r, f = _pod_size(lift)
    pod = Pos(0, 0, W_POD_OUT + lift) * Cylinder(r, 200.0, align=MIN)
    return loc() * fillet(pod.edges().sort_by(Axis.Z)[0:1], f)


def _pod_cylinder(r, f, w0):
    pod = Pos(0, 0, w0) * Cylinder(r, 200.0, align=MIN)
    return fillet(pod.edges().sort_by(Axis.Z)[0:1], f)


@functools.lru_cache(maxsize=None)
def _pod_top():
    """(w_ref, r_edge): just under the walls' bottom edge over the arm (ball frame) and the plate edge's distance from the axis."""
    from shapely.geometry import Point

    import bottomcase
    import topcase

    depth = topcase.floor_profile("right")["thumb_depth"] + params.BOTTOM_RECESS          # wall edge below the thumb plate
    w_ref = params.BALL_CENTER_DEPTH - depth - params.BALL_POD_EDGE_CLEAR
    c = params.BALL_HOLE_CENTER_RIGHT
    return w_ref, bottomcase.bottom_outline("right").exterior.distance(Point(c[0], c[1]))


def _cone_down(r_top, w_top, w_bottom):
    """45 degree cone, r_top at w_top, widening down to w_bottom."""
    h = w_top - w_bottom
    return Pos(0, 0, w_bottom) * Cone(r_top + h, r_top, h, align=MIN)


@functools.lru_cache(maxsize=None)
def pod_outer():
    """Outer body of the pod (to be cut by `pod_cavity` and kept below the plate's inner face): the round cup, inside the plate
    outline up to the floor, outside it (over the arm walls) straight up to just under the walls (user: the pod's outer face
    continues the walls' outer face)."""
    import bottomcase
    import topcase

    w_ref, r_edge = _pod_top()
    r, f = _pod_size(0.0)
    cyl = loc() * _pod_cylinder(r, f, W_POD_OUT)
    flared = cyl & (loc() * _box(-50, 50, -50, 50, W_POD_OUT - 1.0, w_ref))
    inside = cyl & outline.plan_prism("right", bottomcase.bottom_outline("right"))
    under_walls = topcase.below_floor("right", -params.BOTTOM_RECESS - params.BALL_POD_EDGE_CLEAR, pod=False)
    return inside + (flared & under_walls)


@functools.lru_cache(maxsize=None)
def pod_cavity():
    """Inside of the pod and its opening up into the arm: BALL_POD_R_IN with the rounded bottom edge, narrowing at 45 degrees
    (BOTTOM_WALL from the outer flare) to the ball + BALL_POD_TOP_CLEAR."""
    w_ref, r_edge = _pod_top()
    r_top = R + params.BALL_POD_TOP_CLEAR
    w_neck = w_ref - (params.BOTTOM_WALL * np.sqrt(2) - (r_edge - r_top))
    r, f = _pod_size(params.BOTTOM_WALL)
    neck = _cone_down(r_top, w_neck, W_POD_IN - 1.0) + Pos(0, 0, w_neck - 0.01) * Cylinder(r_top, 200.0, align=MIN)
    return loc() * (_pod_cylinder(r, f, W_POD_IN) & neck)


def plate_inner_w():
    """Ball-frame height of the arm plate's inner face (BOTTOM_WALL above the thumb floor)."""
    import topcase

    return params.BALL_CENTER_DEPTH - (topcase.floor_profile("right")["thumb_depth"] - params.BOTTOM_WALL)


def fpc_windows():
    """The two cable windows through the plate ring and the pod wall, in the case frame: (downhill, uphill)."""
    w0, w1 = params.BALL_POD_FPC_BOTTOM, plate_inner_w() + params.BALL_POD_FPC_ABOVE
    r0, r1, hw = params.BALL_POD_FPC_R0, params.BALL_POD_FPC_R1, params.BALL_POD_FPC_W / 2
    return [loc() * _box(min(s * r0, s * r1), max(s * r0, s * r1), -hw, hw, w0, w1) for s in (-1, 1)]


def fpc_arch():
    """Notch in the collar's lower edge on the +u side: the cable leaves the ball shaft under it."""
    r_in = params.BALL_HOLE_D / 2
    z0 = plate_inner_w() - 0.2
    return loc() * _box(r_in - 0.5, r_in + params.BALL_HOLE_WALL + 0.5, -params.BALL_POD_FPC_W / 2, params.BALL_POD_FPC_W / 2,
                        z0, plate_inner_w() + params.BALL_POD_FPC_ARCH_H)


def pod_shell():
    import topcase

    return (pod_outer() - pod_cavity()) & topcase.below_floor("right", params.BOTTOM_WALL, pod=False)


def lowest_points():
    """Case-frame points on the pod's rounded bottom edge and the board screw heads, for the desk plane."""
    c, u, v, n = frame()
    r, f = _pod_size(0.0)
    pts = []
    for a in np.radians(np.arange(0, 360, 5)):
        d = np.cos(a) * u + np.sin(a) * v
        for p in np.radians(np.arange(0, 91, 5)):
            pts.append(c + (r - f + f * np.sin(p)) * d + (W_POD_OUT + f - f * np.cos(p)) * n)
    w_head = W_HEAD - params.SENSOR_SCREW_HEAD_H
    for a0, b0 in board_holes():
        for a in np.radians(np.arange(0, 360, 15)):
            pts.append(to_case(a0 + params.SENSOR_SCREW_HEAD_D / 2 * np.cos(a), b0 + params.SENSOR_SCREW_HEAD_D / 2 * np.sin(a), w_head))
    return pts


def pod_floor_z(x, y, lift=0.0):
    """Height of the pod's floor (lifted) at plan (x, y), or None outside the pod; the rounded edge rises from the flat
    floor (offset along n converted to height)."""
    c, u, v, n = frame()
    p0 = to_case(0.0, 0.0, W_POD_OUT + lift)
    z = p0[2] - (n[0] * (x - p0[0]) + n[1] * (y - p0[1])) / n[2]
    d = np.array((x, y, z)) - c
    rho = np.hypot(d @ u, d @ v)
    r, f = _pod_size(lift)
    if rho > r:
        return None
    k = rho - (r - f)
    rise = 0.0 if k <= 0 else f - np.sqrt(max(f * f - k * k, 0.0))
    return float(z + rise / n[2])


def foot_xy():
    """Plan position of the thumb foot: under the middle of the pod floor."""
    return tuple(to_case(0.0, 0.0, W_POD_OUT)[:2])


def standoffs():
    """Standoffs on the pod floor under the four board holes, up to the board's sensor face."""
    return [loc() * Pos(a, b, W_POD_IN - 0.1) * Cylinder(params.SENSOR_STANDOFF_D / 2, W_SENSOR - W_POD_IN + 0.1, align=MIN)
            for a, b in board_holes()]


def mount_cuts():
    """Through holes for the four board screws and the head counterbores in the pod's outer face."""
    out = []
    for a, b in board_holes():
        out.append(loc() * Pos(a, b, W_POD_OUT - 5.0) * Cylinder(params.SCREW_M25_CLEAR_D / 2, W_SENSOR - W_POD_OUT + 6.0, align=MIN))
        out.append(loc() * Pos(a, b, W_POD_OUT - 5.0) * Cylinder(params.SENSOR_SCREW_CBORE_D / 2, W_HEAD - W_POD_OUT + 5.0, align=MIN))
    return out
