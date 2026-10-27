"""Shared parameters for the case. All lengths in mm.

Values marked TODO are assumptions or unverified readings; see docs/status.md.
"""

import math

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
PLATE_T = 1.9          # integrated plate thickness (user-confirmed, 2026-10-23: 1.5 -> 1.9, JLC wall for 100-200 mm parts is 2.0)
PLATE_TOP_TO_PCB_TOP = 2.2    # plate top face to PCB top face = Choc V2 flange underside height (measured; drawing 5.30 - 3.10)
PLATE_PCB_GAP = round(PLATE_TOP_TO_PCB_TOP - PLATE_T, 3)   # 0.3: plate underside to PCB top (switch barbs top at 0.6: need relief)
PCB_T = 1.6            # actual board thickness (user-confirmed); KiCad STEP substrate is 1.51 (copper/mask not modelled)
STEP_PCB_T = 1.51       # KiCad STEP substrate thickness (copper/mask not modelled)
BOARD_GAP = 5.5        # main_board <-> core_board (2x10 1.27 mm header + socket)
CORE_MAX_PART_H = 5.5  # battery connector, tallest populated part on core board
CORE_J7_POPULATED = False  # J7 2x5 1.27 mm programming header: footprint only, not fitted
                           # (its STEP model is the tallest on the board: 4.0 mm above PCB)
BOTTOM_WALL = 2.0
BOTTOM_CLEAR = 0.5
# The bottom case is a plate inside the top case walls (the seam only shows from below); its outer face sits BOTTOM_RECESS
# up from the bottom edge of the walls, and PLATE_SIDE_CLEAR from their inner face in plan.
BOTTOM_RECESS = 0.8
PLATE_SIDE_CLEAR = 0.2      # TODO: set from a fit coupon (SLA)

# --- Slide switch (SK12D07) on core_board_e73 ---
SLIDE_SW_HANDLE = 7.0  # handle length (user-provided; confirm it is measured from the body top)
# Placeholder bodies for alignment (src/placeholders.py), sizes read from refs/drawings:
# SK12D07: body 8.6 x 4.5 in plan (footprint B.Fab), height 4.7 (drawing, TODO confirm), handle 2.0 wide x 2.7 high.
SLIDE_SW_BODY = (8.6, 4.5, 4.7)
SLIDE_SW_HANDLE_WH = (2.0, 2.7)
# HRO TYPE-C-31-M-12: 8.94 wide, 7.35 deep (front = footprint silk edge, +3.9 from the origin), 3.26 high above the board.
USB_C_BODY = (8.94, 7.35, 3.26)
USB_C_FRONT_V = 3.9
USB_C_FILLET = 1.2
# The core board has three connector slots at the same Y (KiCad x 136.525 / 152.4 / 168.275): USB-C J4, J9, J1 on F.Cu,
# and a switch SW1 / SW2 on B.Cu in the J4 / J1 slots. Population per hand (left: user, 2026-10-23).
# JST S2B-PH-SM4-TB side-entry battery header J8 (F.Cu, rotation 0): footprint fab box x +-3.95, v -3.2..4.4 (7.9 wide = B in the
# drawing; the opening faces +KiCad y), 5.5 high (drawing).
JST_PH_BODY = (7.9, 7.6, 5.5)
JST_PH_V_RANGE = (-3.2, 4.4)
# Right: the mirror image of the left population (the J1 slot carries a USB-C, the J4 slot the switch). TODO: confirm.
CORE_BATTERY_REFS = {"left": ("J8",), "right": ("J8",)}
CORE_USB_REFS = {"left": ("J4", "J9"), "right": ("J1", "J9")}
CORE_SWITCH_REFS = {"left": ("SW2",), "right": ("SW1",)}

# --- Switch (Kailh Choc V2) ---
KEY_PITCH = 19.05
SWITCH_BODY = 13.95    # lower housing, plate cutout nominal
SWITCH_FLANGE = 15.0
CUTOUT_COMP = 0.0      # TODO: cutout compensation, decide from coupon_choc_cutout

# Relief pockets in the skin underside over parts that stand taller than PLATE_PCB_GAP on the plate side
# (diodes, resistors, 2x10 socket pins): plan clearance around the part and clearance above its top.
RELIEF_XY_CLEAR = 0.3
RELIEF_Z_CLEAR = 0.2

# Light-guide slots: each LED gets a slot in the skin underside from the LED to the nearest key opening;
# the skin keeps LED_SLOT_SKIN above the slot.
LED_SLOT_SKIN = 0.8

# --- Fasteners (what is on hand; new sizes are allowed if really needed) ---
M2_HOLE = 2.2          # main_board / thumb PCB mounting holes: too small for M2.5, use them as locating pins only
# Screws: M2.5 x 6 and M2.5 x 4, head dia 5.5, head thickness 1.3.
SCREW_M25_LENGTHS = (6.0, 4.0)
SCREW_M25_HEAD_D = 5.5
SCREW_M25_HEAD_H = 1.3
SCREW_M25_CLEAR_D = 2.8        # TODO: through-hole for M2.5 in SLA (JLC holes shrink up to 0.3), set from coupon
# Nuts: knurled brass insert M2.5 x 2 x 3.5 (thread dia x height x outer dia), glued into the resin
# (refs/drawings/螺母參考.png is the vendor table; this size is the user's, not a row of it).
NUT_M25_THREAD = 2.5
NUT_M25_H = 2.0
NUT_M25_OD = 3.5
NUT_POCKET_CLEAR = 0.3         # TODO: diametral clearance for glue, set from coupon_nut_trap
# The PMW3610 breakout has M3 holes (3.2 mm); M2.5 screws pass through them.

# --- Battery (2x AA, series) ---
AA_D = 14.5
AA_L = 50.5

# --- Heights above the plate top surface, along the plate normal ---
SWITCH_STEM_TOP = 6.4     # Choc V2 drawing: stem top above the flange underside (= plate top)
STEM_ABOVE_HOUSING = 3.1  # Choc V2 drawing: stem top above the housing top
HOUSING_TOP = round(SWITCH_STEM_TOP - STEM_ABOVE_HOUSING, 3)   # 3.3
KEYCAP_H = 4.0            # TODO: low-profile keycap height, user estimate; set from the real keycap
KEYCAP_TOP = round(HOUSING_TOP + KEYCAP_H, 3)   # 7.3: keycap bottom rim assumed at the housing top

# --- Battery holder (off-the-shelf 2x AA) ---
# User gave "583 x 142 x 322"; read as 58.3 x 14.2 x 32.2 mm (value / 10). TODO: confirm units and
# which axis is length / height / width (14.2 is below an AA diameter of 14.5).
BATTERY_HOLDER = (58.3, 14.2, 32.2)
# Place (left-hand case frame): long side along Y, next to the core board, on the battery door (see BATTERY_* below).
# The right hand has the same holder and door, mirrored (see MIRROR_X).
HOTSWAP_SOCKET_PROTRUSION = 1.8   # Choc hot-swap socket sticks out of the PCB (total 3.05, rest is inside the board)
BATTERY_TOP_Z = -(HOTSWAP_SOCKET_PROTRUSION + 1.0)   # -2.8: the holder sits on the battery door (see below)
# The USB-C and slide-switch openings are cut in the top case wall (the walls run down to the bottom).
WALL_OPEN_CLEAR = 0.6      # opening grown around the USB-C receptacle (plug entry) and the slide-switch handle
# Tactile dots on the +Y wall's outer face: spherical caps (0.8 high = the JLC minimum emboss), centre 2.5 from the opening edge,
# lined up with the opening centre: below the middle USB-C (J9), beside the slide switch (on its outer side, at its mid height).
TACTILE_BUMP_D = 3.0
TACTILE_BUMP_H = 0.8
TACTILE_BUMP_GAP = 2.5
TACTILE_BUMPS = {"left": (("usb_J9", "below"), ("switch_SW2", "+x")), "right": (("usb_J9", "below"), ("switch_SW1", "-x"))}
SLIDE_SW_TRAVEL = 3.0      # handle travel between the two positions (TODO confirm from the SK12D07 drawing)
# Screw posts in the free corners between the PCB outlines and the case wall: Ø7.8 so the wall around the
# 3.8 mm nut pocket is 2.0 mm (JLC SLA wall for parts of 100-200 mm); the posts run down to the bottom plate, the nut
# sits in the post's lower end (glued in), the M2.5 x 6 screw comes up through the plate.
# Screw: head 1.3 in a SCREW_HEAD_SINK counterbore (0.7 proud, inside the 0.8 recess), 1.4 of plate, so the 4.7 shank
# reaches 3.3 into the post (nut pocket 2.5); POST_HOLE_LEN is the blind hole above the post end.
# The tilted thumb board (1.6 mm thick, hot-swap sockets 1.8 mm below it) reaches sideways past its plan
# corners by about (1.6 + 1.8) * sin(20 deg); the case plan outline grows by this around the thumb area.
THUMB_TILT_MARGIN = 0.7
BOSS_D = 7.8
SCREW_HEAD_SINK = 0.6
SCREW_HEAD_CBORE_D = SCREW_M25_HEAD_D + 0.5
POST_HOLE_LEN = 5.0
BOSS_PCB_CLEAR = 0.4
BOSS_COUNT = 3
# The right hand uses the left-hand posts, feet and floor mirrored (see MIRROR_X), so these are only given for the left.
# Hand-placed shifts of automatically chosen left-hand posts: {(x, y) of the automatic centre: (dx, dy)}. Matched within 1 mm.
# (57.6, -135.2): 1.0 towards +Y, away from the -Y wall (PCB side wall of the pocket drops to ~1.1 mm, the boss is trimmed there);
# (95.1, -141.7): 4.0 along +Y/-X, away from the wall and the thumb area (the whole boss still fits).
# (13.6, -40.2): 1.2 mm perpendicular to the slanted -X/+Y wall, so the head counterbore (Ø6.0) clears the plate edge by 0.9
# (PCB side wall of the nut pocket drops to ~1.1 mm, the boss is trimmed a little there).
BOSS_SHIFT_LEFT = {(57.6, -135.2): (0.0, 1.0), (95.1, -141.7): (-2.83, 2.83), (13.6, -40.2): (0.46, -1.11)}
# Extra left-hand post in the +Y/+X corner above the main board (user's red circle): about 95% of the boss fits, nut
# pocket walls ~1.5 mm on the PCB side and ~3.0 mm on the wall side.
BOSS_FIXED_LEFT = ((109.5, -38.6),)
# Right hand only, applied after mirroring: the post next to the crease moves 2.5 uphill along the thumb plate (to the 0.4 PCB
# clearance) so its lower end stays out of the trackball pod.
BOSS_SHIFT_RIGHT = {(111.53, -138.90): (2.165, 1.25)}
# The +Y edge of the left outline is pushed out at the main board's top-right corner by this much (the user's red line in
# the bottom view: nearly straight from the core board corner to the right edge), so the battery holder fits below it and
# the +Y screw post needs no trimming.
MAIN_TOP_RIGHT_GROW = 5.9
# Bottom plate outer face: BOTTOM_DEEP_Z under the battery holder and the core board (deep box from the +Y edge), a
# 45 degree ramp (BOTTOM_RAMP_ANGLE) up to BOTTOM_SHALLOW_Z (lowest hot-swap socket + clearance + plate) further on.
BOTTOM_RAMP_ANGLE = 45.0
BOTTOM_DEEP_MARGIN = 1.0     # the deep box runs this far past the battery door pocket (-X and -Y)
# Tenting: the whole half sits on the desk tilted about the Y axis, inner (+X, thumb) side up. The feet are columns on the
# bottom plate, perpendicular to the desk, ending FOOT_END_T above it (rubber pads in a recess); the lowest point of the
# case stays FOOT_MIN_CLEAR above the plane of the column ends.
TENT_ANGLE = 10.0          # TODO: user to set the tenting angle
FOOT_D = 8.0
FOOT_PAD_D = 6.0           # rubber feet: Ø6 x 2.0 (user), glued into a shallow recess at the column end
FOOT_PAD_T = 2.0
FOOT_PAD_RECESS = 0.5      # depth of the recess; the pad stands FOOT_PAD_T - FOOT_PAD_RECESS proud of the column end
FOOT_PAD_RECESS_CLEAR = 0.4   # recess diameter = pad + this (rim 0.8 on the Ø8 column)
FOOT_END_T = FOOT_PAD_T - FOOT_PAD_RECESS   # column end above the desk
FOOT_MIN_CLEAR = 1.0
FOOT_FLARE_R, FOOT_FLARE_L = 2.5, 3.75   # conical flare at the column root (radial x along the axis), clipped to the plate outline
# Ribs on the plate (SLA, so as thick as the walls, >= 1.5): a standing edge rim along the plate edge on the deep level
# (+Y and +X sides), and a bar across the strip between the battery opening and the pocket's +Y end (with a gap for the wire).
RIB_T = 1.5
EDGE_RIB_H = 4.0
STRIP_RIB_H = 5.0
STRIP_RIB_GAP = 1.0        # from the opening's +Y edge
STRIP_RIB_NOTCH_W = 12.0   # centred on the holder, lets the battery wire through
# Feet are at least FOOT_D / 2 + FOOT_FLARE_R + 1.0 = 7.5 from the plate edge and the door's edges, so the root flare is whole
# (user: move the three inward; 2.0 -> 4.5 for the -X pair, the door one 8 from the +Y edge, 2 inward).
FEET_LEFT = ((4.5, -124.0), (4.5, -55.0), (98.0, -48.5),                        # near the user's circles; (98, -48.5) on the battery door
             (123.36, -140.07))                                                 # thumb board hole H5 (user's arrow)
THUMB_FOOT = 3             # index in FEET_LEFT; the right hand puts this foot under the middle of the trackball pod instead
# Support pillars from the bottom plate through main-board mounting holes to the skin underside: a body up to
# PILLAR_TOP_Z (below the hot-swap sockets) and a pin through the Ø2.2 hole touching the skin.
# A short ledge on the thumb end wall, sitting on the bottom plate (the top case rests on the plate there). It reaches
# THUMB_LEDGE_W past the wall's inner face, under the thumb PCB edge: the small thumb board goes in tilted past it.
THUMB_LEDGE_W = 2.0
THUMB_LEDGE_LEN = 10.0
THUMB_LEDGE_GAP = 0.3                # to the thumb PCB underside
SUPPORT_HOLES = ("H2", "H3", "H4")
PILLAR_D = 5.0
PILLAR_TOP_Z = -(HOTSWAP_SOCKET_PROTRUSION + 0.5)
PIN_D = 1.8
# 45 degree shoulder at the pin root (up to PIN_SHOULDER wide), its top PIN_SHOULDER_UP above PILLAR_TOP_Z (0.2 under the
# sockets); where the plate's inner face is close under the sockets (H3, H4) it shrinks to the room that is left (0.3).
# The pin tip has a lead-in chamfer for entering the PCB hole from below.
PIN_SHOULDER = 1.0
PIN_SHOULDER_UP = 0.3
PIN_TIP_CHAMFER = 0.3
# Battery door (left): the 2xAA holder is glued onto a door (MJF PA12) that sits flush in a pocket of the bottom plate's
# outer face and hangs from three keyholes (two on the -X edge, one on the +X edge). Push it BATTERY_SLIDE towards +Y and
# it drops out with the holder (the holder wires stay connected, left long enough); push back towards -Y to lock, a bump
# on a sprung tongue at the door's -Y end clicks into a dimple. The plate around the opening is thickened inside.
# The holder's -X side is BATTERY_CORE_CLEAR past the core board; its +Y end leaves room for the slide, the opening
# clearance, the door's +Y lap, the pocket's travel and BATTERY_EDGE_MARGIN to the plate edge.
# Clearances follow the JLC guideline for moving parts (SLA 0.5, MJF 0.6 total; tolerance +-0.2 SLA / +-0.3 MJF, holes
# +-0.3 and usually small): 0.6 total play between the sliding faces; walls of positioning/snap features >= 1.5; the door
# (about 46 x 67, MJF) 2.0 thick. Still to be checked on a test print (keyhole + stud at 0.3 / 0.4 / 0.5 per side).
BATTERY_CORE_CLEAR = 0.5
BATTERY_SLIDE = 4.0
BATTERY_OPEN_CLEAR = 0.5       # holder -> opening edge
# The holder is glued into a shallow nest in the door's top face (user: simple alignment): the door is BATTERY_FLOOR_T thick under the
# holder and BATTERY_NEST_DEPTH higher round it (the nest edge is 0.3 off the holder's footprint for the glue), so the holder
# stays where it was and so does the floor; the plate's rim goes up by the same depth to keep the ceiling over the door 1.7 thick.
BATTERY_FLOOR_T = 2.0
BATTERY_NEST_DEPTH = 0.5
BATTERY_NEST_CLEAR = 0.3
BATTERY_DOOR_T = BATTERY_FLOOR_T + BATTERY_NEST_DEPTH
BATTERY_DOOR_LAP = 2.5         # door under the plate on the -Y edge
BATTERY_DOOR_LAP_KEY = 7.5     # on the X edges, where the keyholes are (1.5 of plate between big hole and opening)
BATTERY_DOOR_LAP_TOP = 1.0     # at the +Y end
BATTERY_EDGE_MARGIN = 1.0      # pocket -> plate edge at +Y
BATTERY_POCKET_CLEAR = 0.3     # pocket around the door
BATTERY_CEIL_GAP = 0.3         # pocket ceiling above the door (with KEY_HEAD_GAP: 0.6 vertical play)
BATTERY_RIM_H = 2.0 + BATTERY_NEST_DEPTH   # plate thickened on the inside around the opening (1.7 above the pocket)
BATTERY_POST_KEEP = 1.5        # plate kept around the corner post's counterbore (pocket and door notched there)
KEY_STUD_D, KEY_HEAD_D, KEY_HEAD_T = 2.5, 5.0, 1.5       # mushroom studs on the door
KEY_HOLE_D, KEY_SLOT_W = 6.0, 3.1                        # keyholes in the plate
KEY_HEAD_GAP = 0.3                                       # head above the rim
KEY_X_FLOAT = 0.6              # the +X keyhole is this much wider along X: only the -X pair locates the door in X
KEY_HEAD_CHAMFER, KEY_HOLE_CHAMFER, KEY_ROOT_FILLET = 0.5, 0.4, 0.3     # lead-ins and the stud root
BATTERY_DOOR_CHAMFER, BATTERY_POCKET_CHAMFER = 0.4, 0.3                  # door top edge, pocket edge in the floor
# Locking bump: the door has 0.6 vertical play, so the bump engages BATTERY_BUMP_H - 0.6 with the door hanging and
# BATTERY_BUMP_H with it pressed up (keyboard upside down, or on its feet); a 6 x 12 x 2.0 PA12 tongue bends that far
# with roughly 6-10 N (to be tuned on the test print).
BATTERY_TONGUE_W, BATTERY_TONGUE_L, BATTERY_TONGUE_SLOT = 6.0, 12.0, 1.0
BATTERY_BUMP_H, BATTERY_BUMP_W = 0.8, 2.0

# --- Trackball ---
BALL_D = 34.0
BEARING_BALL_D = 2.5
PMW3610_WORKING_DISTANCE = 2.4   # lens reference plane (lowest plane of the lens) to ball surface, PMW3610 spec
PMW3610_WD_TOL = 0.2             # +-; equal to the JLC SLA tolerance, so the sensor mount needs adjustment (shims)
# PMW3610 reference section (refs/drawings/pmw3610-lens.png), distances to the tracking (ball) surface.
# The sensor body sits on one PCB face ("sensor face"); the lens passes through a window in the board
# and sticks out of the other face. On the breakout (user-confirmed, same as the drawing) the IC is on
# F.Cu and the lens protrudes from B.Cu, so in the trackball the board is below the ball with its B.Cu
# toward the ball and F.Cu (IC, headers) facing down.
PMW3610_SENSOR_FACE_TO_SURFACE = 7.40   # PCB face carrying the sensor body
PMW3610_BODY_TOP_TO_SURFACE = 9.05      # top of the sensor body
PMW3610_DIE_TO_SURFACE = 7.83
PMW3610_BOARD_T = 1.60                  # drawing's PCB thickness (breakout board assumed the same)
PMW3610_LENS_FACE_TO_SURFACE = round(PMW3610_SENSOR_FACE_TO_SURFACE - PMW3610_BOARD_T, 3)   # 5.8: board face toward the ball
PMW3610_LENS_PROTRUSION = round(PMW3610_LENS_FACE_TO_SURFACE - PMW3610_WORKING_DISTANCE, 3)  # 3.4 beyond that face
PMW3610_BOARD = (23.5, 31.5)
PMW3610_HOLES = (17.5, 25.5)   # M3 x4
PMW3610_BOARD_CORNER_R = 3.0    # Edge.Cuts: the corners are arcs about the hole centres
PMW3610_BOARD_CENTRE = (150.0, 100.0)    # KiCad; the optical centre (U1 Cmts.User mark) is the board centre
PMW3610_IC_BOX = (16.2, 10.1, 1.65)      # package (pmw3610.png) along the board's long side, body below the sensor face
PMW3610_IC_REF_Y = 102.988               # U1 footprint origin (package centre), KiCad y: 2.988 off the optical centre
# U1 is through-hole: its pin ends and solder stick out of B.Cu, the face against the cup's seat. Pad centres (x0, y0, x1, y1),
# KiCad, from the footprint (pads 1-16), and the clearance around them (pad + solder fillet).
PMW3610_PIN_FIELD = (144.65, 96.82, 155.35, 110.17)
PMW3610_PIN_CLEAR = 1.0
PMW3610_LENS_BOX = (12.9, 8.1)           # lens outline (user), long side along the board's long side; 3.4 high (PMW3610_LENS_PROTRUSION)
PMW3610_FPC_REF_Y = 87.35                # J2 AFC01-S08FCA-00 (F.Cu, the face away from the ball), KiCad y
PMW3610_FPC_BOX = (10.0, 4.5, 2.0)       # AFC01-S08FCA-00 along the board edge x depth x height (user)

# --- Ball cup (right hand, separate part; R2) ---
# Frame: ball centre, u = uphill along the thumb plate (towards the crease), v = n x u (level), n = plate normal.
# The ball rests on three Ø2.5 steel balls; nothing holds it in (tip the keyboard over to take it out), so the cup is only the
# lower part: its rim is BALL_CUP_RIM below the centre, where the cup clears the thumb arm walls (inner face 18.98 from the
# axis) by 0.5 (user: lower rim, keep the outline). Above the rim the top case hole (1.25 per side) guides the ball.
BALL_CUP_GAP = 0.8                 # ball -> cup inner surface = steel ball protrusion
BALL_CUP_WALL = 1.5
BALL_CUP_RIM = 7.0                 # >= 5.2 for 0.5 to the walls; also under the pod neck: the plate's cavity (17.6, the plate edge
                                   # is 18.8 out) is narrower than the cup higher up, so the rim stays where the neck cone widens
BEARING_POLAR = 45.0               # steel balls this far from the bottom pole (azimuths 0 / 120 / 240 from +u); <= ~49 for the uphill boss
# A second set of seats at BEARING_POLAR_ALT, turned 60 deg (azimuths 60 / 180 / 300), to try the steeper angle on the same
# cup: fit the steel balls in one set or the other (user).
BEARING_POLAR_ALT = 49.0
BEARING_HOLE_D = 2.5               # TODO: press fit + glue, set from the test print
BEARING_BOSS_D = 5.5
# PMW3610 board under the cup: long side along u, FPC end uphill; B.Cu (lens) up against the cup's seat. The board is the
# middle of a sandwich: four M2.5 x 10 socket head screws come up through the pod floor, a standoff on it, the board and the
# shims into nuts in the cup (user: the cup shares the board's screws). Shims between seat and board set the working distance:
# the seat is SENSOR_SHIM_NOM nearer the ball than nominal, so shims can make up +-0.2 either way.
SENSOR_SHIM_NOM = 0.2
LENS_WINDOW_CLEAR = 0.5
CUP_BLOCK = (32.0, 25.0)           # seat block under the cup (u x v), carries the four board screws
CUP_BLOCK_TOP = -14.5              # block top below the ball centre (merges with the shell; keeps the screw holes blind)
SENSOR_SCREW_L, SENSOR_SCREW_HEAD_D, SENSOR_SCREW_HEAD_H = 10.0, 4.5, 2.5     # M2.5 x 10 socket head (user has them)
SENSOR_SCREW_CBORE_D = SENSOR_SCREW_HEAD_D + 0.5
SENSOR_SCREW_PROUD = 0.8           # head stands this far out of the pod's outer face (= BOTTOM_RECESS: no lower than the walls)
SENSOR_STANDOFF_D = 5.0            # on the pod floor under each board hole: carries the whole head, 1.1 wall around the hole
BALL_POD_CLEAR = 0.5               # cup -> pod wall (radial)
BALL_POD_FLOOR_CLEAR = 1.5         # lowest part (FPC connector) -> pod floor: standoffs 3.5 high; 0.5 -> 1.5 so the thumb cable (user)
                                   # fits under the sensor board (1.85 under the IC, 1.5 under the connector)
# The pod is a round cup of the bottom plate on the ball axis, hanging below the arm; the top case walls stay as on the left
# (user). Inner radius = the sensor board's rounded corner (hole centre 15.46 + R3 = 18.46 from the axis) + 0.5 (the board
# shifts up to 0.35 on its screws, + SLA / PCB tolerance), so its outer face is flush with the arm walls (20.96 vs 20.98).
# Just under the walls' bottom edge (BALL_POD_EDGE_CLEAR) it starts at the plate's edge and widens at 45 degrees. Its opening
# up into the arm keeps BALL_POD_TOP_CLEAR around the ball. The bottom edge is rounded, BALL_POD_FILLET on the inside (the
# board corners keep 0.5 to it), + BOTTOM_WALL outside.
# Cable windows (user, option A: the sensor FPC and the thumb_1x2 FPC both go through the pod): one on each side of the pod along
# the thumb arm (-u downhill towards the thumb board, +u uphill towards the main area), BALL_POD_FPC_W wide, from the neck's
# wall up through the arm's plate (they open the plate ring and the pod wall between radius R0 and R1 from the axis, leaving the
# pod wall >= 1.6 beside them) and down into the pod's wide part. The collar gets an arch on the +u side so the cable can leave
# the ball shaft; on the -u side the collar's slot at the thumb board is the way out.
BALL_POD_FPC_W = 8.0
BALL_POD_FPC_R0, BALL_POD_FPC_R1 = 16.8, 19.3
BALL_POD_FPC_BOTTOM = -9.5         # below the ball centre (the pod's cone is wider than R1 from about -7.4)
BALL_POD_FPC_ABOVE = 0.5           # window top above the plate's inner face
BALL_POD_FPC_ARCH_H = 2.0          # collar arch height above the plate's inner face
BALL_POD_BOARD_CLEAR = 0.5
BALL_POD_R_IN = round(math.hypot(PMW3610_HOLES[0] / 2, PMW3610_HOLES[1] / 2) + PMW3610_BOARD_CORNER_R + BALL_POD_BOARD_CLEAR, 3)
BALL_POD_FILLET = 2.5
BALL_POD_EDGE_CLEAR = 0.2
BALL_POD_TOP_CLEAR = 0.6

# --- Tenting ---
TENT_DEG = 0.0         # TODO

# --- Hand and board placement ---
# The top case is one printed piece: the flat main plate and the tilted thumb plate meet along a crease
# where the two top planes intersect. The rev4 thumb position put the thumb plane's highest plate edge
# 3.07 mm below the main plate top; lift the thumb boards (both hands, the planes mirror each other) so
# that edge reaches the main plate top (Z = PLATE_TOP_TO_PCB_TOP + PCB_T = 3.8).
THUMB_LIFT_Z = 3.07
# The whole thumb board slides this far toward the main board, horizontally along the
# (outward) fall line of the tilted plane at yaw 30 deg, so the crease moves with it (moves the crease
# and the thumb area closer to the main board; the keys keep their relative layout).
THUMB_SHIFT_IN = 3.0          # both hands (the right thumb board slides the mirror-image way)
_FALL = (math.cos(math.radians(30)), -math.sin(math.radians(30)))
# main_board is reversible: the right hand uses it F.Cu up (B.Cu parts such as the 29 SOD-323
# diodes hang below, away from the plate); the left hand uses it flipped, B.Cu up, so those
# parts sit under the plate (only PLATE_PCB_GAP = 0.3 mm clearance: relief pockets needed).
# Parts that exist on both faces (BTN1/BTN2, the 2x10 sockets, core board parts) are only
# fitted on the physically lower side.
HAND = "left"          # default hand for assembly / check / render

# Case frame (per hand): X, Y as in the main board STEP (Y = -KiCad y) for the right hand;
# Z up with the plate top at PLATE_TOP_TO_PCB_TOP + PCB_T above the main board's lower face.
# Each placement maps board STEP-local (X, Y, Z) to the case frame: p = R @ local + t.
# STEP-local: X = KiCad x, Y = -KiCad y, Z = 0 at the B.Cu face, PCB_T at the F.Cu face.
_PLATE_TOP = PLATE_TOP_TO_PCB_TOP + PCB_T      # 3.8
_FLIP_Y = ((-1, 0, 0), (0, 1, 0), (0, 0, -1))  # rotation 180 deg about Y
_IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
_MAIN_FLIP_X = 203.847   # left hand: X = 203.847 - local X (from rev4 FCStd fit)
# The right-hand case frame is the left one mirrored: X_right = MIRROR_X - X_left maps the main board, the core board
# and the thumb plate (the right 1x2 keys sit where the left 2x3 outer column is) onto each other. The right case reuses
# the left's outline, floor, posts, feet and battery door mirrored; only the thumb keys, the ball hole, the PCB reliefs
# and the wall openings are computed for the right boards.
MIRROR_X = _MAIN_FLIP_X

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
        # thumb_1x2: the right hand keeps the outer 1x2 keys of the thumb area; the inner 2x2 keys
        # become the trackball. rev4/case/ErgoSNM_case_right.FCStd keeps exactly the two key holes of
        # the left file that fit the 2x3 board's first column (SW1/SW5, X=127.0), so the 1x2 board
        # (SW4/SW8, X=187.452) sits where that column is: the right-hand image of the left
        # geometry (X mirrored, PCB unflipped, F.Cu toward the plate) shifted -60.452 along board X.
        "thumb_1x2": (
            ((0.813798, -0.5, -0.296198), (0.469846, 0.866025, -0.17101), (0.34202, 0.0, 0.939693)),
            (-140.3069 + THUMB_SHIFT_IN * _FALL[0], -168.5549 - THUMB_SHIFT_IN * _FALL[1], -84.3265 + THUMB_LIFT_Z),
        ),
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
            (295.4318 - THUMB_SHIFT_IN * _FALL[0], -140.4253 - THUMB_SHIFT_IN * _FALL[1], -62.1471 + THUMB_LIFT_Z),
        ),
        # core_board_e73 below (-Z) the flipped main_board, same 5.5 mm between facing faces; the core
        # board is symmetric, so it keeps the right-hand pose (flip about Y, USB edge at the back) and
        # only X shifts so the centres of its 2x10 headers meet the centres of the sockets. Align the
        # centres, not pin 1: the flipped main board reverses the row direction.
        "core_board_e73": (_FLIP_Y, (_MAIN_FLIP_X - _SOCKET_CX + _HEADER_CX, _CORE_DY, -BOARD_GAP)),
    },
}

# Right-hand trackball: the inner 2x2 keys of the thumb area (2x3 board SW2, SW3, SW6, SW7) are replaced
# by the ball, so the hole is centred on those four keys, on the plate-top plane of the right-hand case
# frame (it includes THUMB_LIFT_Z); plate normal (-0.2962, -0.171, 0.9397), tilt 20 deg. rev4's right
# FreeCAD file put the ball hole ~29 mm further towards the main board; that is not used.
# Hole diameter: rev4's hole bounding box is 35.3 x 36.5 (an ellipse from the tilt) -> ~36.5 for the
# 34 mm ball. Ball centre depth below the plate follows BALL_CENTER_DEPTH.
BALL_HOLE_CENTER_RIGHT = (round(77.232 + THUMB_SHIFT_IN * _FALL[0], 3), round(-141.945 - THUMB_SHIFT_IN * _FALL[1], 3), -3.8)
BALL_HOLE_D = 36.5
# Collar round the ball hole (user): a wall hangs from the skin along the plate normal down to the bottom plate, so the ball sits
# in a closed shaft. On the thumb PCB side the board edge is only 0.16 outside the hole edge, so the wall is cut back to the
# board outline + BALL_HOLE_PCB_CLEAR; whatever is left thinner than BALL_HOLE_WALL_MIN is dropped (a short open slot).
BALL_HOLE_CHAMFER = 0.8          # 45 degree chamfer on the hole's top edge (user), 0.8 = the JLC minimum emboss
BALL_HOLE_WALL = 2.0
BALL_HOLE_WALL_MIN = 1.0
BALL_HOLE_PCB_CLEAR = 0.3
# Ball top is level with the keycap tops; the centre is then BALL_D/2 - KEYCAP_TOP below the plate top.
BALL_RAISE = 5.0                # user: the whole trackball (ball, cup, sensor, pod) moves this far up along the plate normal
BALL_TOP = KEYCAP_TOP + BALL_RAISE
BALL_CENTER_DEPTH = round(BALL_D / 2 - BALL_TOP, 3)   # -0.3 (above the plate top) along the plate normal; 9.7 below with BALL_RAISE = 0

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
# (the FreeCAD file has the main plate top at Z=6.6; the plate top is 3.8 above the main
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
