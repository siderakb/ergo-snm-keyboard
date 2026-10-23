import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build123d import Box, Pos  # noqa: E402

import refmodels  # noqa: E402

MODEL = Path(__file__).resolve().parents[1] / "step" / "vendor" / "choc_v2.step"
pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="run tools/setup.py to fetch the model")


def _width(shape, z):
    sec = shape & (Pos(0, 0, z) * Box(40, 40, 0.02))
    return round(sec.bounding_box().size.X, 2) if sec.volume > 0 else None


def test_choc_model_matches_drawing_and_constants():
    c, m = refmodels.CHOC_V2, refmodels.choc_v2()
    bb = m.bounding_box()
    assert abs(bb.max.Z - c["stem_top"]) < 0.01 and abs(bb.min.Z + 3.3) < 0.01
    assert abs(c["stem_above_plate"] - 6.4) < 0.01                      # drawing: 6.40
    assert abs(c["flange_bottom"] - (5.30 - 3.10)) < 0.01             # drawing 5.30 - 3.10 = 2.2
    assert _width(m, 1.8) == pytest.approx(c["body_w"], abs=0.02)        # 13.95 through the plate
    assert _width(m, 2.5) == pytest.approx(15.0, abs=0.02)               # flange
    assert _width(m, c["flange_bottom"] - 0.05) < 14.0 < _width(m, c["flange_bottom"] + 0.05)
