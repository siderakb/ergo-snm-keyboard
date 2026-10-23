"""Shared parameters for the case. All lengths in mm.

Values marked TODO are assumptions or unverified readings; see docs/status.md.
"""

# --- Process (JLC3DP) ---
SLA_TOL = 0.2          # JLC Black Resin, within 100 mm
MJF_TOL = 0.3          # PA12, within 100 mm
SLA_MIN_WALL = 0.8
MJF_MIN_WALL = 1.5
# Max part size (mm) and min wall by part size class, from the JLC3DP design guideline.
# Wall table: (part max dimension up to, min wall); larger parts use the last row.
MAX_SIZE = {"sla": (780, 780, 530), "mjf": (370, 276, 360)}
MIN_WALL_BY_SIZE = {
    "sla": ((5, 0.5), (10, 0.8), (50, 1.0), (100, 1.5), (200, 2.0)),
    "mjf": ((5, 1.0), (10, 1.2), (50, 1.5), (100, 2.0)),
}
SLA_CLEAR_ASSEMBLED = 0.2
SLA_CLEAR_MOVING = 0.5
MJF_CLEAR_ASSEMBLED = 0.3
MJF_CLEAR_MOVING = 0.6

# --- Stack-up (top to bottom) ---
PLATE_T = 1.5          # integrated plate thickness (user-confirmed)
PLATE_TOP_TO_PCB_TOP = 1.65   # plate outer face to PCB top face, includes the plate (user-confirmed)
PLATE_PCB_GAP = round(PLATE_TOP_TO_PCB_TOP - PLATE_T, 3)   # 0.15: plate underside to PCB top
PCB_T = 1.6            # actual board thickness (user-confirmed); KiCad STEP substrate is 1.51 (copper/mask not modelled)
STEP_PCB_T = 1.51       # KiCad STEP substrate thickness (copper/mask not modelled)
BOARD_GAP = 5.5        # main_board <-> core_board (2x10 1.27 mm header + socket)
CORE_MAX_PART_H = 5.5  # battery connector, tallest populated part on core board
CORE_J7_POPULATED = False  # J7 2x5 1.27 mm programming header: footprint only, not fitted
                           # (its STEP model is the tallest on the board: 4.0 mm above PCB)
BOTTOM_WALL = 2.0
BOTTOM_CLEAR = 0.5

# --- Slide switch (SK12D07) on core_board_e73 ---
SLIDE_SW_HANDLE = 7.0  # handle length (user-provided; confirm it is measured from the body top)

# --- Switch (Kailh Choc V2) ---
KEY_PITCH = 19.05
SWITCH_BODY = 13.95    # lower housing, plate cutout nominal
SWITCH_FLANGE = 15.0
CUTOUT_COMP = 0.0      # TODO: cutout compensation, decide from coupon_choc_cutout

# --- Fasteners ---
M2_HOLE = 2.2          # PCB mounting holes
M2_NUT_AF = 4.0
M2_NUT_T = 1.6
M3_NUT_AF = 5.5
M3_NUT_T = 2.4

# --- Battery (2x AA, series) ---
AA_D = 14.5
AA_L = 50.5

# --- Trackball ---
BALL_D = 34.0
BEARING_BALL_D = 2.5
PMW3610_BOARD = (23.5, 31.5)
PMW3610_HOLES = (17.5, 25.5)   # M3 x4

# --- Tenting ---
TENT_DEG = 0.0         # TODO

# --- Hand and board placement ---
# main_board is reversible: the right hand uses it F.Cu up (B.Cu parts such as the 29 SOD-323
# diodes hang below, away from the plate); the left hand uses it flipped, B.Cu up, so those
# parts sit under the plate (only PLATE_PCB_GAP clearance: relief pockets needed).
# Parts that exist on both faces (BTN1/BTN2, the 2x10 sockets, core board parts) are only
# fitted on the physically lower side.
HAND = "left"          # default hand for assembly / check / render

# Case frame (per hand): X, Y as in the main board STEP (Y = -KiCad y) for the right hand;
# Z up with the plate top at PLATE_TOP_TO_PCB_TOP + PCB_T above the main board's lower face.
# Each placement maps board STEP-local (X, Y, Z) to the case frame: p = R @ local + t.
# STEP-local: X = KiCad x, Y = -KiCad y, Z = 0 at the B.Cu face, PCB_T at the F.Cu face.
_PLATE_TOP = PLATE_TOP_TO_PCB_TOP + PCB_T      # 3.25
_FLIP_Y = ((-1, 0, 0), (0, 1, 0), (0, 0, -1))  # rotation 180 deg about Y
_IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
_MAIN_FLIP_X = 203.847   # left hand: X = 203.847 - local X (from rev4 FCStd fit)

# core_board_e73 (right hand): headers J2/J3 (KiCad 158.115, 74.295 / 93.345) must meet main_board
# sockets J1/J2 (153.05, 59.319 / 78.369). Mirror about x = 155.5825, shift 14.976 in Y,
# B.Cu faces up toward the main board.
_CORE_MIRROR_X = (158.115 + 153.05) / 2
# Centre X of the 2x10 socket (main_board) / header (core_board_e73) bodies, from the KiCad STEP.
_SOCKET_CX = 158.765
_HEADER_CX = 152.4
_CORE_DY = 74.295 - 59.319

PLACEMENTS = {
    "right": {
        "main_board": (_IDENT, (0.0, 0.0, 0.0)),
        "core_board_e73": (_FLIP_Y, (2 * _CORE_MIRROR_X, _CORE_DY, -BOARD_GAP)),
        # TODO: thumb_1x2 (right hand, next to the trackball) position is not defined yet.
    },
    "left": {
        "main_board": (_FLIP_Y, (_MAIN_FLIP_X, 0.0, PCB_T)),
        # thumb_2x3: from rev4/case/ErgoSNM_case_left.FCStd. Its tilted top face has its normal
        # tilted exactly 20.00 deg and 6 key holes that fit the thumb_cluster 2x3 switches (6/6,
        # 0.3 mm); the 29 flat-face holes fit main_board (28/29, X mirrored = flipped board).
        # FreeCAD -> case frame: Y = Y_fc - 60.023, Z = Z_fc - 6.6 + _PLATE_TOP.
        # Board is flipped (B.Cu toward the plate), so local +Z points down: tilt 160 deg, yaw 150 deg.
        "thumb_2x3": (
            ((-0.813798, 0.5, -0.296198), (0.469846, 0.866025, 0.17101), (0.34202, 0.0, -0.939693)),
            (295.5947, -140.5194, -62.1803),
        ),
        # core_board_e73 below (-Z) the flipped main_board, same 5.5 mm between facing faces; the core
        # board is symmetric, so it keeps the right-hand pose (flip about Y, USB edge at the back) and
        # only X shifts so the centres of its 2x10 headers meet the centres of the sockets. Align the
        # centres, not pin 1: the flipped main board reverses the row direction.
        "core_board_e73": (_FLIP_Y, (_MAIN_FLIP_X - _SOCKET_CX + _HEADER_CX, _CORE_DY, -BOARD_GAP)),
    },
}

# thumb_cluster.kicad_pcb is a panel of two boards joined by mouse bites; KiCad x range of each.
THUMB_BOARDS = {
    "thumb_2x3": {"hand": "left", "x_range": (116.84, 175.292), "switches": 6},
    "thumb_1x2": {"hand": "right", "x_range": (177.292, 197.612), "switches": 2},
}
# Which STEP/PCB file each placed board comes from.
BOARD_SOURCE = {"main_board": "main_board", "core_board_e73": "core_board_e73",
                "thumb_2x3": "thumb_cluster", "thumb_1x2": "thumb_cluster"}

# --- Intentional interference between case parts / PCB models ---
# {frozenset({"part_a", "part_b"}): reason}; anything not listed must have zero overlap.
ALLOWED_INTERFERENCE = {}

# --- thumb_cluster placement (tilted), in the case frame above ---
# Derived from rev4/case/ErgoSNM_case_left.FCStd: the top-case tilted face has normal tilted
# exactly 20.00 deg, and its 6 key holes fit the thumb_cluster switches (6/6, 0.3 mm), while the
# 29 flat-face holes fit main_board (28/29). FreeCAD frame -> case frame:
#   X = 203.847 - X_fc, Y = Y_fc - 60.023, Z = Z_fc - 6.6 + (PLATE_TOP_TO_PCB_TOP + PCB_T)
# (the FreeCAD file has the main plate top at Z=6.6; the plate top is 3.25 above the main
# board's B.Cu surface). Assumes the F.Cu-up orientation used for main_board here.
# Maps thumb STEP-local (X, -KiCad y, Z) -> case frame: p = R @ local + t.
THUMB_TILT_DEG = 20.0
THUMB_YAW_DEG = 30.0
THUMB_XF_R = (
    (0.8138, -0.5, -0.2962),
    (0.4698, 0.866, -0.171),
    (0.342, 0.0, 0.9397),
)
THUMB_XF_T = (-91.274, -140.246, -63.684)
