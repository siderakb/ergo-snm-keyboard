import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import params  # noqa: E402
import pcb_ref  # noqa: E402
import placeholders  # noqa: E402
from geometry import to_case  # noqa: E402


@pytest.fixture(scope="module")
def parts():
    return placeholders.core_board_placeholders("left")


def test_left_core_board_has_two_usb_and_one_switch(parts):
    assert sorted(parts) == ["battery_J8", "switch_SW2", "usb_J4", "usb_J9"]
    assert all(s.is_valid for s in parts.values())


def test_switch_is_the_leftmost_slot_and_usb_are_the_other_two(parts):
    xs = {k: (v.bounding_box().min.X + v.bounding_box().max.X) / 2 for k, v in parts.items()}
    assert xs["switch_SW2"] < xs["usb_J9"] < xs["usb_J4"]       # as seen in the top view (X to the right)


def test_usb_front_sticks_out_of_the_core_board_edge_and_switch_handle_further(parts):
    x0, y0, x1, y1 = pcb_ref.outline_bbox(pcb_ref.load_board("core_board_e73"))
    edge_y = to_case("core_board_e73", 0, y0, hand="left")[1]
    assert 0.5 < parts["usb_J4"].bounding_box().max.Y - edge_y < 3
    assert parts["switch_SW2"].bounding_box().max.Y - edge_y > params.SLIDE_SW_HANDLE - 1


def test_usb_hangs_below_the_core_board_and_switch_stands_above_it(parts):
    z_b = to_case("core_board_e73", 0, 0, 0.0, hand="left")[2]
    z_f = to_case("core_board_e73", 0, 0, params.PCB_T, hand="left")[2]
    assert parts["usb_J4"].bounding_box().max.Z <= z_f + 0.1                      # F.Cu face is the lower one
    assert parts["switch_SW2"].bounding_box().min.Z >= z_b - 0.1 and parts["switch_SW2"].bounding_box().max.Z < 0


def test_battery_connector_hangs_below_the_core_board_inside_its_outline(parts):
    bb = parts["battery_J8"].bounding_box()
    z_f = to_case("core_board_e73", 0, 0, params.PCB_T, hand="left")[2]
    assert bb.max.Z <= z_f + 0.1 and bb.min.Z == pytest.approx(z_f - params.JST_PH_BODY[2], abs=0.1)
    x0, y0, x1, y1 = pcb_ref.outline_bbox(pcb_ref.load_board("core_board_e73"))
    ys = [to_case("core_board_e73", 0, ky, hand="left")[1] for ky in (y0, y1)]
    assert min(ys) < bb.min.Y and bb.max.Y < max(ys)
