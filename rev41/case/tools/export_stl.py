"""Export the printable case parts to build/stl/*.stl.

usage: export_stl.py [--hand left|right|both] [--ball-cup]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build123d import export_stl  # noqa: E402

import params  # noqa: E402
from bottomcase import battery_door, bottom_case  # noqa: E402
from topcase import top_case  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "stl"


def parts(hand, ball_cup):
    """Printable parts for `hand`: {file stem: Shape}."""
    out = {f"top_{hand}": top_case(hand)}
    out[f"bottom_{hand}"] = bottom_case(hand)
    out[f"battery_door_{hand}"] = battery_door(hand)
    if ball_cup and hand == "right":
        import trackball

        out["ball_cup_right"] = trackball.cup()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hand", default="both", choices=["left", "right", "both"])
    ap.add_argument("--ball-cup", action="store_true", help="also export the trackball cup (right hand)")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    hands = ["left", "right"] if args.hand == "both" else [args.hand]
    bad = 0
    for hand in hands:
        for stem, shape in parts(hand, args.ball_cup).items():
            path = OUT / f"{stem}.stl"
            export_stl(shape, str(path))
            solids = shape.solids()
            closed = shape.is_valid and len(solids) > 0
            bad += not closed
            print(f"{'ok ' if closed else 'BAD'} {path.name}: {len(solids)} solid(s), volume {shape.volume:.0f} mm3")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
