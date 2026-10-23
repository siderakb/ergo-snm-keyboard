import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import outline  # noqa: E402
import params  # noqa: E402


@pytest.mark.parametrize("hand", ["left", "right"])
def test_skin_is_one_valid_solid_topped_at_the_plate_height(hand):
    skin = outline.top_skin(hand)
    assert skin.is_valid and len(skin.solids()) == 1 and skin.volume > 0
    assert skin.bounding_box().max.Z == pytest.approx(params.PCB_T + params.PLATE_TOP_TO_PCB_TOP, abs=1e-6)


@pytest.mark.parametrize("hand", ["left", "right"])
def test_skin_covers_the_core_board_in_plan(hand):
    skin = outline.top_skin(hand)
    bb = skin.bounding_box()
    for x, y in outline._board_plan_points("core_board_e73", hand):
        assert bb.min.X <= x <= bb.max.X and bb.min.Y <= y <= bb.max.Y


@pytest.mark.parametrize("hand", ["left", "right"])
def test_crease_lies_in_the_wall_margin_just_inside_the_thumb_area_edge(hand):
    """The thumb plane reaches the main plate top (the crease) between the thumb PCB's inner edge and
    OUTLINE_OFFSET towards the main board, so every thumb key sits on the tilted plane."""
    board = outline.thumb_board(hand)
    point, n = outline.plate_plane(board, hand)
    pts = outline._board_plan_points(board, hand, params.THUMB_BOARDS[board]["x_range"])
    if hand == "right":                      # the ball hole is the thumb area's inner part: use its rim
        cx, cy, _ = params.BALL_HOLE_CENTER_RIGHT
        pts = [(cx + params.BALL_HOLE_D / 2 * np.cos(a), cy + params.BALL_HOLE_D / 2 * np.sin(a))
               for a in np.linspace(0, 2 * np.pi, 72, endpoint=False)]
    z_at = lambda x, y: point[2] - ((x - point[0]) * n[0] + (y - point[1]) * n[1]) / n[2]
    z_inner = max(z_at(x, y) for x, y in pts)                     # plane height at the PCB's inner edge
    tan_tilt = np.hypot(n[0], n[1]) / n[2]
    crease_distance = (params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - z_inner) / tan_tilt
    # left: the 2x3 PCB's inner edge; right: the ball hole rim (which sits ~1.5 mm inside the same edge)
    assert 0 < crease_distance <= outline.OUTLINE_OFFSET + 3.0


def test_hull_is_convex_and_contains_all_points():
    pts = [(0, 0), (4, 0), (4, 3), (0, 3), (2, 1), (1, 2)]
    hull = outline._hull(pts)
    assert sorted(hull) == [(0, 0), (0, 3), (4, 0), (4, 3)]


def test_left_outline_is_not_convex_and_contains_every_board():
    from shapely.geometry import MultiPoint, Point

    poly = outline.case_outline_polygon("left")
    assert poly.is_valid and len(poly.interiors) == 0
    assert poly.area < MultiPoint(outline.case_outline_points("left")).convex_hull.area     # concave neck
    for board in ("main_board", "core_board_e73"):
        assert all(poly.contains(Point(p)) for p in outline._board_plan_points(board, "left"))
    x_range = params.THUMB_BOARDS["thumb_2x3"]["x_range"]
    assert all(poly.contains(Point(p)) for p in outline._board_plan_points("thumb_2x3", "left", x_range))


def test_left_outline_bottom_edge_is_parallel_to_x():
    poly = outline.case_outline_polygon("left")
    pts = outline._board_plan_points("main_board", "left")
    y_bottom = min(p[1] for p in pts) - outline.OUTLINE_OFFSET
    flat = [(x, y) for x, y in poly.exterior.coords if abs(y - y_bottom) < 1e-6]
    xs = [x for x, _ in flat]
    assert max(xs) - min(xs) > 0.6 * (max(p[0] for p in pts) - min(p[0] for p in pts))


def test_left_outline_right_edge_is_straight_down_from_the_top_right_corner():
    poly = outline.case_outline_polygon("left")
    pts = outline._board_plan_points("main_board", "left")
    x_edge = max(p[0] for p in pts) + outline.OUTLINE_OFFSET
    on_edge = [y for x, y in poly.exterior.coords if abs(x - x_edge) < 1e-3]
    assert len(on_edge) >= 2 and max(on_edge) - min(on_edge) > 60      # one long vertical edge, not a slanted chord
