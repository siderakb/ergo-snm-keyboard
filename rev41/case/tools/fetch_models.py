"""Download third-party 3D models into step/vendor/ (not tracked by git).

- koktoh/keyswitch_model (Kailh Choc V2 STEP), pinned to a commit. The repository carries no
  licence file, so the models are fetched, never committed.
"""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parents[1]
VENDOR = CASE_DIR / "step" / "vendor"

MODELS = {
    "choc_v2.step": ("https://github.com/koktoh/keyswitch_model",
                     "2b6bcfac0032f1547e27b18b9a897e065e544b37", "choc/v2/step/blue.step"),
}


def _rmtree(path):
    """rmtree that also removes git's read-only object files on Windows."""
    def onerror(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=onerror)


def main():
    VENDOR.mkdir(parents=True, exist_ok=True)
    for out, (url, rev, path) in MODELS.items():
        dest = VENDOR / out
        if dest.exists():
            print(f"present {dest.relative_to(CASE_DIR)}")
            continue
        tmp = VENDOR / "_clone"
        if tmp.exists():
            _rmtree(tmp)
        tmp.mkdir()
        for cmd in (["init", "-q"], ["fetch", "-q", "--depth", "1", url, rev],
                    ["checkout", "-q", "FETCH_HEAD", "--", path]):
            subprocess.run(["git", "-C", str(tmp), *cmd], check=True)
        shutil.copy(tmp / path, dest)
        _rmtree(tmp)
        print(f"fetched {dest.relative_to(CASE_DIR)} ({url}@{rev[:7]})")


if __name__ == "__main__":
    sys.exit(main())
