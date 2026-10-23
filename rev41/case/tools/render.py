"""Render the current assembly to build/renders/*.png.

usage: render.py [--hand left|right] [--view iso|top|front|side] [--section AXIS=VALUE] [--out NAME]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import viz  # noqa: E402
from assembly import load_boards, load_case_parts  # noqa: E402
from placeholders import core_board_placeholders  # noqa: E402
from bottomcase import bottom_case  # noqa: E402
from topcase import top_case_draft  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "renders"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", default="iso", choices=list(viz.VIEWS))
    ap.add_argument("--section", help="e.g. y=-60 (keep the side below the plane)")
    ap.add_argument("--hand", default=None, choices=["left", "right"])
    ap.add_argument("--draft", action="store_true", help="include the top case outline draft")
    ap.add_argument("--bottom", action="store_true", help="include the bottom case")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    section = None
    if args.section:
        axis, value = args.section.split("=")
        section = (axis, float(value))
    shapes = {b.label: b for b in load_boards(args.hand)}
    shapes.update({n: shape for n, (_, shape) in load_case_parts().items()})
    shapes.update(core_board_placeholders(args.hand))
    if args.draft:
        shapes.update(top_case_draft(args.hand))
    if args.bottom:
        shapes["bottom_case"] = bottom_case(args.hand)
    path = OUT / f"{args.out or args.view}.png"
    viz.render(shapes, path, args.view, section)
    print(path)


if __name__ == "__main__":
    main()
