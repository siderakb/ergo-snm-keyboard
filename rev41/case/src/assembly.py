"""Preview the PCB STEP files with OCP CAD Viewer (run in VS Code)."""

import sys
from pathlib import Path

from build123d import Box, Compound, Location, Plane, Pos, import_step
from ocp_vscode import show

import params
from geometry import placement
from topcase import top_case_draft
from parts import load_parts

STEP_DIR = Path(__file__).resolve().parents[1] / "step"


def _without(shape, prefix):
    """Top-level parts of a STEP tree, skipping those whose label starts with prefix.

    Only direct children are filtered: deeper leaves carry locations relative to their parent.
    """
    return [c for c in shape.children if not c.label.startswith(prefix)]


def _side(part):
    """"F" if the part body is on the F.Cu face of its board (STEP local Z above mid-plane), else "B".

    Uses the centre height: through-hole pins stick out the other side of the board.
    """
    bb = part.bounding_box()
    return "F" if (bb.min.Z + bb.max.Z) / 2 > params.STEP_PCB_T / 2 else "B"


def _fit_main_board(shape, hand):
    """main_board as fitted for `hand`: parts that only exist on the physically lower face.

    BTN1 (B.Cu) / BTN2 (F.Cu) are alternates, and the 2x10 sockets are solder-through: only the
    ones on the lower face are fitted. Right hand: lower = B.Cu. Left hand (flipped): lower = F.Cu,
    so the sockets move from B.Cu to the F.Cu face (mirror about the PCB mid-plane).
    """
    lower = "B" if hand == "right" else "F"
    mid = Plane.XY.offset(params.STEP_PCB_T / 2)
    out = []
    for c in shape.children:
        if c.label.startswith("SW_SPST_TL3342"):
            if _side(c) == lower:
                out.append(c)
        elif c.label.startswith("PinSocket_2x10"):
            out.append(c if _side(c) == lower else c.mirror(mid))
        else:
            out.append(c)
    return Compound(children=out)


def _location(R, t):
    return Location(Plane(origin=tuple(t), x_dir=tuple(R[:, 0]), z_dir=tuple(R[:, 2])))


def _panel_part(shape, x_range):
    """The part of a thumb_cluster panel STEP inside the KiCad x range (cut with a box)."""
    box = Pos((x_range[0] + x_range[1]) / 2, 0, 0) * Box(x_range[1] - x_range[0], 1000, 1000)
    pieces = [piece for solid in shape.solids() if (piece := solid & box) and piece.volume > 1e-6]
    return Compound(children=[sol for piece in pieces for sol in piece.solids()])


def load_boards(hand=None):
    """Placed boards for `hand`: [Shape] labelled by board name."""
    hand = hand or params.HAND
    cache, boards = {}, []
    for name in params.PLACEMENTS[hand]:
        src = params.BOARD_SOURCE[name]
        if src not in cache:
            cache[src] = import_step(STEP_DIR / f"{src}.step")
        shape = cache[src]
        if name == "main_board":
            shape = _fit_main_board(shape, hand)
        elif name in params.THUMB_BOARDS:
            shape = _panel_part(shape, params.THUMB_BOARDS[name]["x_range"])
        elif name == "core_board_e73" and not params.CORE_J7_POPULATED:
            shape = Compound(children=_without(shape, "PinHeader_2x05"))
        R, t = placement(name, hand)
        placed = _location(R, t) * shape
        placed.label = name
        boards.append(placed)
    return boards


def load_case_parts():
    """Registered case parts: {name: (Part, Shape)}."""
    return load_parts()


if __name__ == "__main__":
    hand = sys.argv[1] if len(sys.argv) > 1 else params.HAND
    case = [shape for _, shape in load_case_parts().values()]
    draft = [Compound(label=n, children=[s]) for n, s in top_case_draft(hand).items()]
    show(Compound(label=f"boards_{hand}", children=load_boards(hand)),
         Compound(label="top_case_draft", children=draft),
         Compound(label="case", children=case) if case else None,
         names=["boards", "top_case_draft", "case"], alphas=[1.0, 0.6, 1.0])
