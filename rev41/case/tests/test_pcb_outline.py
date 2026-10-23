import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build123d import import_step  # noqa: E402

import pcb_ref  # noqa: E402

STEP = Path(__file__).resolve().parents[1] / "step"


def test_arc_points_quarter_circle_and_direction():
    pts = pcb_ref._arc_points((1, 0), (2 ** -0.5, 2 ** -0.5), (0, 1))
    assert all(abs(x * x + y * y - 1) < 1e-9 for x, y in pts)
    assert pts[0] == pytest.approx((1, 0)) and pts[-1] == pytest.approx((0, 1))
    cw = pcb_ref._arc_points((0, 1), (2 ** -0.5, 2 ** -0.5), (1, 0))      # clockwise quarter
    assert all(x >= -1e-9 and y >= -1e-9 for x, y in cw)


def test_loops_counts():
    assert len(pcb_ref.outline_loops(pcb_ref.load_board("main_board"))) == 1
    assert len(pcb_ref.outline_loops(pcb_ref.load_board("thumb_cluster"))) == 2     # panel of two boards
    assert len(pcb_ref.outline_loops(pcb_ref.load_board("core_board_e73"))) == 1


@pytest.mark.skipif(not (STEP / "main_board.step").exists(), reason="run tools/setup.py")
def test_outline_area_matches_step_substrate_of_a_board_without_switch_cutouts():
    # core_board_e73 has no key cut-outs, so polygon area x STEP substrate thickness is the substrate volume
    area = pcb_ref.outline_area(pcb_ref.load_board("core_board_e73"))
    substrate = max(import_step(STEP / "core_board_e73.step").solids(), key=lambda s: s.volume)
    assert area * 1.51 == pytest.approx(substrate.volume, rel=0.03)


@pytest.mark.skipif(not (STEP / "main_board.step").exists(), reason="run tools/setup.py")
@pytest.mark.parametrize("name", ["main_board", "thumb_cluster"])
def test_outline_area_bounds_substrate_with_key_cutouts(name):
    area = pcb_ref.outline_area(pcb_ref.load_board(name))
    substrate = max(import_step(STEP / f"{name}.step").solids(), key=lambda s: s.volume)
    assert 0.7 < substrate.volume / (area * 1.51) < 1.0          # holes only remove material


def test_outline_in_case_left_main_is_mirrored_bbox():
    from geometry import outline_in_case

    (loop,) = outline_in_case("main_board", hand="left")
    xs = [p[0] for p in loop]
    assert min(xs) == pytest.approx(203.847 - 207.264, abs=1e-3) and max(xs) == pytest.approx(203.847 - 91.186, abs=1e-3)
