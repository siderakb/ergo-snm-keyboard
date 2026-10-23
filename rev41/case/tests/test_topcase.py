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
    all_pts = topcase.post_positions("left")
    pts, extra = all_pts[:params.BOSS_COUNT], all_pts[params.BOSS_COUNT:]
    assert len(pts) >= 3 and len(extra) == len(params.BOSS_EXTRA_LEFT)
    r_nut = (params.NUT_M25_OD + params.NUT_POCKET_CLEAR) / 2
    outer = outline.case_outline_polygon("left")
    for p in extra:      # trimmed boss: at least 1.4 mm of material around the nut pocket on both sides
        assert topcase.pcb_union("left").distance(Point(p)) >= params.BOSS_PCB_CLEAR + r_nut + 1.4
        assert outer.exterior.distance(Point(p)) >= r_nut + 1.4
    union = topcase.pcb_union("left")
    inner = outline.case_outline_polygon("left").buffer(-params.BOTTOM_WALL)
    r = params.BOSS_D / 2
    for p in pts:
        assert union.distance(Point(p)) >= r + params.BOSS_PCB_CLEAR - 0.01
        assert inner.buffer(-(r - 1.0) + 1e-6).contains(Point(p))
    a = np.array(all_pts)
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


def test_pockets_are_empty_in_walls_and_in_the_fused_case(case):
    r_nut = (params.NUT_M25_OD + params.NUT_POCKET_CLEAR) / 2
    w = topcase.walls("left")
    for x, y in topcase.post_positions("left"):
        seam, n = topcase._seam_point_and_normal("left", x, y)
        for ang in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            u = np.array([np.cos(ang), np.sin(ang), 0.0])
            u = u - n * np.dot(u, n)                       # in the plane perpendicular to the post axis
            u /= np.linalg.norm(u)
            pt = seam + n * 1.0 + u * (r_nut - 0.1)        # just inside the pocket wall
            assert not w.is_inside(tuple(pt)) and not case.is_inside(tuple(pt)), (x, y, ang)


def test_key_openings_cut_the_skin_square_for_every_switch():
    import outline
    cuts = topcase.key_cutouts("left")
    assert len(cuts) == 35                      # 29 main + 6 thumb keys
    skin = outline.top_skin("left")
    for c in cuts:
        skin = skin - c
    cut = outline.top_skin("left").volume - skin.volume
    assert cut == pytest.approx(len(cuts) * params.SWITCH_BODY**2 * params.PLATE_T, rel=1e-3)


def test_relief_pockets_clear_the_skin_of_main_and_thumb_board_parts():
    skin = topcase.top_skin_keyed("left")
    plain = outline.top_skin("left")
    for board in load_boards("left"):
        if board.label in ("main_board", "thumb_2x3"):
            assert analysis.interference_volume(plain, board) > 1.0      # without relief the parts hit the skin
            assert analysis.interference_volume(skin, board) == pytest.approx(0.0, abs=1e-6)


def test_relief_includes_both_2x10_socket_pin_rows():
    wide = [c for c in topcase.relief_cutouts("left") if c.bounding_box().size.X > 10]
    assert len(wide) == 2


def test_led_slots_join_each_plate_side_led_to_a_key_opening():
    slots = topcase.led_slots("left")
    assert len(slots) == 2                     # LD1, LD3 sit on the plate side in the left hand (LD2, LD4 are the alternates)
    keys = topcase.key_cutouts("left")
    for slot in slots:
        assert any(analysis.interference_volume(slot, k) > 0.5 for k in keys)


def test_thumb_end_wall_is_perpendicular_to_the_tilted_plate():
    _, n = outline.plate_plane("thumb_2x3", "left")
    fall = np.array(n[:2]) / np.hypot(n[0], n[1])
    vec = lambda v: np.array([v.X, v.Y, v.Z])
    planar = [f for f in topcase.walls("left").faces() if str(f.geom_type).endswith("PLANE") and f.area > 100 and vec(f.normal_at()) @ np.array([*fall, 0.0]) > 0.9 * np.cos(np.radians(20))]
    end = max(planar, key=lambda f: vec(f.center())[:2] @ fall)
    assert abs(vec(end.normal_at()) @ n) < 1e-3       # face normal lies in the plate plane
