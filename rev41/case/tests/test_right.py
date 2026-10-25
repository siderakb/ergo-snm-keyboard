"""Right hand: the left case mirrored (params.MIRROR_X), with the 1x2 thumb keys and the trackball (cup, sensor, pod)."""

import sys
from pathlib import Path

import numpy as np
import pytest
from build123d import Pos, Sphere

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import analysis  # noqa: E402
import batterydoor  # noqa: E402
import bottomcase  # noqa: E402
import geometry  # noqa: E402
import outline  # noqa: E402
import params  # noqa: E402
import topcase  # noqa: E402
import trackball  # noqa: E402
from assembly import load_boards  # noqa: E402
from placeholders import battery_holder, core_board_placeholders  # noqa: E402


def test_outline_is_the_left_outline_mirrored():
    left, right = outline.case_outline_polygon("left"), outline.case_outline_polygon("right")
    x0, y0, x1, y1 = left.bounds
    assert right.area == pytest.approx(left.area, rel=1e-9)
    assert np.allclose(right.bounds, (params.MIRROR_X - x1, y0, params.MIRROR_X - x0, y1), atol=1e-6)


def test_posts_and_battery_door_are_mirrored():
    for (xl, yl), (xr, yr) in zip(topcase.post_positions("left"), topcase.post_positions("right")):
        shift = next((d for s, d in params.BOSS_SHIFT_RIGHT.items() if np.hypot(xr - d[0] - s[0], yr - d[1] - s[1]) < 1.0), (0.0, 0.0))
        assert (xr - shift[0], yr - shift[1]) == pytest.approx((params.MIRROR_X - xl, yl))
    l, r = batterydoor.layout("left"), batterydoor.layout("right")
    assert r["door"] == pytest.approx((params.MIRROR_X - l["door"][2], l["door"][1], params.MIRROR_X - l["door"][0], l["door"][3]))
    core = next(b for b in load_boards("right") if b.label == "core_board_e73").bounding_box()
    assert battery_holder("right").bounding_box().max.X < core.min.X        # holder on the core board's -X side


def test_ball_hole_goes_through_the_thumb_plate():
    skin = topcase.top_skin_keyed("right")
    _, n = outline.plate_plane("thumb_1x2", "right")
    c = np.array(params.BALL_HOLE_CENTER_RIGHT)
    mid = lambda p: tuple(p - params.PLATE_T / 2 * n)                       # mid-thickness of the skin
    u = np.cross(n, (0.0, 0.0, 1.0))
    u /= np.linalg.norm(u)
    assert not skin.is_inside(mid(c)) and not skin.is_inside(mid(c + (params.BALL_HOLE_D / 2 - 0.3) * u))
    assert skin.is_inside(mid(c + (params.BALL_HOLE_D / 2 + 0.5) * u))


@pytest.fixture(scope="module")
def right_case():
    return {"top": topcase.top_case("right"), "bottom": bottomcase.bottom_case("right"), "door": bottomcase.battery_door("right"),
            "cup": trackball.cup()}


def test_right_case_clears_the_boards_placeholders_and_trackball_parts(right_case):
    parts = ({b.label: b for b in load_boards("right")} | core_board_placeholders("right") | {"holder": battery_holder("right")}
             | trackball.sensor_parts() | {"ball": trackball.ball()} | {f"steel_{i}": s for i, s in enumerate(trackball.steel_balls())})
    for cn, c in right_case.items():
        for n, p in parts.items() | {"cup": right_case["cup"]}.items():
            if cn != n:
                assert analysis.interference_volume(c, p) < 0.01, (cn, n)


def test_door_matches_the_left_one():
    # the door itself; its foot is longer on the right (the trackball pod lifts the whole half)
    assert batterydoor.door("right").volume == pytest.approx(batterydoor.door("left").volume, rel=1e-4)


def test_ball_rests_on_three_steel_balls_and_clears_the_cup(right_case):
    centres = trackball.bearings()
    assert len(centres) == 3
    for p in centres:
        assert np.linalg.norm(p) == pytest.approx(params.BALL_D / 2 + params.BEARING_BALL_D / 2)       # touching the ball
        assert np.degrees(np.arccos(-p[2] / np.linalg.norm(p))) == pytest.approx(params.BEARING_POLAR)
    assert right_case["cup"].distance_to(trackball.ball()) == pytest.approx(params.BALL_CUP_GAP, abs=0.05)


def test_second_seat_set_is_in_the_gaps_at_the_steeper_angle(right_case):
    alt = trackball.alt_bearings()
    assert len(alt) == 3
    for p in alt:
        assert np.linalg.norm(p) == pytest.approx(params.BALL_D / 2 + params.BEARING_BALL_D / 2)
        assert np.degrees(np.arccos(-p[2] / np.linalg.norm(p))) == pytest.approx(params.BEARING_POLAR_ALT)
        az = np.degrees(np.arctan2(p[1], p[0])) % 360
        assert min(abs(((az - a) + 180) % 360 - 180) for a in (0, 120, 240)) == pytest.approx(60.0)    # midway between
        ball = trackball.loc() * Pos(*p) * Sphere(params.BEARING_BALL_D / 2)
        assert analysis.interference_volume(right_case["cup"], ball) < 1e-6                         # the seat is open
        k = p / np.linalg.norm(p)
        behind = trackball.to_case(*(p + 2.0 * k))                     # past the seat bottom, outside the shell: the boss
        assert right_case["cup"].is_inside(tuple(behind))


def test_cup_rim_clears_the_arm_walls(right_case):
    assert right_case["cup"].distance_to(right_case["top"]) >= 0.5 - 0.05


def test_sensor_stack_and_pod_depths():
    R = params.BALL_D / 2
    lens_top = trackball.W_BOARD + params.PMW3610_LENS_PROTRUSION
    assert -R - lens_top == pytest.approx(params.PMW3610_WORKING_DISTANCE)          # nominal, with the nominal shim
    assert trackball.W_SEAT - trackball.W_BOARD == pytest.approx(params.SENSOR_SHIM_NOM)
    assert trackball.W_LOW - trackball.W_POD_IN == pytest.approx(params.BALL_POD_CLEAR)
    parts = trackball.sensor_parts()
    _, _, _, n = trackball.frame()
    c = np.array(geometry.ball_center())
    low = min(float((np.array((v.X, v.Y, v.Z)) - c) @ n) for s in parts.values() for v in s.vertices())
    assert low >= trackball.W_POD_IN                                                # nothing below the pod floor


def test_thumb_foot_stands_under_the_pod():
    axes = bottomcase._foot_axes("right", False)
    x, y = trackball.foot_xy()
    assert any(np.hypot(t[0] - x, t[1] - y) < 1e-6 for t, _, _ in axes)
    assert topcase.floor_z("right", x, y) == pytest.approx(trackball.pod_floor_z(x, y), abs=1e-6)


def test_board_sandwich_screws_engage_the_nut_and_stay_blind():
    shim_max = 2 * params.SENSOR_SHIM_NOM
    tip_short = trackball.W_TIP - (shim_max - params.SENSOR_SHIM_NOM)             # thickest shim pack pushes the cup up
    assert tip_short >= trackball.W_SEAT + params.NUT_M25_H                          # the whole nut is engaged
    assert trackball.W_TIP + 0.5 <= params.CUP_BLOCK_TOP                             # blind hole stays inside the block
    proud = trackball.W_POD_OUT - (trackball.W_HEAD - params.SENSOR_SCREW_HEAD_H)
    assert proud <= params.BOTTOM_RECESS + 1e-9                                       # head no lower than the walls' edge
    assert trackball.W_HEAD < trackball.W_POD_IN                                     # counterbore stays in the floor
    assert trackball.W_SENSOR - trackball.W_HEAD >= 1.5                              # material under the head


def test_cup_seat_clears_the_sensor_pins_on_bcu():
    u0, u1, v0, v1 = trackball.pin_field()
    c = params.PMW3610_PIN_CLEAR - 0.1
    pins = trackball.loc() * trackball._box(u0 + c, u1 - c, v0 + c, v1 - c, trackball.W_BOARD, trackball.W_BOARD + 1.5)
    assert analysis.interference_volume(trackball.cup(), pins) < 1e-6


def test_standoffs_clear_the_sensor_parts():
    parts = trackball.sensor_parts()
    for s in trackball.standoffs():
        for k in ("pmw3610_ic", "pmw3610_fpc"):
            assert s.distance_to(parts[k]) >= 0.5, k
