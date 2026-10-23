"""Bottom case (left): a plate inside the top case walls.

Its outer face is the lower of two planes parallel to the main and thumb top planes (`topcase.below_floor`), BOTTOM_RECESS
up from the bottom edge of the walls, so the seam only shows from below. The M2.5 screws go up through it into the nuts at
the lower ends of the top case posts; the heads sit in shallow counterbores.
"""

import outline
import params
import topcase
from topcase import _along, below_floor, post_axis


def bottom_outline(hand):
    """Plan outline of the plate: the inner face of the top case walls, less the side clearance."""
    return outline.case_outline_polygon(hand).buffer(-params.BOTTOM_WALL - params.PLATE_SIDE_CLEAR)


def bottom_case(hand=None):
    hand = hand or params.HAND
    body = outline.plan_prism(hand, bottom_outline(hand)) & below_floor(hand, params.BOTTOM_WALL) - below_floor(hand)
    for x, y in topcase.post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        body = body - _along(top, n, t - 1.0, params.BOTTOM_WALL + 2.0, params.SCREW_M25_CLEAR_D / 2)
    for c in topcase.screw_counterbores(hand):
        body = body - c
    return body
