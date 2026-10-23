"""Run all design checks; exit 1 on failure. Writes build/report.json.

usage: check.py [--fast] [--update-baseline]
  --fast             skip wall-thickness and interference checks
  --update-baseline  store current part volumes/bboxes in docs/baseline.json
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE / "src"))
sys.path.insert(0, str(CASE / "tools"))

import export_step  # noqa: E402
import params  # noqa: E402
import analysis  # noqa: E402
import pcb_ref  # noqa: E402
from assembly import load_boards, load_case_parts  # noqa: E402
from build123d import import_step  # noqa: E402
from geometry import local_to_case, to_case  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))


BASELINE = CASE / "docs" / "baseline.json"
BASELINE_TOL = 0.001   # relative


def snapshot(shapes):
    out = {}
    for name, sh in shapes.items():
        bb = sh.bounding_box()
        out[name] = {"volume": round(sh.volume, 3),
                     "bbox": [round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)]}
    return out


def check_baseline(snap, update):
    if update:
        BASELINE.write_text(json.dumps(snap, indent=2), encoding="utf8")
        print(f"baseline updated: {BASELINE}")
        return
    if not BASELINE.exists():
        print("[SKIP] baseline: none yet (run with --update-baseline once parts are stable)")
        return
    base = json.loads(BASELINE.read_text(encoding="utf8"))
    for name in sorted(set(base) | set(snap)):
        if name not in snap or name not in base:
            check(f"baseline[{name}]", False, "part added or removed; update the baseline if intended")
            continue
        dv = abs(snap[name]["volume"] - base[name]["volume"]) / max(base[name]["volume"], 1e-9)
        db = max(abs(a - b) for a, b in zip(snap[name]["bbox"], base[name]["bbox"]))
        check(f"baseline[{name}]", dv <= BASELINE_TOL and db <= 0.01,
              f"volume {dv * 100:.3f}% off, bbox off by {db:.3f} mm")


def case_part_checks(boards, parts, fast):
    for name, (part, shape) in parts.items():
        ok = shape.is_valid and len(shape.solids()) >= 1
        check(f"valid[{name}]", ok, f"{len(shape.solids())} solids")
        fits, dims = analysis.within_max_size(shape, part.material)
        check(f"max_size[{name}]", fits, "x".join(f"{d:.1f}" for d in dims) + f" ({part.material})")
        if fast:
            continue
        wall = analysis.size_class_wall(part.material, dims[0])
        spots = analysis.thin_spots(shape, wall)
        where = "; ".join(f"{d:.2f} mm at ({x:.1f}, {y:.1f}, {z:.1f})" for d, x, y, z in spots[:3])
        check(f"min_wall[{name}]", not spots, f"limit {wall} mm, {len(spots)} thin samples" + (f": {where}" if spots else ""))

    if fast:
        return
    for (na, (_, a)), (nb, (_, b)) in itertools.combinations(parts.items(), 2):
        v = analysis.interference_volume(a, b)
        if v > 1e-3 and frozenset({na, nb}) not in params.ALLOWED_INTERFERENCE:
            check(f"interference[{na} x {nb}]", False, f"{v:.2f} mm^3")
    for na, (_, a) in parts.items():
        for pcb in boards:
            v = analysis.interference_volume(a, pcb)
            if v > 1e-3 and frozenset({na, pcb.label}) not in params.ALLOWED_INTERFERENCE:
                check(f"interference[{na} x {pcb.label}]", False, f"{v:.2f} mm^3")
    check("interference_done", True, f"{len(parts)} parts vs each other and {len(boards)} boards")


def to_local_case(board, X, Y, hand):
    """STEP-local (X, Y) on the board -> case-frame (X, Y)."""
    x, y, _ = local_to_case(board, X, Y, 0.0, hand=hand)
    return x, y


def check_boards(hand):
    """Placement sanity for every board placed for `hand`."""
    for b in load_boards(hand):
        tag = f"{b.label}@{hand}"
        bad = [s for s in b.solids() if not s.is_valid]
        check(f"valid_solids[{tag}]", not bad, f"{len(b.solids())} solids, {len(bad)} invalid")
        # Catches parts that lost their location (e.g. when rebuilding a STEP tree).
        src = params.BOARD_SOURCE[b.label]
        x0, y0, x1, y1 = pcb_ref.outline_bbox(pcb_ref.load_board(src))
        if b.label in params.THUMB_BOARDS:
            x0, x1 = params.THUMB_BOARDS[b.label]["x_range"]
        corners = [to_case(b.label, x, y, hand=hand) for x in (x0, x1) for y in (y0, y1)]
        xs, ys = [c[0] for c in corners], [c[1] for c in corners]
        slack = 8.0 if b.label in params.THUMB_BOARDS else 5.0   # tilt moves parts sideways
        bb = b.bounding_box()
        inside = (bb.min.X >= min(xs) - slack and bb.max.X <= max(xs) + slack
                  and bb.min.Y >= min(ys) - slack and bb.max.Y <= max(ys) + slack)
        check(f"within_outline[{tag}]", inside, f"bbox x {bb.min.X:.1f}..{bb.max.X:.1f} y {bb.min.Y:.1f}..{bb.max.Y:.1f}")

    if params.PLACEMENTS[hand].get("core_board_e73"):
        # 2x10 header/socket body centres must coincide after placement (sorted by Y).
        def centres(board, prefix):
            step = import_step(CASE / "step" / f"{params.BOARD_SOURCE[board]}.step")
            out = []
            for c in step.children:
                if c.label.startswith(prefix):
                    bb = c.bounding_box()
                    out.append(to_local_case(board, (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, hand))
            return sorted(out, key=lambda p: p[1])

        for i, (c, m) in enumerate(zip(centres("core_board_e73", "PinHeader_2x10"), centres("main_board", "PinSocket_2x10"))):
            err = max(abs(c[0] - m[0]), abs(c[1] - m[1]))
            check(f"header_align[row {i + 1}@{hand}]", err < 0.05, f"error {err:.3f} mm")
        def z_faces(board):
            return [to_case(board, 0, 0, z, hand=hand)[2] for z in (0.0, params.PCB_T)]
        gap = min(z_faces("main_board")) - max(z_faces("core_board_e73"))   # main lower face to core upper face
        check(f"board_gap@{hand}", abs(gap - params.BOARD_GAP) < 1e-6, f"{gap:.3f} mm (expected {params.BOARD_GAP})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--hand", choices=["left", "right"], help="hand whose boards the case parts are checked against")
    args = ap.parse_args()
    stale = export_step.stale_boards(export_step.kicad_version(export_step.find_kicad_cli()),
                                     export_step.load_manifest())
    check("step_fresh", not stale, ", ".join(stale) or "up to date (run tools/setup.py)")
    if stale:
        sys.exit(1)

    for hand in ("left", "right"):
        check_boards(hand)

    step_t = params.STEP_PCB_T
    check("pcb_thickness", abs(params.PCB_T - step_t) <= 0.1, f"PCB_T {params.PCB_T} vs STEP substrate {step_t}")

    hand = args.hand or params.HAND
    boards = load_boards(hand)
    parts = load_case_parts()
    case_part_checks(boards, parts, args.fast)
    check_baseline(snapshot({n: sh for n, (_, sh) in parts.items()}), args.update_baseline)

    CASE.joinpath("build").mkdir(exist_ok=True)
    CASE.joinpath("build", "report.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
