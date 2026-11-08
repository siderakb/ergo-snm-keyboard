"""Battery door: a plate carrying the 2xAA holder (glued on), flush in a pocket of the bottom plate's outer face.

It hangs on slide tabs, three on each X edge, that ride in grooves cut sideways into the pocket's side walls, over a
ledge of the plate (a keyhole turned sideways). Pushed BATTERY_SLIDE towards +Y the tabs reach notches in the ledges and
the door drops out with the holder; the holder wires stay connected. Locked (towards -Y), a bump on a sprung tongue at
the door's -Y end sits in a dimple in the pocket ceiling. No foot stands on the door. Door and pocket are notched around
a corner screw post if one comes near. Rectangles are (x0, y0, x1, y1) in the case frame, the door in its locked
position. The right door is the left one mirrored.
"""

import functools

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, chamfer

import params
from geometry import mirror_x
from placeholders import battery_holder
from topcase import floor_profile

MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@functools.lru_cache(maxsize=None)
def layout(hand):
    """Plan rectangles of the holder, the opening in the plate, the door, the pocket and the locked slide tabs (each from
    0.5 inside the door edge to its tip)."""
    if hand == "right":
        left = layout("left")
        flip = lambda r: (mirror_x(r[2]), r[1], mirror_x(r[0]), r[3])
        return {k: flip(v) for k, v in left.items() if k != "tabs"} | {"tabs": tuple(flip(t) for t in left["tabs"])}
    bb = battery_holder(hand).bounding_box()
    s, c = params.BATTERY_SLIDE, params.BATTERY_OPEN_CLEAR
    holder = (bb.min.X, bb.min.Y, bb.max.X, bb.max.Y)
    opening = (holder[0] - c, holder[1] - c, holder[2] + c, holder[3] + s + c)      # the holder passes when pushed +Y
    k = params.BATTERY_DOOR_LAP_SIDE
    door = (opening[0] - k, opening[1] - params.BATTERY_DOOR_LAP, opening[2] + k, opening[3] + params.BATTERY_DOOR_LAP_TOP)
    pocket = (door[0], door[1], door[2], door[3] + s)
    w, n = params.BATTERY_TAB_W, params.BATTERY_TAB_L
    tabs = tuple((door[0] - w, door[1] + dy, door[0] + 0.5, door[1] + dy + n) for dy in params.BATTERY_TABS_LEFT["-X"]) \
        + tuple((door[2] - 0.5, door[1] + dy, door[2] + w, door[1] + dy + n) for dy in params.BATTERY_TABS_LEFT["+X"])
    return {"holder": holder, "opening": opening, "door": door, "pocket": pocket, "tabs": tabs}


def levels(hand):
    """Z of the door underside (flush with the floor), the nest floor (the holder's bottom), the door top, the pocket ceiling and
    the rim top."""
    z = floor_profile(hand)["z_deep"]
    top = z + params.BATTERY_DOOR_T
    return {"bottom": z, "nest": z + params.BATTERY_FLOOR_T, "top": top, "ceiling": top + params.BATTERY_CEIL_GAP,
            "rim": z + params.BOTTOM_WALL + params.BATTERY_RIM_H}


def tab_z(hand):
    """(z0, z1) of the slide tabs (door locked, hanging free)."""
    top = levels(hand)["top"]
    return top + params.BATTERY_TAB_RISE - params.BATTERY_TAB_T, top + params.BATTERY_TAB_RISE


def _tab_side(hand, tab):
    """+1 for a tab on the door's +X edge, -1 on its -X edge."""
    d = layout(hand)["door"]
    return 1 if tab[0] + tab[2] > d[0] + d[2] else -1


def grooves(hand):
    """[(groove, notch)] per tab: the groove in the pocket's side wall the tab slides in (from 0.6 inside the door edge, over
    the locked and the unlocked positions) and the notch through the ledge below it at the unlocked position."""
    d, s = layout(hand)["door"], params.BATTERY_SLIDE
    g, tip = params.BATTERY_TAB_GAP, params.BATTERY_TAB_TIP_CLEAR
    z0, z1 = tab_z(hand)
    out = []
    for t in layout(hand)["tabs"]:
        if _tab_side(hand, t) > 0:
            x0, x1 = d[2] - 0.6, t[2] + tip
        else:
            x0, x1 = t[0] - tip, d[0] + 0.6
        groove = _box((x0, t[1] - g, x1, t[3] + s + g), z0 - g, z1 + g)
        notch = _box((x0, t[1] + s - g, x1, t[3] + s + g), levels(hand)["bottom"] - 5.0, z0 - g + 0.01)
        out.append((groove, notch))
    return out


def on_door(hand, x, y):
    x0, y0, x1, y1 = layout(hand)["door"]
    return x0 < x < x1 and y0 < y < y1


def _box(r, z0, z1, grow=0.0):
    x0, y0, x1, y1 = r
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0 + 2 * grow, y1 - y0 + 2 * grow, z1 - z0, align=MIN)


def _post_keep(hand):
    """(x, y, r) of the plate kept around the corner post's counterbore, or None if it is far from the pocket."""
    import topcase

    x0, y0, x1, y1 = layout(hand)["pocket"]
    r = params.SCREW_HEAD_CBORE_D / 2 + params.BATTERY_POST_KEEP
    for x, y in topcase.post_positions(hand):
        if x0 - r < x < x1 + r and y0 - r < y < y1 + r:
            return x, y, r
    return None


def post_notch(hand):
    """Solid the door must stay out of: the corner post's keep-out circle swept over the whole slide (a stadium from
    y - SLIDE to y), or None."""
    keep = _post_keep(hand)
    if not keep:
        return None
    x, y, r = keep
    r += params.BATTERY_POCKET_CLEAR
    s, z = params.BATTERY_SLIDE, levels(hand)
    z0, h = z["bottom"] - 20.0, z["top"] + 1.0 - (z["bottom"] - 20.0)
    return (Pos(x, y, z0) * Cylinder(r, h, align=MIN) + Pos(x, y - s, z0) * Cylinder(r, h, align=MIN)
            + _box((x - r, y - s, x + r, y), z0, z0 + h))


def nest(hand):
    """The shallow nest for the glued holder: its footprint plus BATTERY_NEST_CLEAR, from the nest floor up through the door's top."""
    h, z = layout(hand)["holder"], levels(hand)
    return _box(h, z["nest"], z["top"] + 1.0, grow=params.BATTERY_NEST_CLEAR)


def _tongue(hand):
    """(x0, y0, x1, y1) of the sprung tongue at the door's -Y end and the y of its bump."""
    d = layout(hand)["door"]
    cx, w = (d[0] + d[2]) / 2, params.BATTERY_TONGUE_W
    return (cx - w / 2, d[1], cx + w / 2, d[1] + params.BATTERY_TONGUE_L), d[1] + params.BATTERY_DOOR_LAP / 2


def door(hand):
    """The door with its slide tabs and the locking tongue; the holder is glued on."""
    lay, z = layout(hand), levels(hand)
    body = _box(lay["door"], z["bottom"], z["top"])
    body = chamfer(body.edges().group_by(Axis.Z)[-1], params.BATTERY_DOOR_CHAMFER)
    notch = post_notch(hand)
    if notch:
        body = body - notch
    body = body - nest(hand)
    z0, z1 = tab_z(hand)
    for t in lay["tabs"]:
        body = body + _box(t, z0, z1)
    (tx0, ty0, tx1, ty1), by = _tongue(hand)
    w = params.BATTERY_TONGUE_SLOT
    for x in (tx0 - w, tx1):                                     # two slots from the -Y edge free the tongue
        body = body - _box((x, ty0 - 1.0, x + w, ty1), z["bottom"] - 1.0, z["top"] + 1.0)
    bump = Pos((tx0 + tx1) / 2, by, z["top"]) * Rot(0, 90, 0) * Cylinder(params.BATTERY_BUMP_W / 2, tx1 - tx0 - 1.0)
    body = body + (bump & _box((tx0, by - 1.0, tx1, by + 1.0), z["top"] - 0.1, z["top"] + params.BATTERY_BUMP_H))
    hx = (lay["holder"][0] + lay["holder"][2]) / 2
    for i in range(4):                                           # thumb grip grooves in the underside, behind the tongue
        y = ty1 + 2.0 + i * 2.0
        body = body - _box((hx - 8.0, y, hx + 8.0, y + 1.0), z["bottom"] - 1.0, z["bottom"] + 0.5)
    return body


def plate_rim(hand):
    """Plan region of the thickening: the pocket plus BATTERY_RIM_LAP all round, and past the side grooves on the X edges (it
    bridges the pocket's slit, roofs the grooves and sits on the plate), less the opening. Posts are cut out and the plate
    outline is clipped in bottomcase."""
    lay, z = layout(hand), levels(hand)
    inner = z["bottom"] + params.BOTTOM_WALL
    x0, y0, x1, y1 = lay["pocket"]
    lap, gx = params.BATTERY_RIM_LAP, params.BATTERY_TAB_W + params.BATTERY_TAB_TIP_CLEAR
    return _box((x0 - gx - lap, y0 - lap, x1 + gx + lap, y1 + lap), inner - 0.1, z["rim"]) - _box(lay["opening"], inner - 1.0, z["rim"] + 1.0)


def plate_cuts(hand):
    """Pocket (edge chamfered, notched around a corner post), opening, the tabs' side grooves and ledge notches, and the dimple."""
    lay, z = layout(hand), levels(hand)
    g, c = params.BATTERY_POCKET_CLEAR, params.BATTERY_POCKET_CHAMFER
    pocket = _box(lay["pocket"], z["bottom"] - 5.0, z["ceiling"], grow=g)
    edge = _box(lay["pocket"], z["bottom"] - 5.0, z["bottom"] + c, grow=g + c)
    edge = chamfer(edge.edges().group_by(Axis.Z)[-1], c - 0.01)
    keep = _post_keep(hand)
    if keep:
        x, y, r = keep
        post = Pos(x, y, z["bottom"] - 10.0) * Cylinder(r, 20.0, align=MIN)
        pocket, edge = pocket - post, edge - post
    cuts = [pocket, edge, _box(lay["opening"], z["bottom"] - 5.0, z["rim"] + 5.0)]
    for groove, notch in grooves(hand):
        cuts += [groove, notch]
    (tx0, _, tx1, _), by = _tongue(hand)
    cuts.append(_box((tx0 - 0.5, by - params.BATTERY_BUMP_W / 2 - 0.2, tx1 + 0.5, by + params.BATTERY_BUMP_W / 2 + 0.2),
                     z["ceiling"] - 0.2, z["ceiling"] + params.BATTERY_BUMP_H + 0.1))      # room for the door pressed up
    return cuts
