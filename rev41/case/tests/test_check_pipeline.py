"""Run tools/check.py's part checks on deliberately bad parts; each defect must fail."""

import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE / "src"))
sys.path.insert(0, str(CASE / "tools"))

from build123d import Box, Pos  # noqa: E402

import check  # noqa: E402
from assembly import load_boards  # noqa: E402
from parts import Part  # noqa: E402


def _run(parts):
    check.results.clear()
    check.case_part_checks(load_boards("right"), {n: (Part(n, None, m), s) for n, (m, s) in parts.items()}, fast=False)
    return {r["name"]: r["ok"] for r in check.results}


def test_good_part_passes_and_defects_fail():
    # Far from every board: clean. thin: 0.5 mm plate. big: exceeds MJF max size.
    far = Pos(500, 500, 500)
    res = _run({
        "good": ("sla", far * Box(40, 40, 3)),
        "thin": ("sla", Pos(500, 600, 500) * Box(40, 40, 0.5)),
        "big": ("mjf", Pos(900, 500, 500) * Box(400, 10, 10)),
    })
    assert res["valid[good]"] and res["min_wall[good]"] and res["max_size[good]"]
    assert not res["min_wall[thin]"]
    assert not res["max_size[big]"]


def test_interference_with_part_and_pcb_detected():
    res = _run({
        "a": ("sla", Pos(500, 500, 500) * Box(20, 20, 3)),
        "b": ("sla", Pos(505, 500, 500) * Box(20, 20, 3)),          # overlaps a
        "c": ("sla", Pos(150, -90, 0.8) * Box(10, 10, 3)),           # inside main_board PCB
    })
    assert not res["interference[a x b]"]
    assert not res["interference[c x main_board]"]


def test_baseline_detects_change(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "BASELINE", tmp_path / "baseline.json")
    snap = check.snapshot({"p": Box(10, 10, 10)})
    check.check_baseline(snap, update=True)

    check.results.clear()
    check.check_baseline(snap, update=False)
    assert all(r["ok"] for r in check.results)

    check.results.clear()
    check.check_baseline(check.snapshot({"p": Box(10, 10, 11)}), update=False)
    assert not check.results[0]["ok"]
