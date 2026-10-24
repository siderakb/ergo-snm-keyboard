"""Detail diagrams (not to scale in section): option 2 (ledge above the plate) and option 3 (wall pads)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
from shapely.geometry import Polygon as SP

import outline
import params
import topcase
from geometry import outline_in_case
from placeholders import battery_holder

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
WALL_C, PLATE_C, PCB_C, BAT_C, CORE_C, SKIN_C = "#e0b030", "#9a9a9a", "#3d8f5a", "#7a3a8a", "#4466bb", "#f0d080"


def rect(ax, x, y, w, h, c, label=None, tc="k", fs=9):
    ax.add_patch(Rectangle((x, y), w, h, fc=c, ec="k", lw=1))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=tc)


def arrow(ax, p, q, c="#c33", lw=2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=c, lw=lw))


def dim(ax, p, q, text, off=(0, 0), fs=8, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<->", mutation_scale=9, color="k", lw=0.8))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, fontsize=fs, ha=ha, va="center")


def clean(ax, title, xl, yl):
    ax.set_title(title, fontsize=12, pad=8)
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.set_aspect("equal")
    ax.axis("off")


def poly(ax, g, **kw):
    ax.add_patch(Polygon(np.array(g.exterior.coords), closed=True, **kw))


out = outline.case_outline_polygon("left")
inner = out.buffer(-params.BOTTOM_WALL)
bb = battery_holder("left").bounding_box()
core = outline_in_case("core_board_e73", "left")
core = SP(max(core, key=lambda l: SP(l).area))


def plan_base(c, ledge=False):
    poly(c, out, fc=WALL_C, ec="k", lw=1)
    poly(c, inner, fc="#c9902a" if ledge else "white", ec="k", lw=0.8)
    if ledge:
        poly(c, inner.buffer(-2.5), fc="white", ec="#7a5510", lw=0.6)
    c.add_patch(Rectangle((bb.min.X, bb.min.Y), bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, fc=BAT_C, ec="k", alpha=0.8))
    poly(c, core, fc=CORE_C, ec="k", alpha=0.6)
    c.text((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, "電池盒", ha="center", color="w", fontsize=9)
    c.text(45, -60, "核心板", ha="center", color="w", fontsize=9)
    c.set_xlim(-12, 175)
    c.set_ylim(-182, -25)
    c.set_aspect("equal")
    c.axis("off")


# ======================================================================================================
# Option 2: ledge above the plate
# ======================================================================================================
fig, ax = plt.subplots(1, 3, figsize=(17, 7.5), gridspec_kw={"width_ratios": [1.25, 1, 1]})

a = ax[0]                                   # (a) section at the wall, z = 0 is the wall bottom edge
rect(a, 0, 0, 2, 22, WALL_C)
a.text(1, 20.5, "上蓋牆 2.0", ha="center", fontsize=9, rotation=90, va="top")
rect(a, 2, 6.0, 2.5, 2.0, WALL_C, "托邊\n厚 2.0", fs=8)
rect(a, 2.2, 4.0, 11, 2.0, PLATE_C, "下蓋底板 2.0", "w")
rect(a, 5.0, 6.0, 8.0, 6.5, BAT_C, "電池盒\n（固定在底板上）", "w", fs=8)
rect(a, 6, -1.4, 4.4, 1.4, "#444", "腳墊", "w", fs=8)
rect(a, 2.2, 20.0, 12.5, 2.0, SKIN_C, "蒙皮（鍵軸從這裡按下）", fs=8)
a.axhline(-1.4, color="#555", lw=1, ls=":")
a.text(14.6, -1.4, "桌面", fontsize=8, va="center", color="#555")
dim(a, (-1.0, 0), (-1.0, 4.0), "內縮\n約 0.8", off=(-1.6, 0))
a.text(2.1, 9.0, "間隙 0.2", fontsize=8, ha="left")
dim(a, (2.2, 3.3), (4.5, 3.3), "接觸寬 2.3", off=(0, -0.8))
arrow(a, (13.0, 19.0), (13.0, 15.5))
a.text(13.4, 17.2, "按鍵敲擊", fontsize=8, color="#c33", ha="left")
arrow(a, (3.2, 15.5), (3.2, 8.4), lw=1.6)
a.text(4.0, 14.3, "力走牆 → 托邊 → 底板\n→ 腳墊 → 桌面", fontsize=8, color="#c33")
clean(a, "(a) 牆邊剖面與受力路徑", (-3.5, 16.5), (-3.2, 23))

b = ax[1]                                   # (b) assembly from below
rect(b, 0, 14, 2, 10, WALL_C)
rect(b, 2, 18.0, 2.5, 2.0, WALL_C)
rect(b, 2.2, 16.0, 8, 2.0, PLATE_C, "底板（鎖緊後）", "w", fs=8)
rect(b, 5.5, 14.2, 1.6, 1.8, "#bbb", "頭", fs=6)
b.plot([6.3, 6.3], [14.0, 19.0], color="#888", lw=2)
b.text(10.6, 21.5, "② 頂到托邊後鎖螺絲\n（螺絲只負責拉緊）", fontsize=9, va="center")
rect(b, 0, 0, 2, 10, WALL_C)
rect(b, 2, 4.0, 2.5, 2.0, WALL_C)
rect(b, 2.2, -3.0, 8, 2.0, PLATE_C, "底板（從下方靠近）", "w", fs=8)
arrow(b, (6.2, -4.2), (6.2, -0.8))
b.text(7.0, -4.2, "往上推", fontsize=8, color="#c33", va="top")
b.text(10.6, 7.5, "① 底板進入牆內\n（和牆只有 0.2 間隙）", fontsize=9, va="center")
clean(b, "(b) 組裝：底板從下面往上放", (-1, 18), (-6, 25))

c = ax[2]                                   # (c) plan view
plan_base(c, ledge=True)
for x, y in topcase.post_positions("left"):
    c.add_patch(Circle((x, y), params.BOSS_D / 2, fc="#d33", ec="k", alpha=0.9))
c.text(-3, -100, "深色細框 = 托邊\n（沿牆內側一圈，\n只在螺絲柱處讓開）", fontsize=8, va="top")
c.set_title("(c) 俯視：托邊沿牆內側一圈", fontsize=12, pad=8)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.text(0.5, 0.005, "選項②：托邊放在底板上方（腳架與電池都在下蓋；剖面不按比例）", ha="center", fontsize=10, color="#555")
fig.savefig("docs/option2_detail.png", dpi=120)

# ======================================================================================================
# Option 3: wall pads
# ======================================================================================================
fig, ax = plt.subplots(1, 2, figsize=(15, 7.5), gridspec_kw={"width_ratios": [1.1, 1.2]})
a = ax[0]
rect(a, 0, 0, 2, 22, WALL_C)
a.text(1, 20.5, "上蓋牆 2.0", ha="center", fontsize=9, rotation=90, va="top")
rect(a, 2, 4.0, 6.0, 12.0, WALL_C)
a.text(6.6, 11.0, "貼牆柱\n（跟牆一起印）", ha="center", va="center", fontsize=8)
rect(a, 3.2, 3.9, 1.6, 3.2, "white", "螺\n母", fs=7)
rect(a, 3.6, 7.0, 0.8, 5.0, "white")
a.text(6.9, 9.5, "盲孔", fontsize=7, ha="center", va="center", rotation=90)
rect(a, 2.2, 2.0, 12.5, 2.0, PLATE_C, "下蓋底板 2.0", "w")
rect(a, 3.6, 2.0, 0.8, 2.1, "white")
arrow(a, (4.0, -2.3), (4.0, 6.3))
a.text(4.4, -2.3, "M2.5×6 螺絲", fontsize=8, color="#c33", va="top")
rect(a, 2, 16.0, 12.7, 1.6, PCB_C, "PCB 與熱插拔座（往下約 1.8）", "w", fs=8)
rect(a, 2.2, 20.0, 12.5, 2.0, SKIN_C, "蒙皮", fs=8)
a.plot([2, 14.7], [16.0, 16.0], color="#c33", lw=1, ls="--")
a.text(8.4, 14.8, "柱頂：熱插拔座下 0.5", fontsize=8, color="#c33", ha="left", va="top")
rect(a, 2.2, -2.0, 4.2, 2.0, "#444", "腳墊", "w", fs=8)
arrow(a, (11.5, 19.0), (11.5, 16.4))
a.text(11.9, 18.3, "按鍵敲擊\n走牆與柱子", fontsize=8, color="#c33", ha="left")
dim(a, (9.5, 4.0), (9.5, 16.0), "高約 10~13", off=(0.4, 0), ha="left")
clean(a, "(a) 穿過貼牆柱的剖面", (-2.2, 22), (-4.5, 23))

c = ax[1]
plan_base(c)
for x, y in [(-0.9, -60), (-0.9, -88), (72.0, -34.0), (10.0, -33.8), (110.2, -50)]:
    c.add_patch(Circle((x, y), 3.0, fc="#d33", ec="k", alpha=0.9))
for x, y in topcase.post_positions("left"):
    c.add_patch(Circle((x, y), params.BOSS_D / 2, fc="none", ec="#d33", ls="--", lw=1))
c.text(-8, -120, "紅點 = 貼牆柱位置（示意）\n在 PCB 下方，牆邊任何地方都可以放；\n右牆和電池盒中間只有約 4 mm，\n柱子要貼牆做窄一點。\n虛線圈 = 目前圓柱的位置", fontsize=8, va="top")
c.set_title("(b) 俯視：貼牆柱可以放的位置", fontsize=12, pad=8)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.text(0.5, 0.005, "選項③：貼牆柱（只在 PCB 下方；剖面不按比例）", ha="center", fontsize=10, color="#555")
fig.savefig("docs/option3_detail.png", dpi=120)
