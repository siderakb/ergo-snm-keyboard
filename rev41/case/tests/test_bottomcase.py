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
    f = topcase.floor_profile("left")
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    assert b.max.Z == pytest.approx(skin_under, abs=1e-6)                         # the support pins touch the skin
    for x, y in ((90.0, -60.0),):                                                   # main side: outer face 0.8 above the wall edge
        assert bottom.is_inside((x, y, -19.0 + 0.3)) and not bottom.is_inside((x, y, -19.0 - 0.3))


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


def test_floor_is_deep_under_the_battery_holder_and_ramps_up_beyond_its_tail(bottom):
    from placeholders import battery_holder

    f = topcase.floor_profile("left")
    bb = battery_holder("left").bounding_box()
    assert f["y_flat"] == pytest.approx(bb.min.Y - params.BOTTOM_DEEP_MARGIN)
    x = (bb.min.X + bb.max.X) / 2
    assert bottom.is_inside((x, bb.min.Y + 5, f["z_deep"] + 0.3)) and not bottom.is_inside((x, bb.min.Y + 5, f["z_deep"] - 0.3))
    run = (f["z_shallow"] - f["z_deep"]) / np.tan(np.radians(params.BOTTOM_RAMP_ANGLE))
    y = f["y_flat"] - run - 5
    assert bottom.is_inside((x, y, f["z_shallow"] + 0.3)) and not bottom.is_inside((x, y, f["z_shallow"] - 0.3))
    assert vol(bottom & battery_holder("left")) < 1e-3


def test_x_profile_steps_down_from_minus_x_to_the_battery_and_keeps_screw_heads_flat():
    f = topcase.floor_profile("left")
    assert topcase.floor_z("left", 5.0, -60.0) == pytest.approx(f["z_shallow"])      # -X: thinnest
    assert topcase.floor_z("left", 45.0, -60.0) == pytest.approx(f["z_core"])        # under the core board
    assert topcase.floor_z("left", 90.0, -60.0) == pytest.approx(f["z_deep"])        # under the battery holder
    assert topcase.floor_z("left", 90.0, -130.0) == pytest.approx(f["z_shallow"])    # past the battery tail (Y profile)
    r = params.SCREW_HEAD_CBORE_D / 2
    for x, y in topcase.post_positions("left"):
        zs = [topcase.floor_z("left", x + r * np.cos(a), y + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 16)]
        assert np.ptp(zs) < params.SCREW_HEAD_SINK, (x, y)        # the flat counterbore bottom still seats the head


def test_feet_end_on_the_tented_desk_plane(bottom):
    n, d = bottomcase.desk_plane("left")
    assert np.degrees(np.arccos(n[2])) == pytest.approx(params.TENT_ANGLE) and n[0] > 0     # +X (thumb side) up
    for foot in bottomcase.feet("left"):
        low = min(n @ np.array((v.X, v.Y, v.Z)) for v in foot.vertices())
        assert low == pytest.approx(d + params.FOOT_PAD_T, abs=1e-3)
    # nothing else of the case comes closer to the desk than the pads plus the clearance (sampled along the outline)
    walls = topcase.walls("left")
    assert min(n @ np.array((v.X, v.Y, v.Z)) for v in walls.vertices()) >= d + params.FOOT_PAD_T + params.FOOT_MIN_CLEAR - 0.5


def test_support_pillars_go_through_the_main_board_holes_to_the_skin(bottom):
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    holes = bottomcase.support_holes("left")
    assert set(holes) == set(params.SUPPORT_HOLES_LEFT)
    for x, y in holes.values():
        assert bottom.is_inside((x, y, skin_under - 0.2)) and bottom.is_inside((x, y, params.PCB_T / 2))
        assert not bottom.is_inside((x + params.PIN_D / 2 + 0.1, y, params.PCB_T / 2))      # only the thin pin in the hole


def test_thumb_ledge_sits_on_the_plate_under_the_thumb_pcb_edge(bottom):
    ledge = topcase.thumb_ledge("left")
    assert ledge.is_valid and ledge.volume > 10
    thumb = next(b for b in load_boards("left") if b.label == "thumb_2x3")
    assert vol(ledge & thumb) < 1e-6
    assert vol(ledge & bottom) < 1e-3                       # touches the plate's inner face, no overlap
    assert bottom.distance(ledge) < 1e-3
