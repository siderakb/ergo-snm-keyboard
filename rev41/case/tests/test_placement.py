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
