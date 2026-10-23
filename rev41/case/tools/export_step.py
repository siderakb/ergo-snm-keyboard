"""Export the PCB STEP files with kicad-cli into step/ (not tracked by git).

Skips boards whose .kicad_pcb hash and KiCad version match step/manifest.json.
Use --force to re-export everything.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parents[1]
PCB_DIR = CASE_DIR.parent / "pcb"
STEP_DIR = CASE_DIR / "step"
MANIFEST = STEP_DIR / "manifest.json"
BOARDS = ("main_board", "thumb_cluster", "core_board_e73")


def find_kicad_cli():
    found = shutil.which("kicad-cli")
    if found:
        return found
    for root in (Path("C:/Program Files/KiCad"), Path("/Applications/KiCad/KiCad.app/Contents/MacOS")):
        hits = sorted(root.glob("*/bin/kicad-cli*")) or sorted(root.glob("kicad-cli*"))
        if hits:
            return str(hits[-1])
    sys.exit("kicad-cli not found: install KiCad 10 or add it to PATH")


def kicad_version(cli):
    return subprocess.run([cli, "-v"], capture_output=True, text=True, check=True).stdout.strip()


def pcb_hash(board):
    return hashlib.sha256((PCB_DIR / board / f"{board}.kicad_pcb").read_bytes()).hexdigest()


def load_manifest():
    try:
        return json.loads(MANIFEST.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return {}


def stale_boards(version, manifest):
    return [
        b
        for b in BOARDS
        if not (STEP_DIR / f"{b}.step").exists()
        or manifest.get("kicad") != version
        or manifest.get("boards", {}).get(b, {}).get("sha256") != pcb_hash(b)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", action="store_true", help="only report staleness (exit 1 if stale)")
    args = ap.parse_args()

    cli = find_kicad_cli()
    version = kicad_version(cli)
    manifest = {} if args.force else load_manifest()
    todo = stale_boards(version, manifest)

    if args.check:
        print("STEP up to date" if not todo else f"STEP stale: {', '.join(todo)}")
        sys.exit(1 if todo else 0)
    if not todo:
        print(f"STEP up to date (KiCad {version})")
        return

    STEP_DIR.mkdir(exist_ok=True)
    boards = manifest.get("boards", {}) if manifest.get("kicad") == version else {}
    for b in todo:
        out = STEP_DIR / f"{b}.step"
        # --subst-models: use KiCad's stock model where a footprint has none.
        # --user-origin 0x0mm: keep KiCad coordinates (STEP Y is the negated KiCad y).
        subprocess.run(
            [cli, "pcb", "export", "step", "--output", str(out), "--subst-models",
             "--user-origin", "0x0mm", str(PCB_DIR / b / f"{b}.kicad_pcb")],
            check=True, capture_output=True,
        )
        boards[b] = {"sha256": pcb_hash(b)}
        print(f"exported {out.relative_to(CASE_DIR)}")
    MANIFEST.write_text(
        json.dumps({"kicad": version, "exported": datetime.now(timezone.utc).isoformat(),
                    "boards": boards}, indent=2),
        encoding="utf8",
    )


if __name__ == "__main__":
    main()
