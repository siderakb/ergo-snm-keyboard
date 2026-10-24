"""Bottom case (left): a plate inside the top case walls, with feet columns and support pillars.

Its outer face follows `topcase.below_floor`, BOTTOM_RECESS up from the bottom edge of the walls, so the seam only shows
from below. The M2.5 screws go up through it into the nuts at the lower ends of the top case posts (heads in shallow
counterbores). Feet columns stand perpendicular to the tented desk plane (`desk_plane`); support pillars rise through the
main board's mounting holes to the skin underside.
"""

import functools

import numpy as np
from build123d import Align, Cylinder, Location, Plane, Pos

import outline
import params
import pcb_ref
import topcase
from geometry import to_case
from topcase import _along, below_floor, floor_z, post_axis


def bottom_outline(hand):
    """Plan outline of the plate: the inner face of the top case walls, less the side clearance."""
    return outline.case_outline_polygon(hand).buffer(-params.BOTTOM_WALL - params.PLATE_SIDE_CLEAR)


@functools.lru_cache(maxsize=None)
def desk_plane(hand):
    """(unit normal, d) of the desk in the case frame, n . p = d: tilted by TENT_ANGLE about Y with the +X side up, as
    high as the lowest point of the case allows (the walls' bottom edge along the outline, plus pads and clearance)."""
    t = np.radians(params.TENT_ANGLE)
    n = np.array((np.sin(t), 0.0, np.cos(t)))
    ring = outline.case_outline_polygon(hand).exterior
    pts = [ring.interpolate(s) for s in np.arange(0.0, ring.length, 1.0)]
    low = min(n @ np.array((p.x, p.y, floor_z(hand, p.x, p.y, -params.BOTTOM_RECESS))) for p in pts)
    return n, float(low - params.FOOT_PAD_T - params.FOOT_MIN_CLEAR)


def feet(hand):
    """Feet columns: from the plate's inner face down along the desk normal to FOOT_PAD_T above the desk."""
    n, d = desk_plane(hand)
    out = []
    for x, y in params.FEET_LEFT:
        # start inside the plate, low enough that the tilted top disc stays under its inner face
        sink = params.FOOT_D / 2 * np.sin(np.radians(params.TENT_ANGLE)) + 0.1
        top = np.array((x, y, floor_z(hand, x, y, params.BOTTOM_WALL) - sink))
        length = n @ top - (d + params.FOOT_PAD_T)
        plane = Plane(origin=tuple(top), z_dir=tuple(-n))
        out.append(Location(plane) * Cylinder(params.FOOT_D / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out


def support_holes(hand):
    """{ref: (x, y)} of the main-board mounting holes used for support pillars, in the case frame."""
    holes = {r: (x, y) for r, x, y in pcb_ref.mounting_holes(pcb_ref.load_board(params.BOARD_SOURCE["main_board"]))}
    return {r: tuple(to_case("main_board", *holes[r], 0.0, hand=hand)[:2]) for r in params.SUPPORT_HOLES_LEFT}


def pillars(hand):
    """Pillar body from the plate up to PILLAR_TOP_Z (below the sockets) and a pin through the hole to the skin underside."""
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    out = []
    for x, y in support_holes(hand).values():
        base = floor_z(hand, x, y, params.BOTTOM_WALL) - 0.5            # sunk into the plate
        if params.PILLAR_TOP_Z > base:
            out.append(Pos(x, y, base) * Cylinder(params.PILLAR_D / 2, params.PILLAR_TOP_Z - base, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        z0 = min(base, params.PILLAR_TOP_Z)
        out.append(Pos(x, y, z0) * Cylinder(params.PIN_D / 2, skin_under - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out


def bottom_case(hand=None):
    hand = hand or params.HAND
    body = outline.plan_prism(hand, bottom_outline(hand)) & below_floor(hand, params.BOTTOM_WALL) - below_floor(hand)
    for x, y in topcase.post_positions(hand):
        top, n, t = post_axis(hand, x, y)
        body = body - _along(top, n, t - 1.0, params.BOTTOM_WALL + 2.0, params.SCREW_M25_CLEAR_D / 2)
    for c in topcase.screw_counterbores(hand):
        body = body - c
    for part in feet(hand) + pillars(hand):
        body = body + part
    solids = sorted(body.solids(), key=lambda s: s.volume)
    assert all(s.volume < 0.1 for s in solids[:-1]), "bottom case falls apart"
    return solids[-1]                                    # drops boolean slivers (counterbore against a ramp)
