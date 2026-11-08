"""Board placement helpers: board STEP-local / KiCad coordinates -> case frame.

See params.PLACEMENTS. STEP-local = (KiCad x, -KiCad y, z with 0 at the B.Cu face).
"""

import numpy as np
from build123d import Align, Cylinder, Location, Plane, RegularPolygon, extrude

import params


def placement(board, hand=None):
    """(R, t) with case = R @ local + t, or None if the board is not placed for this hand."""
    entry = params.PLACEMENTS[hand or params.HAND].get(board)
    return None if entry is None else (np.array(entry[0], float), np.array(entry[1], float))


def local_to_case(board, X, Y, Z=0.0, hand=None):
    R, t = placement(board, hand)
    return tuple(R @ np.array([X, Y, Z]) + t)


def to_case(board, kx, ky, kz=0.0, hand=None):
    """Map a KiCad (x, y) on `board` (at STEP-local height kz) to the case frame, returns (X, Y, Z)."""
    return local_to_case(board, kx, -ky, kz, hand)


def mirror_x(x):
    """X in the other hand's case frame (see params.MIRROR_X)."""
    return params.MIRROR_X - x


def mirror_shape(shape):
    """A left-hand case shape mirrored into the right-hand frame (or back)."""
    from build123d import Plane

    return shape.mirror(Plane.YZ.offset(params.MIRROR_X / 2))


def ball_center(hand="right"):
    """Trackball centre in the case frame: below the plate-top hole centre along the plate normal."""
    if hand != "right":
        raise ValueError("the trackball is on the right hand only")
    n = placement("thumb_1x2", "right")[0][:, 2]
    return tuple(np.array(params.BALL_HOLE_CENTER_RIGHT) - params.BALL_CENTER_DEPTH * n)


def sensor_lens_plane_center(hand="right"):
    """Centre of the PMW3610 lens reference plane: below the ball along the plate normal,
    PMW3610_WORKING_DISTANCE under the ball surface (sensor board parallel to the plate)."""
    n = placement("thumb_1x2", hand)[0][:, 2]
    return tuple(np.array(ball_center(hand)) - (params.BALL_D / 2 + params.PMW3610_WORKING_DISTANCE) * n)


def sensor_stack(hand="right"):
    """Centres (case frame) of the PMW3610 reference planes, from the ball surface point nearest
    the board straight down the plate normal. Keys: ball_surface, lens, board_ball_face,
    board_sensor_face, body_top."""
    n = placement("thumb_1x2", hand)[0][:, 2]
    surface = np.array(ball_center(hand)) - params.BALL_D / 2 * n
    below = {
        "ball_surface": 0.0,
        "lens": params.PMW3610_WORKING_DISTANCE,
        "board_ball_face": params.PMW3610_LENS_FACE_TO_SURFACE,
        "board_sensor_face": params.PMW3610_SENSOR_FACE_TO_SURFACE,
        "body_top": params.PMW3610_BODY_TOP_TO_SURFACE,
    }
    return {k: tuple(surface - d * n) for k, d in below.items()}


def outline_in_case(board, hand=None, source=None):
    """Edge.Cuts loops of the board as case-frame (X, Y) polygons (arcs discretised).

    `board` is the placed board name; `source` the PCB it comes from (default: params.BOARD_SOURCE).
    The two thumb boards share one panel outline, so both return the whole panel (one outer loop
    plus the cut-out between the tabs); split it with params.THUMB_BOARDS x ranges if needed.
    """
    import pcb_ref

    loops = pcb_ref.outline_loops(pcb_ref.load_board(source or params.BOARD_SOURCE[board]))
    return [[to_case(board, x, y, hand=hand)[:2] for x, y in loop] for loop in loops]


def location(board, hand=None):
    """build123d Location that places a STEP-local shape of `board` in the case frame."""
    from build123d import Location, Plane

    R, t = placement(board, hand)
    return Location(Plane(origin=tuple(t), x_dir=tuple(R[:, 0]), z_dir=tuple(R[:, 2])))


def standoff_pocket(top, n, t, u):
    """Hex pocket for the brass standoff, open at the post's lower end (t below `top`) and STANDOFF_H deep, with round
    corner reliefs and three crush ribs, as (cut, ribs): subtract the cut, then add the ribs back."""
    af = params.STANDOFF_AF + params.STANDOFF_POCKET_CLEAR
    R = af / np.sqrt(3)                                     # corner radius of the pocket hex
    depth = params.STANDOFF_H
    v = np.cross(n, u)                                      # n x u: in-plane, 90 deg from u (right-handed with -n axis)
    ang = lambda a: np.cos(np.radians(a)) * u + np.sin(np.radians(a)) * v
    end = top - t * n
    base = end - 1.0 * n                                    # the cut starts 1.0 below the post end (clean mouth)
    plane = Plane(origin=tuple(base), x_dir=tuple(ang(30)), z_dir=tuple(n))     # hex corners on x: corner at 30 deg from u
    cut = Location(plane) * extrude(RegularPolygon(R, 6), depth + 1.0)
    for k in range(6):
        c = base + R * ang(30 + 60 * k)
        cut = cut + Location(Plane(origin=tuple(c), z_dir=tuple(n))) * Cylinder(
            params.STANDOFF_CORNER_RELIEF_D / 2, depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ribs = []
    r_rib = params.STANDOFF_RIB_D / 2
    reach = params.STANDOFF_AF / 2 - params.STANDOFF_RIB_INTERF          # rib crest, from the axis
    for a in (60, 180, 300):                                               # alternate flats, not the one facing u
        c = end + n * params.STANDOFF_RIB_LEAD + (reach + r_rib) * ang(a)
        ribs.append(Location(Plane(origin=tuple(c), z_dir=tuple(n))) * Cylinder(
            r_rib, depth - params.STANDOFF_RIB_LEAD, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return cut, ribs
