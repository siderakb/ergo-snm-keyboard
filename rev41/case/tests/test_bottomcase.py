import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import bottomcase  # noqa: E402
import params  # noqa: E402
import topcase  # noqa: E402
from assembly import load_boards  # noqa: E402
from placeholders import core_board_placeholders  # noqa: E402


def vol(shape):
    return shape.volume if shape else 0.0


@pytest.fixture(scope="module")
def bottom():
    return bottomcase.bottom_case("left")


@pytest.fixture(scope="module")
def top():
    return topcase.top_case("left")


def test_bottom_case_is_one_valid_solid(bottom):
    assert bottom.is_valid and len(bottom.solids()) == 1


def test_plate_sits_inside_the_walls_recessed_from_their_bottom_edge(bottom, top):
    t, b = top.bounding_box(), bottom.bounding_box()
    gap = params.BOTTOM_WALL + params.PLATE_SIDE_CLEAR
    assert b.min.X - t.min.X == pytest.approx(gap, abs=0.05) and t.max.Y - b.max.Y == pytest.approx(gap, abs=0.05)
    assert b.max.Z == pytest.approx(-19.0 + params.BOTTOM_WALL, abs=1e-6)          # main plate inner face
    for x, y in ((40.0, -60.0),):                                                   # main side: outer face 0.8 above the wall edge
        assert bottom.is_inside((x, y, -19.0 + 0.3)) and not bottom.is_inside((x, y, -19.0 - 0.3))
    assert t.min.Z < b.min.Z                                                        # walls hang past the plate everywhere


def test_bottom_case_does_not_touch_the_top_case_or_the_boards(bottom, top):
    assert vol(bottom & top) < 1e-3
    for board in load_boards("left"):
        assert vol(bottom & board) < 1e-3, board.label
    for label, shape in core_board_placeholders("left").items():
        assert vol(bottom & shape) < 1e-3, label


def test_screw_holes_and_counterbores_line_up_with_the_posts(bottom):
    for x, y in topcase.post_positions("left"):
        top_pt, n, t = topcase.post_axis("left", x, y)
        on_axis = lambda d: top_pt - (t + d) * n
        assert not bottom.is_inside(tuple(on_axis(params.BOTTOM_WALL / 2)))                      # through hole
        c = bottomcase.bottom_outline("left").centroid
        u = np.array((c.x - x, c.y - y, 0.0)); u -= n * (u @ n); u /= np.linalg.norm(u)      # towards the plate inside
        assert bottom.is_inside(tuple(on_axis(0.5) + u * (params.SCREW_M25_CLEAR_D / 2 + 0.5)))   # plate around the hole
        sink = on_axis(params.BOTTOM_WALL - params.SCREW_HEAD_SINK / 2) + u * (params.SCREW_HEAD_CBORE_D / 2 - 0.2)
        assert not bottom.is_inside(tuple(sink))                                                  # head counterbore
