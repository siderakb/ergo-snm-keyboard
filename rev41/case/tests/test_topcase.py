import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import analysis  # noqa: E402
import outline  # noqa: E402
import params  # noqa: E402
import topcase  # noqa: E402
from assembly import load_boards  # noqa: E402


@pytest.fixture(scope="module")
def case():
    return topcase.top_case("left")


def test_top_case_is_one_valid_solid(case):
    assert case.is_valid and len(case.solids()) == 1


def test_walls_hang_seam_depth_below_the_top_surface():
    w = topcase.walls("left")
    bb = w.bounding_box()
    assert bb.max.Z == pytest.approx(params.PCB_T + params.PLATE_TOP_TO_PCB_TOP, abs=1e-6)
    assert bb.min.Z < params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.SEAM_DEPTH   # thumb side is lower


def test_posts_are_spread_and_clear_of_the_pcbs():
    pts = topcase.post_positions("left")
    assert len(pts) >= 3
    union = topcase.pcb_union("left")
    inner = outline.case_outline_polygon("left").buffer(-params.BOTTOM_WALL)
    r = params.BOSS_D / 2
    for p in pts:
        assert union.distance(Point(p)) >= r + params.BOSS_PCB_CLEAR - 0.01
        assert inner.buffer(-(r - 1.0) + 1e-6).contains(Point(p))
    a = np.array(pts)
    assert np.ptp(a[:, 0]) > 40 and np.ptp(a[:, 1]) > 40


def test_walls_and_posts_do_not_touch_the_boards():
    # the skin is left out: it has no key openings yet, so the switches still stick through it
    shell = topcase.walls("left") + topcase.posts("left")
    for board in load_boards("left"):
        assert analysis.interference_volume(shell, board) < 1e-3, board.label


def test_nut_pocket_is_open_at_the_seam_and_screw_hole_is_blind(case):
    x, y = topcase.post_positions("left")[0]
    seam, n = topcase._seam_point_and_normal("left", x, y)
    probe = lambda d: case.is_inside(tuple(seam + n * d + np.array([0, 0, 0])))
    assert not probe(0.5) and not probe(params.NUT_M25_H)            # in the nut pocket
    assert probe(params.SEAM_DEPTH - params.PLATE_T / 2)             # skin above is solid
