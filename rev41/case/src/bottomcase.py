"""Bottom case (left): floor, walls up to the top-case seam and screw bosses.

The rim follows the top case seam exactly: the folded SEAM_DEPTH surface, stepped down to SEAM_DEPTH_TONGUE along
the +Y band where the top case wall carries the USB-C / switch openings (the same Y-Z trapezoid, `topcase._tongue_zone`).
The outer floor face is the lower of two planes, like the top surface is the lower of the main and thumb planes: the
main one sits under the battery holder, the one parallel to the thumb plate under the tilted thumb board.
Screw bosses rise from the floor to the post ends of the top case (along the plane normal there); the M2.5 screw head
sits at the ceiling of a well bored from the outside (see params.BOSS_WELL_D).
"""

import numpy as np
from build123d import Align, Cylinder, Location, Plane

import outline
import params
import topcase
from topcase import _planes, _prism, _seam_point_and_normal, _tongue_zone, _under


def main_floor_z():
    """Outer floor face under the main plate: below the battery holder with the clearance and the floor wall."""
    return params.BATTERY_TOP_Z_LEFT - params.BATTERY_HOLDER[1] - params.BOTTOM_CLEAR - params.BOTTOM_WALL


def thumb_floor_depth(hand):
    """Outer floor face depth under the thumb plate, along the plate normal: lowest corner of the thumb board
    (with its hot-swap sockets) plus the clearance and the floor wall."""
    from assembly import load_boards

    (_, _), (tp, tn) = _planes(hand)
    board = next(b for b in load_boards(hand) if b.label == outline.thumb_board(hand))
    reach = max(float((tp - np.array((v.X, v.Y, v.Z))) @ tn) for v in board.vertices())
    reach = max(reach, params.SEAM_DEPTH - 0.5)        # the STEP has no hot-swap sockets: PCB underside + their protrusion
    return reach + params.BOTTOM_CLEAR + params.BOTTOM_WALL


def _below_floor(hand, lift=0.0):
    """Everything below the outer floor face raised by `lift` (the inside face of the floor for lift = BOTTOM_WALL)."""
    (mp, mn), (tp, tn) = _planes(hand)
    d_main = mp[2] - main_floor_z() - lift
    return outline._half_space(mp, mn, d_main) & outline._half_space(tp, tn, thumb_floor_depth(hand) - lift)


def _under_seam(hand):
    """Everything below the stepped seam surface."""
    return _under(hand, params.SEAM_DEPTH) - (_tongue_zone(hand) - _under(hand, params.SEAM_DEPTH_TONGUE))


def bottom_outline(hand):
    """Plan outline of the bottom case: the top case outline set back by SEAM_INSET."""
    return outline.case_outline_polygon(hand, offset=outline.BOTTOM_OFFSET)


def bosses(hand):
    """(bodies fused with the floor, well and hole cutters) for every screw post."""
    r = params.BOSS_D / 2
    keep_out = topcase.pcb_union(hand).buffer(params.BOSS_PCB_CLEAR)
    # a boss beside the deep +Y wall is cut back by it (the top case wall hangs lower than the post end there)
    clip = (outline.plan_prism(hand, bottom_outline(hand)) & _under(hand, params.SEAM_DEPTH)
            - _prism(keep_out) - _below_floor(hand) - topcase.walls(hand))
    bodies, cutters = [], []
    for x, y in topcase.post_positions(hand):
        seam, n = _seam_point_and_normal(hand, x, y)
        down = Plane(origin=tuple(seam), z_dir=tuple(-n))             # +Z of this plane points down the screw axis
        bodies.append(Location(down) * Cylinder(r, 100, align=(Align.CENTER, Align.CENTER, Align.MIN)) & clip)
        up = 0.5
        hole = Plane(origin=tuple(seam + up * n), z_dir=tuple(-n))
        cutters.append(Location(hole) * Cylinder(params.SCREW_M25_CLEAR_D / 2, up + params.BOSS_HOLE_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        well = Plane(origin=tuple(seam - params.BOSS_HOLE_LEN * n), z_dir=tuple(-n))
        cutters.append(Location(well) * Cylinder(params.BOSS_WELL_D / 2, 100, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return bodies, cutters


def bottom_case(hand=None):
    hand = hand or params.HAND
    outer = bottom_outline(hand)
    envelope = _under_seam(hand) - _below_floor(hand)
    shell = outline.plan_prism(hand, outer) & envelope
    cavity = outline.plan_prism(hand, outer.buffer(-params.BOTTOM_WALL)) - _below_floor(hand, params.BOTTOM_WALL)
    body = shell - cavity
    bodies, cutters = bosses(hand)
    for b in bodies:
        body = body + b
    for c in cutters:
        body = body - c
    return body
