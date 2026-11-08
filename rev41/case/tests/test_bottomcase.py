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
        assert bottom.is_inside(tuple(on_axis(0.5) + u * (params.BOTTOM_SCREW_CLEAR_D / 2 + 0.5)))   # plate around the hole
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
    assert len(plate_feet) == len(params.FEET_LEFT) and not door_feet                  # no foot on the battery door
    for foot in plate_feet + door_feet:
        low = min(n @ np.array((v.X, v.Y, v.Z)) for v in foot.vertices())
        assert low == pytest.approx(d + params.FOOT_END_T, abs=1e-3)                     # column end (rim of the pad recess)
        floor = d + params.FOOT_PAD_T                                                     # pad top = recess floor
        assert any(abs(n @ np.array((v.X, v.Y, v.Z)) - floor) < 1e-3 for v in foot.vertices())
    assert (params.FOOT_PAD_D + params.FOOT_PAD_RECESS_CLEAR) / 2 < params.FOOT_D / 2 - 0.5     # rim around the recess
    # nothing else of the case comes closer to the desk than the pads plus the clearance (sampled along the outline)
    walls = topcase.walls("left")
    assert min(n @ np.array((v.X, v.Y, v.Z)) for v in walls.vertices()) >= d + params.FOOT_END_T + params.FOOT_MIN_CLEAR - 0.5


def test_foot_flares_stay_whole_inside_the_plate_and_the_foot_beside_the_door_clears_the_pocket():
    from shapely.geometry import Point, box

    need = params.FOOT_D / 2 + params.FOOT_FLARE_R + 1.0                  # flare radius + 1.0: not cut by an edge
    plate = bottomcase.bottom_outline("left")
    x0, y0, x1, y1 = batterydoor.layout("left")["pocket"]
    g = params.BATTERY_POCKET_CLEAR + params.BATTERY_POCKET_CHAMFER
    pocket = box(x0 - g, y0 - g, x1 + g, y1 + g)
    notches = [n for _, n in batterydoor.grooves("left")]
    for i, (x, y) in enumerate(params.FEET_LEFT):
        assert not batterydoor.on_door("left", x, y), (x, y)
        if i == params.THUMB_FOOT:
            continue                                                       # the thumb foot is far from every edge
        if i == params.FOOT_BESIDE_DOOR:                                   # the column clears the pocket, its notches and the edge
            r = params.FOOT_D / 2 + params.FOOT_SIDE_CLEAR
            assert plate.exterior.distance(Point(x, y)) >= r - 0.05, (x, y)
            assert pocket.distance(Point(x, y)) >= r - 0.05, (x, y)
            for n in notches:
                b = n.bounding_box()
                assert box(b.min.X, b.min.Y, b.max.X, b.max.Y).distance(Point(x, y)) >= r - 0.05, (x, y)
        else:
            assert plate.exterior.distance(Point(x, y)) >= need - 0.1, (x, y)


def test_foot_columns_flare_at_the_root(bottom):
    r = params.FOOT_D / 2
    for on_door, solid in ((False, bottom),):
        for top, n, _ in bottomcase._foot_axes("left", on_door):
            x, y = top[0], top[1]
            z = topcase.floor_z("left", x, y)
            u = np.array((0.0, 1.0, 0.0)); u -= n * (u @ n); u /= np.linalg.norm(u)       # across the axis, along Y
            for sign in (1, -1):
                p = top + n * ((z - 0.5 - top[2]) / n[2]) + sign * u * (r + 0.8)            # 0.5 below the floor, beside the column
                assert solid.is_inside(tuple(p)), (x, y, sign)
            p = top + n * ((z - params.FOOT_FLARE_L - 2.0 - top[2]) / n[2]) + u * (r + 0.8)   # below the flare: bare column
            assert not solid.is_inside(tuple(p)), (x, y)


def test_feet_and_pillars_do_not_poke_through_the_plate_faces(bottom):
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    ribs = bottomcase.ribs("left") + [batterydoor.plate_rim("left")]
    for top, n, _ in bottomcase._foot_axes("left", False):          # columns end at the plate's inner face, also on a ramp
        x, y = top[0], top[1]
        for a in angles:
            px, py = x + 0.9 * params.FOOT_D / 2 * np.cos(a), y + 0.9 * params.FOOT_D / 2 * np.sin(a)
            p = (px, py, topcase.floor_z("left", px, py, params.BOTTOM_WALL) + 0.3)
            if any(r.is_inside(p) for r in ribs):
                continue                                              # the +X edge rib and the battery rim, beside the foot next to the door
            assert not bottom.is_inside(p), (x, y, a)
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
    assert holder.bounding_box().min.Z == pytest.approx(z["nest"])                         # the holder sits on the nest floor
    for other in [top, holder] + load_boards("left") + list(core_board_placeholders("left").values()):
        assert vol(door & other) < 1e-3
    rigid = door
    for p in batterydoor.preloads("left"):
        assert vol(bottom & p) > 0.01                             # the bump and the fingers press the plate (relaxed in the model)
        rigid = rigid - p
    assert vol(bottom & rigid) < 1e-3                             # nothing else touches
    play = params.BATTERY_CEIL_GAP
    assert vol(bottom & (Pos(0, 0, play - 0.01) * rigid)) < 1e-3  # pressed up: free for the play
    assert vol(bottom & (Pos(0, 0, -0.05) * rigid)) > 0.5         # seated: the tabs sit on the ledges (flush)
    assert vol(bottom & (Pos(0, -0.5, 0) * rigid)) > 1.0          # it cannot slide further towards -Y
    for dx in (-0.5, 0.5):                                        # the pocket walls locate it along X ...
        assert vol(bottom & (Pos(dx, 0, 0) * rigid)) > 0.1
    for dx in (-params.BATTERY_POCKET_CLEAR + 0.05, params.BATTERY_POCKET_CLEAR - 0.05):
        assert vol(bottom & (Pos(dx, 0, 0) * rigid)) < 1e-3       # ... with BATTERY_POCKET_CLEAR each side
    keep = batterydoor._post_keep("left")                         # notched around a corner post's counterbore, if one is near
    if keep:
        x, y, r = keep
        assert door.distance(Pos(x, y, 0) * Cylinder(r, 100)) > params.BATTERY_POCKET_CLEAR - 0.01


def test_battery_door_tabs_each_side_ride_on_a_ledge_with_a_notch_at_the_unlocked_position(bottom, door):
    lay, s = batterydoor.layout("left"), params.BATTERY_SLIDE
    z0, z1 = batterydoor.tab_z("left")
    d = lay["door"]
    sides = [1 if t[0] + t[2] > d[0] + d[2] else -1 for t in lay["tabs"]]
    assert sides.count(1) == 3 and sides.count(-1) == 3
    for t, side in zip(lay["tabs"], sides):
        xm = t[2] - 0.5 if side > 0 else t[0] + 0.5                      # near the tab tip
        ym = (t[1] + t[3]) / 2
        assert door.is_inside((xm, ym, (z0 + z1) / 2))                    # the tab
        assert bottom.is_inside((xm, ym, z0 - 0.3))                       # the ledge right under it (locked, seated)
        assert bottom.is_inside((xm, ym, z1 + params.BATTERY_TAB_GAP + 0.5))   # the groove's roof over it
        assert not bottom.is_inside((xm, ym + s, z0 - 0.5))               # the notch (unlocked)
    assert min(t[2] - t[0] for t in lay["tabs"]) == pytest.approx(params.BATTERY_TAB_W + 0.5)
    assert d[2] - d[0] < lay["opening"][2] - lay["opening"][0] + 2 * params.BATTERY_DOOR_LAP_SIDE + 0.01


def test_battery_door_has_a_nest_that_locates_the_holder(door):
    from placeholders import battery_holder

    h, z = batterydoor.layout("left")["holder"], batterydoor.levels("left")
    c = params.BATTERY_NEST_CLEAR
    assert z["top"] - z["nest"] == pytest.approx(params.BATTERY_NEST_DEPTH)
    xm, ym = (h[0] + h[2]) / 2, (h[1] + h[3]) / 2
    zm = z["nest"] + params.BATTERY_NEST_DEPTH / 2                            # mid height of the nest wall
    assert door.is_inside((xm, ym, z["nest"] - 0.3)) and not door.is_inside((xm, ym, z["nest"] + 0.1))     # floor / open
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):                         # open inside the 0.3 gap
        x = (h[2] if dx > 0 else h[0]) + dx * (c - 0.1) if dx else xm
        y = (h[3] if dy > 0 else h[1]) + dy * (c - 0.1) if dy else ym
        assert not door.is_inside((x, y, zm)), (dx, dy)
    assert door.is_inside((h[0] - c - 0.2, ym, zm)) and door.is_inside((h[2] + c + 0.2, ym, zm))   # wall on the two long sides
    from build123d import Box

    wall = door & (Pos((h[0] + h[2]) / 2, (h[1] + h[3]) / 2, z["nest"] + 5.0) * Box(500, 500, 10))            # the nest's wall only
    assert wall.distance(battery_holder("left")) >= c - 0.01                    # the holder fits with the glue gap


def test_battery_door_pushed_towards_plus_y_drops_out_with_the_holder(bottom, top, door):
    from placeholders import battery_holder

    s = params.BATTERY_SLIDE
    rigid = door
    for p in batterydoor.preloads("left"):
        rigid = rigid - p
    for dz in (0.0, -0.5, -1.5, -3.0, -6.0, -12.0, -20.0):
        for part in [door if dz < -1.0 else rigid, battery_holder("left")]:   # the springs drag on the ceiling until clear
            moved = Pos(0, s, dz) * part
            assert vol(bottom & moved) < 1e-3 and vol(top & moved) < 1e-3, dz


def test_battery_door_locks_with_a_bump_in_a_dimple(door):
    (tx0, _, tx1, _), by = batterydoor._tongue("left")
    z = batterydoor.levels("left")
    cx = (tx0 + tx1) / 2
    assert door.is_inside((cx, by, z["top"] + params.BATTERY_BUMP_H / 2))                  # bump on the tongue
    assert not door.is_inside((tx0 - params.BATTERY_TONGUE_SLOT / 2, by, (z["top"] + z["bottom"]) / 2))   # slot beside it


def test_battery_door_is_preloaded_down_by_the_bump_and_two_springs(bottom, door):
    lay, z = batterydoor.layout("left"), batterydoor.levels("left")
    d = lay["door"]
    assert len(lay["springs"]) == 2
    assert {1 if r[0] + r[2] > d[0] + d[2] else -1 for r in lay["springs"]} == {1, -1}       # one on each X edge
    s = params.BATTERY_SLIDE
    for r in lay["springs"]:
        xm, tip = (r[0] + r[2]) / 2, r[1] + 0.3
        assert door.is_inside((xm, tip, z["ceiling"] + params.BATTERY_SPRING_PRELOAD - 0.3))   # the tip reaches into the ceiling
        assert not door.is_inside((xm, tip, z["top"] - 0.5))                                    # the relief under it
        assert r[0] > d[0] + params.BATTERY_DOOR_CHAMFER - 0.01 and r[2] < d[2] - params.BATTERY_DOOR_CHAMFER + 0.01
        assert r[2] < lay["opening"][0] or r[0] > lay["opening"][2]                              # under the plate, not the opening
        for groove, _ in batterydoor.grooves("left"):                    # never under a tab groove over the slide
            b = groove.bounding_box()
            if b.min.X < r[2] and r[0] < b.max.X:
                assert r[1] + s < b.min.Y or r[3] > b.max.Y and r[1] > b.max.Y, (r, b)
    # the bump stands above the dimple's roof: the tongue stays bent and pushes the door down
    (_, _, _, _), by = batterydoor._tongue("left")
    assert params.BATTERY_BUMP_H - params.BATTERY_CEIL_GAP > params.BATTERY_DIMPLE_D + 0.2


def test_thumb_ledge_sits_on_the_plate_under_the_thumb_pcb_edge(bottom):
    ledge = topcase.thumb_ledge("left")
    assert ledge.is_valid and ledge.volume > 10
    thumb = next(b for b in load_boards("left") if b.label == "thumb_2x3")
    assert vol(ledge & thumb) < 1e-6
    assert vol(ledge & bottom) < 1e-3                       # touches the plate's inner face, no overlap
    assert bottom.distance(ledge) < 1e-3


def test_battery_rim_is_bonded_to_the_plate_across_the_pocket_slit(bottom):
    """The rim above the pocket slit roofs the tab grooves: it needs a real section on every side, not a sliver."""
    x0, y0, x1, y1 = batterydoor.layout("left")["pocket"]
    z, g = batterydoor.levels("left"), params.BATTERY_POCKET_CLEAR
    za, zb = z["ceiling"] + 0.01, z["rim"] - 0.01
    sides = {"-X": (x0 - g, y0, x0, y1), "+X": (x1, y0, x1 + g, y1), "-Y": (x0, y0 - g, x1, y0), "+Y": (x0, y1, x1, y1 + g)}
    for name, r in sides.items():
        section = vol(bottom & batterydoor._box(r, za, zb)) / g           # material bridging the slit, mm2
        assert section > 40.0, f"{name}: rim is joined to the plate by only {section:.1f} mm2"


def test_battery_bump_dimple_leaves_a_wall_to_the_opening():
    """The dimple in the rim's -Y strip must not run into the opening edge (it used to leave 0.05 mm)."""
    lay = batterydoor.layout("left")
    (_, _, _, _), by = batterydoor._tongue("left")
    hw = batterydoor.dimple_half_width()
    assert lay["opening"][1] - (by + hw) >= 0.6
    assert by - hw - lay["door"][1] >= 0.6
