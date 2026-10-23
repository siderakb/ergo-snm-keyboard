import sys
from pathlib import Path

import numpy as np
import pytest
from build123d import Align, Cylinder, Location, Plane, Pos

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import bottomcase  # noqa: E402
import params  # noqa: E402
import topcase  # noqa: E402
from assembly import load_boards  # noqa: E402
from placeholders import core_board_placeholders  # noqa: E402

TOP = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP


@pytest.fixture(scope="module")
def bottom():
    return bottomcase.bottom_case("left")


def test_bottom_case_is_one_valid_solid(bottom):
    assert bottom.is_valid and len(bottom.solids()) == 1


def test_floor_is_below_the_battery_holder_and_the_rim_meets_the_top_case_seam(bottom):
    bb = bottom.bounding_box()
    assert bb.max.Z == pytest.approx(TOP - params.SEAM_DEPTH, abs=1e-6)
    assert bottomcase.main_floor_z() == pytest.approx(-19.0)
    probe = Pos(36, -31.8, TOP - params.SEAM_DEPTH_TONGUE - 0.2) * Cylinder(0.3, 0.2)      # rim top in the deep +Y band
    assert vol(bottom & probe) > 0
    assert vol(bottom & (Pos(36, -31.8, TOP - params.SEAM_DEPTH_TONGUE - 1.5) * Cylinder(0.3, 0.2))) > 0      # wall below
    assert vol(bottom & (Pos(36, -31.8, TOP - params.SEAM_DEPTH_TONGUE + 0.7) * Cylinder(0.3, 0.2))) < 1e-9


@pytest.fixture(scope="module")
def top():
    return topcase.top_case("left")


def test_bottom_case_does_not_touch_the_top_case_or_the_boards(bottom, top):
    assert vol(bottom & top) < 1.0
    for board in load_boards("left"):
        assert vol(bottom & board) < 1.0, board.label
    for label, shape in core_board_placeholders("left").items():
        assert vol(bottom & shape) < 1e-3, label


def vol(shape):
    return shape.volume if shape else 0.0


def test_every_boss_reaches_the_post_end_with_a_screw_hole_and_a_well_with_wall_left(bottom, top):
    for x, y in topcase.post_positions("left"):
        seam, n = topcase._seam_point_and_normal("left", x, y)
        axis = Plane(origin=tuple(seam), z_dir=tuple(-n))
        at = lambda d, r, h=0.2: (Location(axis) * Pos(0, 0, d) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.CENTER)))
        assert vol(bottom & at(0.1, 1.0)) < 1e-6                                   # 2.8 hole at the seam is open
        assert vol(bottom & at(1.0, params.SCREW_M25_CLEAR_D / 2 + 0.3)) > 0        # boss material around the hole
        assert vol(bottom & at(params.BOSS_HOLE_LEN + 3.0, params.BOSS_WELL_D / 2 - 0.2)) < 1e-6   # head well open
        ring = at(params.BOSS_HOLE_LEN + 3.0, params.BOSS_WELL_D / 2 + 0.7, 1.0) - at(params.BOSS_HOLE_LEN + 3.0, params.BOSS_WELL_D / 2, 1.0)
        assert vol((bottom + top) & ring) > 0.8 * ring.volume, (x, y)     # ~0.7 mm wall around the well (less where the boss is trimmed by the PCB clearance)
