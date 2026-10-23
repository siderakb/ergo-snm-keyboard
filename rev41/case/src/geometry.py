"""Board placement helpers: board STEP-local / KiCad coordinates -> case frame.

See params.PLACEMENTS. STEP-local = (KiCad x, -KiCad y, z with 0 at the B.Cu face).
"""

import numpy as np

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
