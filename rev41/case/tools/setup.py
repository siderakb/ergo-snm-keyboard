"""One-shot environment setup: check tools, then export the PCB STEP files."""

import shutil
import sys

import export_step
import fetch_models


def main():
    if not shutil.which("uv"):
        print("note: uv not on PATH (fine if you are already inside `uv run`)")
    cli = export_step.find_kicad_cli()
    print(f"kicad-cli: {cli} ({export_step.kicad_version(cli)})")
    sys.argv = [sys.argv[0]]
    export_step.main()
    fetch_models.main()


if __name__ == "__main__":
    main()
