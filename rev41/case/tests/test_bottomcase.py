import sys
from pathlib import Path

import numpy as np
import pytest
from build123d import Cylinder, Pos

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import batterydoor  # noqa: E402
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
    assert b.min.X - t.min.X == pytest.approx(gap, abs=0.05) and t.max.Y - params.TACTILE_BUMP_H - b.max.Y == pytest.approx(gap, abs=0.05)   # the dots stand proud of the +Y wall
    f = topcase.floor_profile("left")
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    assert b.max.Z == pytest.approx(skin_under, abs=1e-6)                         # the support pins touch the skin
    for x, y in ((108.5, -60.0),):                                  # main side, beside the battery door: outer face 0.8 above the wall edge
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


def test_screw_head_counterbores_stay_inside_the_plate_edge():
    from shapely.geometry import Point

    plate = bottomcase.bottom_outline("left")
    for p in topcase.post_positions("left"):
        if p in [tuple(q) for q in params.BOSS_FIXED_LEFT]:
            continue                      # TODO: the corner post (109.5, -38.6) leaves 2.83 < 3.0 to the plate edge
        assert plate.exterior.distance(Point(p)) >= params.SCREW_HEAD_CBORE_D / 2 + 0.5, p


def test_floor_is_deep_under_the_battery_door_pocket_and_ramps_up_beyond_it(bottom):
    from placeholders import battery_holder

    f = topcase.floor_profile("left")
    x0, y0, x1, y1 = batterydoor.layout("left")["pocket"]
    assert f["y_flat"] == pytest.approx(y0 - params.BOTTOM_DEEP_MARGIN)
    assert f["x_pts"][4][0] == pytest.approx(x0 - params.BOTTOM_DEEP_MARGIN)
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        assert topcase.floor_z("left", x, y) == pytest.approx(f["z_deep"])
    x = (x0 + x1) / 2
    y = y0 - params.BATTERY_POCKET_CLEAR - 0.4                    # plate just past the pocket
    assert bottom.is_inside((x, y, f["z_deep"] + 0.3)) and not bottom.is_inside((x, y, f["z_deep"] - 0.3))
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
    plate_feet, door_feet = bottomcase.feet("left"), bottomcase.feet("left", on_door=True)
    assert len(plate_feet) + len(door_feet) == len(params.FEET_LEFT) and door_feet
    for foot in plate_feet + door_feet:
        low = min(n @ np.array((v.X, v.Y, v.Z)) for v in foot.vertices())
        assert low == pytest.approx(d + params.FOOT_END_T, abs=1e-3)                     # column end (rim of the pad recess)
        floor = d + params.FOOT_PAD_T                                                     # pad top = recess floor
        assert any(abs(n @ np.array((v.X, v.Y, v.Z)) - floor) < 1e-3 for v in foot.vertices())
    assert (params.FOOT_PAD_D + params.FOOT_PAD_RECESS_CLEAR) / 2 < params.FOOT_D / 2 - 0.5     # rim around the recess
    # nothing else of the case comes closer to the desk than the pads plus the clearance (sampled along the outline)
    walls = topcase.walls("left")
    assert min(n @ np.array((v.X, v.Y, v.Z)) for v in walls.vertices()) >= d + params.FOOT_END_T + params.FOOT_MIN_CLEAR - 0.5


def test_foot_flares_stay_whole_inside_the_plate_and_the_door_edges():
    from shapely.geometry import Point

    need = params.FOOT_D / 2 + params.FOOT_FLARE_R + 1.0                  # flare radius + 1.0: not cut by an edge
    plate = bottomcase.bottom_outline("left")
    x0, y0, x1, y1 = batterydoor.layout("left")["door"]
    notch = batterydoor._post_keep("left")
    for i, (x, y) in enumerate(params.FEET_LEFT):
        if i == params.THUMB_FOOT:
            continue                                                       # the thumb foot is far from every edge
        if batterydoor.on_door("left", x, y):
            assert min(x - x0, x1 - x, y - y0, y1 - y) >= need - 0.1, (x, y)
            assert np.hypot(x - notch[0], y - notch[1]) - notch[2] >= need - 0.1, (x, y)   # nor from the post notch
        else:
            assert plate.exterior.distance(Point(x, y)) >= need - 0.1, (x, y)


def test_foot_columns_flare_at_the_root(bottom, door):
    r = params.FOOT_D / 2
    for on_door, solid in ((False, bottom), (True, door)):
        for top, n, _ in bottomcase._foot_axes("left", on_door):
            x, y = top[0], top[1]
            z = batterydoor.levels("left")["bottom"] if on_door else topcase.floor_z("left", x, y)
            u = np.array((1.0, 0.0, 0.0)); u -= n * (u @ n); u /= np.linalg.norm(u)       # across the axis
            for sign in (1, -1):
                p = top + n * ((z - 0.5 - top[2]) / n[2]) + sign * u * (r + 0.8)            # 0.5 below the floor, beside the column
                if sign == -1 and abs(x) < r + 3:
                    continue                                                                   # the -X edge clips the flare
                assert solid.is_inside(tuple(p)), (x, y, sign)
            p = top + n * ((z - params.FOOT_FLARE_L - 2.0 - top[2]) / n[2]) + u * (r + 0.8)   # below the flare: bare column
            assert not solid.is_inside(tuple(p)), (x, y)


def test_feet_and_pillars_do_not_poke_through_the_plate_faces(bottom):
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    for top, n, _ in bottomcase._foot_axes("left", False):          # columns end at the plate's inner face, also on a ramp
        x, y = top[0], top[1]
        for a in angles:
            px, py = x + 0.9 * params.FOOT_D / 2 * np.cos(a), y + 0.9 * params.FOOT_D / 2 * np.sin(a)
            assert not bottom.is_inside((px, py, topcase.floor_z("left", px, py, params.BOTTOM_WALL) + 0.3)), (x, y, a)
    for x, y in bottomcase.support_holes("left").values():          # pillars stop at the outer face, also on a ramp
        for a in angles:
            px, py = x + 0.95 * params.PILLAR_D / 2 * np.cos(a), y + 0.95 * params.PILLAR_D / 2 * np.sin(a)
            assert not bottom.is_inside((px, py, topcase.floor_z("left", px, py) - 0.3)), (x, y, a)


def test_ribs_stand_on_the_plate_and_keep_the_wire_gap_and_posts_clear(bottom):
    z = batterydoor.levels("left")
    z_in = z["bottom"] + params.BOTTOM_WALL
    lay = batterydoor.layout("left")
    ribs = bottomcase.ribs("left")
    assert len(ribs) == 2 and all(r.is_valid and r.volume > 50 for r in ribs)
    edge, strip = ribs
    plate = bottomcase.bottom_outline("left")
    x, y = 90.0, plate.intersection(__import__("shapely.geometry", fromlist=["LineString"]).LineString([(90, -300), (90, 50)])).bounds[3]
    assert bottom.is_inside((x, y - params.RIB_T / 2, z_in + params.EDGE_RIB_H - 0.3))            # +Y edge rim
    assert not bottom.is_inside((x, y - params.RIB_T - 0.4, z_in + params.EDGE_RIB_H - 0.3))       # nothing beside it
    y0 = lay["opening"][3] + params.STRIP_RIB_GAP + params.RIB_T / 2
    cx = (lay["holder"][0] + lay["holder"][2]) / 2
    assert bottom.is_inside((lay["holder"][0] + 3.0, y0, z["rim"] + params.STRIP_RIB_H - 0.3))   # bar
    assert not bottom.is_inside((cx, y0, z["rim"] + 1.0))                                           # wire gap
    for r in ribs:
        for px, py in topcase.post_positions("left"):
            assert vol(r & (Pos(px, py, -50) * Cylinder(params.BOSS_D / 2, 100))) < 1e-3


def test_support_pillars_go_through_the_main_board_holes_to_the_skin(bottom):
    skin_under = params.PCB_T + params.PLATE_TOP_TO_PCB_TOP - params.PLATE_T
    holes = bottomcase.support_holes("left")
    assert set(holes) == set(params.SUPPORT_HOLES)
    for x, y in holes.values():
        assert bottom.is_inside((x, y, skin_under - 0.2)) and bottom.is_inside((x, y, params.PCB_T / 2))
        assert not bottom.is_inside((x + params.PIN_D / 2 + 0.1, y, params.PCB_T / 2))      # only the thin pin in the hole
        inner = topcase.floor_z("left", x, y, params.BOTTOM_WALL)
        top = params.PILLAR_TOP_Z + params.PIN_SHOULDER_UP
        r = params.PIN_D / 2 + 0.1
        assert top - inner >= 0.15
        assert bottom.is_inside((x + r, y, top - 0.15))                                       # 45 degree shoulder under the sockets
        assert not bottom.is_inside((x + r, y, top + 0.05))                                   # nothing above it, 0.1+ under the sockets
        assert bottom.is_inside((x, y, skin_under - 0.02))                                    # the chamfered tip still reaches the skin


@pytest.fixture(scope="module")
def door():
    return bottomcase.battery_door("left")


def test_battery_door_is_flush_and_touches_nothing_when_locked(bottom, top, door):
    from placeholders import battery_holder

    assert door.is_valid and len(door.solids()) == 1
    lay, z = batterydoor.layout("left"), batterydoor.levels("left")
    assert z["bottom"] == pytest.approx(topcase.floor_profile("left")["z_deep"])          # flush with the floor
    holder = battery_holder("left")
    assert holder.bounding_box().min.Z == pytest.approx(z["top"])                          # the holder sits on the door
    for other in [bottom, top, holder] + load_boards("left") + list(core_board_placeholders("left").values()):
        assert vol(door & other) < 1e-3
    play = params.BATTERY_CEIL_GAP
    assert vol(bottom & (Pos(0, 0, play - 0.01) * door)) < 1e-3   # pressed up: the bump still fits its dimple
    assert vol(bottom & (Pos(0, 0, -params.KEY_HEAD_GAP + 0.01) * door)) < 1e-3
    assert vol(bottom & (Pos(0, 0, -params.KEY_HEAD_GAP - 0.2) * door)) > 1.0     # the stud heads hold it up
    assert vol(bottom & (Pos(0, -0.5, 0) * door)) > 1.0           # it cannot slide further towards -Y
    x, y, r = batterydoor._post_keep("left")                      # notched around the corner post's counterbore
    assert door.distance(Pos(x, y, 0) * Cylinder(r, 100)) > params.BATTERY_POCKET_CLEAR - 0.01


def test_battery_door_pushed_towards_plus_y_drops_out_with_the_holder(bottom, top, door):
    from placeholders import battery_holder

    s = params.BATTERY_SLIDE
    cartridge = [door, battery_holder("left")]
    for dz in (0.0, -0.5, -1.5, -3.0, -6.0, -12.0, -20.0):
        for part in cartridge:
            moved = Pos(0, s, dz) * part
            assert vol(bottom & moved) < 1e-3 and vol(top & moved) < 1e-3, dz


def test_battery_door_locks_with_a_bump_in_a_dimple(door):
    (tx0, _, tx1, _), by = batterydoor._tongue("left")
    z = batterydoor.levels("left")
    cx = (tx0 + tx1) / 2
    assert door.is_inside((cx, by, z["top"] + params.BATTERY_BUMP_H / 2))                  # bump on the tongue
    assert not door.is_inside((tx0 - params.BATTERY_TONGUE_SLOT / 2, by, (z["top"] + z["bottom"]) / 2))   # slot beside it


def test_thumb_ledge_sits_on_the_plate_under_the_thumb_pcb_edge(bottom):
    ledge = topcase.thumb_ledge("left")
    assert ledge.is_valid and ledge.volume > 10
    thumb = next(b for b in load_boards("left") if b.label == "thumb_2x3")
    assert vol(ledge & thumb) < 1e-6
    assert vol(ledge & bottom) < 1e-3                       # touches the plate's inner face, no overlap
    assert bottom.distance(ledge) < 1e-3
