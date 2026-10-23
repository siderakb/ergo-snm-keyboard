"""Simplified bodies of parts that have no STEP model, for alignment only (not printed, not checked).

Everything is built in the STEP-local frame of its board (X = KiCad x, Y = -KiCad y, Z from the B.Cu face) from the
footprint position in the .kicad_pcb, then placed with geometry.location().
"""

from build123d import Axis, Box, Pos, fillet

import params
import pcb_ref
from geometry import location


def _footprint(board, ref):
    """(x, y, rotation, layer) of footprint `ref` on `board` in KiCad coordinates."""
    for _, r, x, y, rot, layer in pcb_ref.footprints(pcb_ref.load_board(params.BOARD_SOURCE[board])):
        if r == ref:
            return x, y, rot, layer
    raise KeyError(ref)


def _box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def usb_c(ref, board="core_board_e73"):
    """USB-C receptacle on F.Cu, footprint rotated 180 deg: the opening faces -KiCad y (out of the board edge)."""
    x, y, rot, layer = _footprint(board, ref)
    assert layer == "F.Cu" and rot % 360 == 180
    w, d, h = params.USB_C_BODY
    v0, v1 = params.USB_C_FRONT_V - d, params.USB_C_FRONT_V      # footprint v: back .. front
    # board = (x - u, y - v); local Y = -board y = v - y
    body = _box(x - w / 2, x + w / 2, v0 - y, v1 - y, params.STEP_PCB_T, params.STEP_PCB_T + h)
    return fillet(body.edges().filter_by(Axis.Y), params.USB_C_FILLET)


def slide_switch(ref, board="core_board_e73"):
    """SK12D07 on B.Cu (rotated 180 deg, so mirrored): body below the board, handle out of the board edge."""
    x, y, rot, layer = _footprint(board, ref)
    assert layer == "B.Cu" and rot % 360 == 180
    L, W, H = params.SLIDE_SW_BODY
    hw, hh = params.SLIDE_SW_HANDLE_WH
    # B.Cu + rotation 180: board = (x + u, y - v), so local X = x + u and local Y = v - y
    body = _box(x - L / 2, x + L / 2, -W / 2 - y, W / 2 - y, -H, 0.0)
    v0, v1 = W / 2, W / 2 + params.SLIDE_SW_HANDLE
    handle = _box(x - hw, x, v0 - y, v1 - y, -H / 2 - hh / 2, -H / 2 + hh / 2)
    return body + handle


def battery_connector(ref, board="core_board_e73"):
    """JST S2B-PH-SM4-TB on F.Cu, rotation 0: board = (x + u, y + v), local Y = -board y; opening toward +KiCad y."""
    x, y, rot, layer = _footprint(board, ref)
    assert layer == "F.Cu" and rot % 360 == 0
    w, _, h = params.JST_PH_BODY
    v0, v1 = params.JST_PH_V_RANGE
    return _box(x - w / 2, x + w / 2, -(y + v1), -(y + v0), params.STEP_PCB_T, params.STEP_PCB_T + h)


def core_board_placeholders(hand):
    """{label: Shape} of the USB-C and switch placeholders on the core board, placed in the case frame."""
    out = {}
    loc = location("core_board_e73", hand)
    for ref in params.CORE_USB_REFS.get(hand, ()):
        out[f"usb_{ref}"] = loc * usb_c(ref)
    for ref in params.CORE_BATTERY_REFS.get(hand, ()):
        out[f"battery_{ref}"] = loc * battery_connector(ref)
    for ref in params.CORE_SWITCH_REFS.get(hand, ()):
        out[f"switch_{ref}"] = loc * slide_switch(ref)
    return out


def battery_holder(hand):
    """2x AA holder (BATTERY_HOLDER, read as length x height x width) in the case frame: long side along Y, centred in
    BATTERY_AREA_LEFT, top at BATTERY_TOP_Z_LEFT. Left hand only."""
    assert hand == "left"
    L, H, W = params.BATTERY_HOLDER
    a = params.BATTERY_AREA_LEFT
    cx, cy = sum(a["x"]) / 2, sum(a["y"]) / 2
    top = params.BATTERY_TOP_Z_LEFT
    return _box(cx - W / 2, cx + W / 2, cy - L / 2, cy + L / 2, top - H, top)
