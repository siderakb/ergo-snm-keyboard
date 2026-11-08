"""Right-hand trackball (R2): ball cup with the tilted PMW3610 board under it, standing in a pod of the bottom plate.

Everything is built in the ball frame (`frame`): origin at the ball centre, x = u (uphill along the thumb plate, towards the
crease), y = v = n x u, z = n (thumb plate normal). The sensor board lies in the sensor frame (`sensor_frame`): the ball
frame turned SENSOR_TILT_DEG about v, its x (a) along the board towards the hole edge (+u, up), z the board normal; depths `w`
of the sensor parts are along that normal from the ball centre. The cup is a separate part: a spherical shell below
BALL_CUP_RIM with three steel-ball seats and a lens collar that sits on the board. The board is screwed to the pod (two
screws down from the cup's arm through the board into nuts in the pod's standoffs, which fixes the cup too) and rests
on two pads at its low end.
"""

import functools

import numpy as np
from build123d import Align, Axis, Box, Compound, Cone, Cylinder, Location, Plane, Pos, Sphere, fillet, import_step

import geometry
import outline
import params

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
R = params.BALL_D / 2
TILT = np.radians(params.SENSOR_TILT_DEG)
# sensor frame depths
W_BOARD = -(R + params.PMW3610_LENS_FACE_TO_SURFACE)          # board face toward the ball (nominal)
W_SENSOR = W_BOARD - params.PMW3610_BOARD_T                    # face with the IC and the FPC connector
W_SEAT = W_BOARD + params.SENSOR_SHIM_NOM                      # collar underside (shims fill the rest)
W_LOW = W_SENSOR - params.PMW3610_FPC_BOX[2]                   # lowest part of the module
W_POD_IN = W_SENSOR - params.PMW3610_CAP_H - params.BALL_POD_FLOOR_CLEAR      # slot floor under the board (inner face)
W_POD_OUT = W_POD_IN - params.BOTTOM_WALL
W_SLOT_TOP = 5.0                                               # the slot is open upwards into the case
# ball frame: the tube's floor under the cup
W_TUBE_IN = -(R + params.BALL_CUP_GAP + params.BALL_CUP_WALL + params.BALL_POD_FLOOR_CLEAR)
W_TUBE_OUT = W_TUBE_IN - params.BOTTOM_WALL


def board_ab(kx, ky):
    """KiCad (x, y) of the sensor board -> sensor frame (a, b): a towards the hole edge, b across (board X mirrored)."""
    ox, oy = params.PMW3610_OPTICAL_CENTRE
    return ky - oy, ox - kx


def _part_boxes():
    """Sensor-frame boxes (a0, a1, b0, b1, w0, w1) of the board and its parts."""
    x0, y0, x1, y1 = params.PMW3610_BOARD_EDGES
    a0, b1 = board_ab(x0, y0)
    a1, b0 = board_ab(x1, y1)
    iu, iv, ih = params.PMW3610_IC_BOX
    lu, lv = params.PMW3610_LENS_BOX
    fw, fd, fh = params.PMW3610_FPC_BOX
    ia, fa = board_ab(0, params.PMW3610_IC_REF_Y)[0], board_ab(0, params.PMW3610_FPC_REF_Y)[0]
    return {"board": (a0, a1, b0, b1, W_SENSOR, W_BOARD),
            "ic": (ia - iu / 2, ia + iu / 2, -iv / 2, iv / 2, W_SENSOR - ih, W_SENSOR),
            "fpc": (fa - fd / 2, fa + fd / 2, -fw / 2, fw / 2, W_SENSOR - fh, W_SENSOR),
            "lens": (-lu / 2, lu / 2, -lv / 2, lv / 2, W_BOARD, W_BOARD + params.PMW3610_LENS_PROTRUSION)}


def _collar_box():
    lu, lv = params.PMW3610_LENS_BOX
    c = params.LENS_WINDOW_CLEAR + params.CUP_COLLAR_WALL
    return -lu / 2 - c, lu / 2 + c, -lv / 2 - c, lv / 2 + c


def _cavity_boxes():
    """The slot's inside, sensor frame: round the board (and the passives under it), U1, J2 and the cup's collar, each with
    BALL_POD_FLOOR_CLEAR under it, BALL_POD_BOARD_CLEAR beside it, open up to W_SLOT_TOP."""
    k, f = params.BALL_POD_BOARD_CLEAR, params.BALL_POD_FLOOR_CLEAR
    p = _part_boxes()
    out = [(p["board"][0] - k, p["board"][1] + k, p["board"][2] - k, p["board"][3] + k, W_POD_IN)]
    for name in ("ic", "fpc"):
        a0, a1, b0, b1, w0, _ = p[name]
        out.append((a0 - k, a1 + k, b0 - k, b1 + k, w0 - f))
    a0, a1, b0, b1 = _collar_box()
    out.append((a0 - k, a1 + k, b0 - k, b1 + k, W_SEAT - k))
    a0, a1, bw = _arm_extent()
    out.append((a0 - k, a1 + k + params.CUP_ARM_SWEEP, -bw - k, bw + k, W_SEAT - k))
    return out


def _arm_extent():
    """(a0, a1, half width) of the cup's arm and its posts, sensor frame."""
    (ha, hb), _ = board_holes()
    r = params.CUP_BOSS_D / 2
    return params.CUP_ARM_A0, ha + r, abs(hb) + r


def _slot_boxes(grow):
    """The cavity boxes grown by `grow` beside and below: (a0, a1, b0, b1, w0, w1)."""
    return [(a0 - grow, a1 + grow, b0 - grow, b1 + grow, w0 - grow, W_SLOT_TOP) for a0, a1, b0, b1, w0 in _cavity_boxes()]


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


@functools.lru_cache(maxsize=None)
def sensor_frame():
    """(c, a, v, w) of the sensor frame in the case frame: the ball frame turned TILT about v (a = cos u + sin n)."""
    c, u, v, n = frame()
    return c, np.cos(TILT) * u + np.sin(TILT) * n, v, -np.sin(TILT) * u + np.cos(TILT) * n


def sloc():
    c, a, _, w = sensor_frame()
    return Location(Plane(origin=tuple(c), x_dir=tuple(a), z_dir=tuple(w)))


def to_sensor(a, b, w):
    c, ax, v, n = sensor_frame()
    return c + a * ax + b * v + w * n


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
    """(a0, a1, b0, b1) of U1's through-hole pins with their clearance, sensor frame."""
    x0, y0, x1, y1 = params.PMW3610_PIN_FIELD
    c = params.PMW3610_PIN_CLEAR
    (a0, b1), (a1, b0) = board_ab(x0, y0), board_ab(x1, y1)
    return a0 - c, a1 + c, b0 - c, b1 + c


def board_holes():
    """Sensor-frame (a, b) of the two board holes."""
    return [board_ab(x, y) for x, y in params.PMW3610_HOLES_KICAD]


def pads():
    """Sensor-frame (a, b) of the support pads under the board's low end."""
    return [board_ab(x, y) for x, y in params.SENSOR_PAD_POS]


W_HEAD = W_SEAT + params.CUP_POST_H                                                   # screw head underside, on the post
W_TIP = W_HEAD - params.SENSOR_SCREW_L                                                # screw tip (nominal shim)
W_POST_TOP = W_HEAD                                                                   # top of the arm and its posts
W_NUT = W_SENSOR - params.SENSOR_NUT_H                                                # nut underside (its top on F.Cu)


def _arm():
    """The cup's arm (sensor frame): a plate from inside the shell out over the holes, CUP_ARM_GAP above the seat, and the
    two posts down to the seat."""
    a0, a1, bw = _arm_extent()
    arm = _box(a0, a1 - params.CUP_BOSS_D / 2, -bw, bw, W_SEAT + params.CUP_ARM_GAP, W_POST_TOP)
    for a, b in board_holes():
        arm = arm + Pos(a, b, W_SEAT) * Cylinder(params.CUP_BOSS_D / 2, W_POST_TOP - W_SEAT, align=MIN)
    return arm


def _nut(a, b, af, w0, h):
    """Hex prism (sensor frame) across flats `af` round the hole at (a, b), one flat towards b = 0."""
    from build123d import RegularPolygon, extrude

    hexa = extrude(RegularPolygon(af / np.sqrt(3), 6), h)        # corners on x: flats on +-y
    return Pos(a, b, w0) * hexa


def _seat_frame():
    """The two side feet (from the seat W_SEAT up into the shell) and the lens collar: only a short frame round the window
    under the shell (CUP_COLLAR_LIFT above the seat): it stiffens the window edge, the feet carry the cup."""
    a0, a1, b0, b1 = _collar_box()
    top = -R
    frame = _box(a0, a1, b0, b1, W_SEAT + params.CUP_COLLAR_LIFT, top)
    (fa0, fa1), (fb0, fb1) = params.CUP_SIDE_FEET
    for s in (-1, 1):
        frame = frame + _box(fa0, fa1, min(s * fb0, s * fb1), max(s * fb0, s * fb1), W_SEAT, top)
    return frame


def _tilt():
    """Sensor frame in the ball frame: turned TILT about v, so that a = cos u + sin n."""
    return Location((0, 0, 0), (0, -params.SENSOR_TILT_DEG, 0))


@functools.lru_cache(maxsize=None)
def cup_local():
    """The cup in the ball frame."""
    r_in, r_out = R + params.BALL_CUP_GAP, R + params.BALL_CUP_GAP + params.BALL_CUP_WALL
    tilt = _tilt()
    body = Sphere(r_out) + tilt * _seat_frame()
    for p in bearings() + alt_bearings():
        body = body + Pos(*p) * Sphere(params.BEARING_BOSS_D / 2)
    r_keep = params.BALL_POD_R_IN - params.BALL_POD_CLEAR    # nothing above the rim, nothing outside the pod's wall
    body = body & (Pos(0, 0, -60.0) * Cylinder(r_keep, 60.0 - params.BALL_CUP_RIM, align=MIN))
    body = body + tilt * _arm()                              # out of the tube into the slot, on the +u side
    body = body - Sphere(r_in)
    lu, lv = params.PMW3610_LENS_BOX
    c = params.LENS_WINDOW_CLEAR
    body = body - tilt * _box(-lu / 2 - c, lu / 2 + c, -lv / 2 - c, lv / 2 + c, W_SEAT - 1.0, 0.0)   # the sensor sees the ball
    body = body - tilt * _box(*pin_field(), W_SEAT - 1.0, W_SEAT + 2.0)                                # U1 pins on B.Cu
    for p in bearings() + alt_bearings():      # blind seat: the steel ball sits on its bottom, touching the ball
        k = p / np.linalg.norm(p)
        body = body - Location(Plane(origin=tuple(p - k * 2.0), z_dir=tuple(k))) * Cylinder(params.BEARING_HOLE_D / 2, 2.0 + params.BEARING_BALL_D / 2, align=MIN)
    for a, b in board_holes():                 # clearance holes through the posts
        body = body - tilt * (Pos(a, b, W_SEAT - 1.0) * Cylinder(params.BOTTOM_SCREW_CLEAR_D / 2, W_POST_TOP - W_SEAT + 2.0, align=MIN))
    return body


def cup():
    return loc() * cup_local()


def ball():
    return Pos(*geometry.ball_center()) * Sphere(R)


def steel_balls():
    return [loc() * Pos(*p) * Sphere(params.BEARING_BALL_D / 2) for p in bearings()]


def sensor_parts():
    """{label: Shape}: the PMW3610 board (STEP, B.Cu up at W_BOARD) and boxes for the parts without a model."""
    ox, oy = params.PMW3610_OPTICAL_CENTRE
    c, a, v, w = sensor_frame()
    # board local X (KiCad x) -> -v, local Y (-KiCad y) -> -a, local Z (B.Cu -> F.Cu) -> -w
    origin = to_sensor(-oy, ox, W_BOARD)
    placed = Location(Plane(origin=tuple(origin), x_dir=tuple(-v), z_dir=tuple(-w)))
    step = import_step(_step_path("pmw3610_board"))
    board = placed * Compound(children=[ch for ch in step.children if not ch.label.startswith("PinHeader")])
    p = _part_boxes()
    out = {"pmw3610_board": board, "pmw3610_ic": sloc() * _box(*p["ic"]), "pmw3610_lens": sloc() * _box(*p["lens"]),
           "pmw3610_fpc": sloc() * _box(*p["fpc"])}
    for i, (a, b) in enumerate(board_holes()):
        out[f"sensor_nut_{i}"] = sloc() * _nut(a, b, params.SENSOR_NUT_AF, W_NUT, params.SENSOR_NUT_H)
    return out


def _step_path(name):
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / "step" / f"{name}.step"


def _pod_size(lift):
    """(radius, bottom edge radius) of the pod's outer face lifted by `lift` (an offset surface: both shrink with the lift)."""
    return params.BALL_POD_R_IN + params.BOTTOM_WALL - lift, params.BALL_POD_FILLET + params.BOTTOM_WALL - lift


def _slot(grow):
    """The slot's boxes grown by `grow` (BOTTOM_WALL: outer face), case frame."""
    return [sloc() * _box(*b) for b in _slot_boxes(grow)]


def pod_cut(lift=0.0):
    """What the pod takes away from `below_floor(right, lift)`: the round tube and the slot (outer faces lifted by `lift`)
    and up."""
    r, f = _pod_size(lift)
    out = loc() * _pod_cylinder(r, f, W_TUBE_OUT + lift)
    for b in _slot(params.BOTTOM_WALL - lift):
        out = out + b
    return out


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


@functools.lru_cache(maxsize=None)
def pod_outer():
    """Outer body of the pod (to be cut by `pod_cavity` and kept below the plate's inner face): the round tube, inside the
    plate outline up to the floor, outside it (over the arm walls) straight up to just under the walls (user: the pod's outer
    face continues the walls' outer face); and the slot, inside the plate outline."""
    import bottomcase
    import topcase

    w_ref, r_edge = _pod_top()
    r, f = _pod_size(0.0)
    cyl = loc() * _pod_cylinder(r, f, W_TUBE_OUT)
    flared = cyl & (loc() * _box(-50, 50, -50, 50, W_TUBE_OUT - 1.0, w_ref))
    plan = outline.plan_prism("right", bottomcase.bottom_outline("right"))
    inside = cyl & plan
    for b in _slot(params.BOTTOM_WALL):
        inside = inside + (b & plan)
    under_walls = topcase.below_floor("right", -params.BOTTOM_RECESS - params.BALL_POD_EDGE_CLEAR, pod=False)
    return inside + (flared & under_walls)


@functools.lru_cache(maxsize=None)
def pod_cavity():
    """Inside of the pod: the straight tube BALL_POD_R_IN with the rounded bottom edge, open all the way up through the
    arm's plate (no neck), so the cup goes in from above; and the slot for the tilted board."""
    r, f = _pod_size(params.BOTTOM_WALL)
    out = loc() * _pod_cylinder(r, f, W_TUBE_IN)
    for b in _slot(0.0):
        out = out + b
    return out


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


def _box_corners(boxes):
    return [to_sensor(a, b, w) for a0, a1, b0, b1, w, _ in boxes for a in (a0, a1) for b in (b0, b1)]


def lowest_points():
    """Case-frame points on the tube's rounded bottom edge and the slot's bottom corners, for the desk plane."""
    c, u, v, n = frame()
    r, f = _pod_size(0.0)
    pts = []
    for a in np.radians(np.arange(0, 360, 5)):
        d = np.cos(a) * u + np.sin(a) * v
        for p in np.radians(np.arange(0, 91, 5)):
            pts.append(c + (r - f + f * np.sin(p)) * d + (W_TUBE_OUT + f - f * np.cos(p)) * n)
    pts += _box_corners(_slot_boxes(params.BOTTOM_WALL))
    return pts


def _tube_floor_z(x, y, lift):
    c, u, v, n = frame()
    p0 = to_case(0.0, 0.0, W_TUBE_OUT + lift)
    z = p0[2] - (n[0] * (x - p0[0]) + n[1] * (y - p0[1])) / n[2]
    d = np.array((x, y, z)) - c
    rho = np.hypot(d @ u, d @ v)
    r, f = _pod_size(lift)
    if rho > r:
        return None
    k = rho - (r - f)
    rise = 0.0 if k <= 0 else f - np.sqrt(max(f * f - k * k, 0.0))
    return float(z + rise / n[2])


def _box_floor_z(x, y, box):
    """Lowest z where the vertical line at (x, y) enters a sensor-frame box (a0, a1, b0, b1, w0, w1), or None."""
    c, a, v, w = sensor_frame()
    p = np.array((x, y, 0.0)) - c
    lo, hi = -1e9, 1e9
    for axis, (m0, m1) in zip((a, v, w), ((box[0], box[1]), (box[2], box[3]), (box[4], box[5]))):
        p0, dz = p @ axis, axis[2]
        if abs(dz) < 1e-12:
            if not m0 <= p0 <= m1:
                return None
            continue
        t0, t1 = sorted(((m0 - p0) / dz, (m1 - p0) / dz))
        lo, hi = max(lo, t0), min(hi, t1)
    return float(lo) if lo <= hi else None


def pod_floor_z(x, y, lift=0.0):
    """Height of the pod's floor (lifted) at plan (x, y), or None outside the pod: the tube (its rounded edge rises from the
    flat floor, offset along n converted to height) or the slot's boxes."""
    zs = [_tube_floor_z(x, y, lift)] + [_box_floor_z(x, y, b) for b in _slot_boxes(params.BOTTOM_WALL - lift)]
    zs = [z for z in zs if z is not None]
    return min(zs) if zs else None


def foot_xy():
    """Plan position of the thumb foot: under the slot's floor below U1."""
    ia = _part_boxes()["ic"]
    return tuple(to_sensor((ia[0] + ia[1]) / 2, 0.0, W_POD_OUT)[:2])


def standoffs():
    """Standoffs on the slot floor under the two board holes (round the nut pockets, cut flat beside J2) and the two pads under
    the low end, up to the sensor face."""
    h = W_SENSOR - W_POD_IN + 0.1
    fw = params.PMW3610_FPC_BOX[0] / 2 + params.SENSOR_STANDOFF_FPC_CLEAR
    r = params.SENSOR_STANDOFF_D / 2
    out = []
    for a, b in board_holes():
        post = Pos(a, b, W_POD_IN - 0.1) * Cylinder(r, h, align=MIN)
        b0 = fw if b > 0 else b - r - 1.0
        b1 = b + r + 1.0 if b > 0 else -fw
        out.append(sloc() * (post & _box(a - r - 1.0, a + r + 1.0, b0, b1, W_POD_IN - 1.0, W_SENSOR + 1.0)))
    pa, pb = params.SENSOR_PAD
    out += [sloc() * Pos(a, b, W_POD_IN - 0.1) * Box(pa, pb, h, align=MIN) for a, b in pads()]
    return out


def mount_cuts():
    """Nut pockets at the standoffs' tops and blind screw holes below them, SENSOR_SCREW_FLOOR above the outer face."""
    out = []
    af = params.SENSOR_NUT_AF + params.SENSOR_NUT_CLEAR
    for a, b in board_holes():
        out.append(sloc() * _nut(a, b, af, W_NUT, params.SENSOR_NUT_H + 1.0))
        w0 = W_POD_OUT + params.SENSOR_SCREW_FLOOR
        out.append(sloc() * Pos(a, b, w0) * Cylinder(params.BOTTOM_SCREW_CLEAR_D / 2, W_SENSOR - w0 + 1.0, align=MIN))
    return out
