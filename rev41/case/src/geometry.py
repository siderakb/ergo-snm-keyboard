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
