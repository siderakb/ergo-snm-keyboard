"""Reference (not printed) models of purchased parts, loaded from step/vendor and step/."""

from pathlib import Path

from build123d import import_step

STEP_DIR = Path(__file__).resolve().parents[1] / "step"

# Kailh Choc V2 (koktoh/keyswitch_model, choc/v2/step/blue.step). Model frame: Z = 0 is the PCB top
# surface (housing sits on it, pins go down to -3.0), X/Y centred on the switch. Heights measured
# from the model and cross-checked with refs/drawings/choc_v2.png: flange underside above the PCB
# top = 5.30 - 3.10 = 2.2 (user-measured ~2.2); stem above the plate 6.40.
CHOC_V2 = {
    "barb_bottom": 0.1,       # retention barbs under the plate: 14.5-14.7 wide between Z 0.1 and 0.6
    "barb_top": 0.6,          # plate underside rests here (max)
    "body_w": 13.95,          # housing part that goes through the plate cutout (Z 1.4 .. 2.2)
    "flange_bottom": 2.2,     # 15.0 wide flange underside = plate top surface
    "flange_top": 3.0,
    "housing_top": 5.4,       # tapered upper housing (13.0 wide at the top)
    "stem_top": 8.6,          # stem 6.5 dia
    "pin_bottom": -3.0,
}
CHOC_V2["plate_slot"] = round(CHOC_V2["flange_bottom"] - CHOC_V2["barb_top"], 3)       # 1.6: room for the plate between barbs and flange
CHOC_V2["stem_above_plate"] = round(CHOC_V2["stem_top"] - CHOC_V2["flange_bottom"], 3)  # 6.4 (drawing: 6.40)


def choc_v2():
    return import_step(STEP_DIR / "vendor" / "choc_v2.step")
