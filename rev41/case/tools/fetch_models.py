"""Download third-party 3D models into step/vendor/ (not tracked by git).

- koktoh/keyswitch_model (Kailh Choc V2 switch and hot-swap socket STEP), pinned to a commit. The repository carries no
  licence file, so the models are fetched, never committed.
"""

import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parents[1]
VENDOR = CASE_DIR / "step" / "vendor"

MODELS = {
    "choc_v2.step": ("https://github.com/koktoh/keyswitch_model",
                     "2b6bcfac0032f1547e27b18b9a897e065e544b37", "choc/v2/step/blue.step"),
    "hotswap_choc.step": ("https://github.com/koktoh/keyswitch_model",
                          "2b6bcfac0032f1547e27b18b9a897e065e544b37", "socket/step/choc.step"),
}


def _rmtree(path):
    """rmtree that also removes git's read-only object files on Windows."""
    def onerror(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=onerror)


def _git(repo, *args, tries=3):
    """git with retries: GitHub connections reset now and then."""
    for attempt in range(tries):
        try:
            return subprocess.run(["git", "-C", str(repo), *args], check=True)
        except subprocess.CalledProcessError:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


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
        try:
            for cmd in (["init", "-q"], ["fetch", "-q", "--depth", "1", url, rev],
                        ["checkout", "-q", "FETCH_HEAD", "--", path]):
                _git(tmp, *cmd)
        except subprocess.CalledProcessError:
            _rmtree(tmp)
            raise
        shutil.copy(tmp / path, dest)
        _rmtree(tmp)
        print(f"fetched {dest.relative_to(CASE_DIR)} ({url}@{rev[:7]})")


if __name__ == "__main__":
    sys.exit(main())
