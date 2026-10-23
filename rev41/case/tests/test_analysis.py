import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build123d import Box, Pos  # noqa: E402

import analysis  # noqa: E402


def test_interference_overlap_and_touch():
    a = Box(10, 10, 10)
    assert abs(analysis.interference_volume(a, Pos(5, 0, 0) * Box(10, 10, 10)) - 500) < 1e-3
    assert analysis.interference_volume(a, Pos(10, 0, 0) * Box(10, 10, 10)) < 1e-6


def test_thin_wall_detected():
    plate = Box(30, 30, 0.5)
    spots = analysis.thin_spots(plate, 0.8)
    assert spots and spots[0][0] < 0.8


def test_thick_wall_passes():
    assert analysis.thin_spots(Box(30, 30, 1.2), 0.8) == []


def test_hollow_box_wall():
    shell = Box(30, 30, 30) - Box(28.4, 28.4, 28.4)   # 0.8 wall
    assert analysis.thin_spots(shell, 0.7) == []
    assert analysis.thin_spots(shell, 1.0)


def test_size_limits_and_wall_class():
    assert analysis.within_max_size(Box(300, 200, 100), "mjf")[0]
    assert not analysis.within_max_size(Box(400, 10, 10), "mjf")[0]
    assert analysis.size_class_wall("sla", 80) == 1.5
    assert analysis.size_class_wall("sla", 120) == 2.0
    assert analysis.size_class_wall("mjf", 400) == 2.0
