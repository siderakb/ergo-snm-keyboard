import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import params  # noqa: E402
from geometry import local_to_case, placement, to_case  # noqa: E402


def test_right_main_board_is_y_negated():
    assert to_case("main_board", 153.05, 59.319, hand="right") == (153.05, -59.319, 0.0)


def test_left_main_board_is_flipped_about_y():
    x, y, z = to_case("main_board", 153.05, 59.319, 0.0, hand="left")
    assert abs(x - (203.847 - 153.05)) < 1e-6 and abs(y + 59.319) < 1e-6 and abs(z - params.PCB_T) < 1e-6


def test_core_headers_meet_main_sockets_right():
    for (cx, cy), (mx, my) in (((158.115, 74.295), (153.05, 59.319)),
                               ((158.115, 93.345), (153.05, 78.369))):
        x, y, _ = to_case("core_board_e73", cx, cy, hand="right")
        assert abs(x - mx) < 1e-6 and abs(y + my) < 1e-6


def test_all_placements_are_proper_rotations():
    for hand, boards in params.PLACEMENTS.items():
        for name in boards:
            R, _ = placement(name, hand)
            assert np.allclose(R @ R.T, np.eye(3), atol=2e-3), (hand, name)
            assert abs(np.linalg.det(R) - 1) < 2e-3, (hand, name)


def test_left_thumb_2x3_tilt_and_yaw():
    R, _ = placement("thumb_2x3", "left")
    # flipped board: local +Z points down; the plate normal (-local Z) is tilted 20 deg
    assert abs(np.degrees(np.arccos(-R[2, 2])) - 20.0) < 0.05
    assert abs(np.degrees(np.arctan2(R[1, 0], R[0, 0])) - 150.0) < 0.05


def test_core_header_centres_meet_socket_centres_both_hands():
    # STEP-local body centres: sockets on main_board, headers on core_board_e73.
    for hand in ("left", "right"):
        for (sx, sy), (hx, hy) in (((158.765, -58.684), (152.4, -73.66)),
                                   ((158.765, -77.734), (152.4, -92.71))):
            sx_, sy_, _ = local_to_case("main_board", sx, sy, 0.0, hand=hand)
            hx_, hy_, _ = local_to_case("core_board_e73", hx, hy, 0.0, hand=hand)
            assert abs(sx_ - hx_) < 0.05 and abs(sy_ - hy_) < 0.05, hand


def test_core_board_is_below_main_for_both_hands():
    for hand in ("left", "right"):
        zc = max(to_case("core_board_e73", 0, 0, z, hand=hand)[2] for z in (0, params.PCB_T))
        zm = min(to_case("main_board", 0, 0, z, hand=hand)[2] for z in (0, params.PCB_T))
        assert abs((zm - zc) - params.BOARD_GAP) < 1e-6


def test_right_thumb_1x2_is_mirror_image_of_left_first_column():
    # right SW4/SW8 (X=187.452) correspond to left 2x3 SW1/SW5 (X=127.0); compare on the plate-facing face
    for ky in (76.2, 95.25):
        xl, yl, zl = to_case("thumb_2x3", 127.0, ky, 0.0, hand="left")
        xr, yr, zr = to_case("thumb_1x2", 187.452, ky, params.PCB_T, hand="right")
        assert abs(xr - (params.MIRROR_X - xl)) < 0.01 and abs(yr - yl) < 0.01 and abs(zr - zl) < 0.01   # both slide in


def test_ball_top_is_BALL_RAISE_above_keycap_top():
    import numpy as np
    from geometry import ball_center

    n = placement("thumb_1x2", "right")[0][:, 2]
    top = np.array(ball_center()) + params.BALL_D / 2 * n          # ball point farthest along the normal
    plate_top = np.array(params.BALL_HOLE_CENTER_RIGHT)
    assert abs((top - plate_top) @ n - (params.KEYCAP_TOP + params.BALL_RAISE)) < 1e-3


def test_sensor_lens_plane_is_working_distance_below_ball():
    import numpy as np
    from geometry import ball_center, sensor_lens_plane_center

    n = placement("thumb_1x2", "right")[0][:, 2]
    gap = (np.array(ball_center()) - np.array(sensor_lens_plane_center())) @ n
    assert abs(gap - (params.BALL_D / 2 + params.PMW3610_WORKING_DISTANCE)) < 1e-3


def test_sensor_stack_matches_pmw3610_section_drawing():
    import numpy as np
    from geometry import sensor_lens_plane_center, sensor_stack

    st = sensor_stack()
    assert np.allclose(st["lens"], sensor_lens_plane_center(), atol=1e-3)
    n = placement("thumb_1x2", "right")[0][:, 2]
    d = lambda a, b: float((np.array(st[a]) - np.array(st[b])) @ n)
    assert abs(d("board_ball_face", "board_sensor_face") - params.PMW3610_BOARD_T) < 1e-3
    assert abs(d("lens", "board_ball_face") - params.PMW3610_LENS_PROTRUSION) < 1e-3   # 3.40 gap in the drawing


def test_ball_hole_is_centred_on_the_inner_2x2_keys():
    import numpy as np

    kx, ky = (146.05 + 165.1) / 2, (76.2 + 95.25) / 2          # 2x3 board SW2, SW3, SW6, SW7
    xs = kx + (187.452 - 127.0)                                # same column position in 1x2 board coordinates
    zs_top = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP
    c = np.array(local_to_case("thumb_1x2", xs, -ky, zs_top, hand="right"))
    assert np.allclose(c, params.BALL_HOLE_CENTER_RIGHT, atol=0.01)
