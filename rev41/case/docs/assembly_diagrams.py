"""Schematic diagrams (not to scale): bottom-plate support options and the USB-C insertion into the +Y wall."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
WALL_C, PLATE_C, PCB_C, PART_C = "#e0b030", "#9a9a9a", "#3d8f5a", "#4466bb"


def rect(ax, x, y, w, h, c, label=None, tc="k", fs=9):
    ax.add_patch(Rectangle((x, y), w, h, fc=c, ec="k", lw=1))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=tc)


def arrow(ax, p, q, c="#c33", lw=2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=c, lw=lw))


def clean(ax, title, xl, yl):
    ax.set_title(title, fontsize=12, pad=8)
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")


# ---- 1. three ways to hold the bottom plate -----------------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(15, 6))

# A: bayonet tabs (plan view, looking up at the bottom)
a = ax[0]
rect(a, 0, 0, 2, 14, WALL_C, "上蓋牆")
for y in (1.5, 8.5):
    rect(a, 2, y, 2.5, 3.5, WALL_C, "托邊\n小塊", fs=8)
a.add_patch(Polygon([(2.2, 0.2), (2.2, 5.5), (4.7, 5.5), (4.7, 8.0), (2.2, 8.0), (2.2, 13.8), (9, 13.8), (9, 0.2)], fc=PLATE_C, ec="k", alpha=0.85))
a.text(6.2, 7, "底板\n（邊緣有缺口）", ha="center", va="center", fontsize=9, color="w")
arrow(a, (4.8, 6.7), (4.8, 3.9)); a.text(5.3, 3.6, "裝入後\n橫向滑 3 mm", fontsize=8, color="#c33", va="top")
clean(a, "① 卡口：托邊只做小塊，\n底板缺口對位，推進去再滑", (-0.5, 9.5), (-3, 15))

# B: ledge above the plate
b = ax[1]
rect(b, 0, 0, 2, 12, WALL_C, "上蓋牆")
rect(b, 2, 4.5, 2.5, 2, WALL_C, "托邊\n（在上方）", fs=8)
rect(b, 2.2, 2.5, 7, 2, PLATE_C, "底板 2.0", "w")
arrow(b, (6, 0.2), (6, 2.3)); b.text(6.2, 0.2, "螺絲拉住", fontsize=8, color="#c33", va="top")
arrow(b, (7.5, 7.5), (7.5, 5.0), c="#555", lw=1.5); b.text(7.8, 7.7, "重量掛在螺絲上\n托邊只管往上定位", fontsize=8, color="#333")
clean(b, "② 托邊放在底板上方：\n底板從下面推上去頂住", (-0.5, 10), (-2, 13))

# C: wall pad under the PCB
c = ax[2]
rect(c, 0, 0, 2, 14, WALL_C, "上蓋牆")
rect(c, 2, 0.2, 4, 7.0, WALL_C, "貼牆柱\n（從牆長出）", fs=8)
rect(c, 2.0, 7.0, 7.5, 0.5, PCB_C)
c.text(9.7, 7.25, "PCB 高度\n（柱子到這裡為止）", fontsize=8, va="center", color=PCB_C)
rect(c, 3.4, 5.4, 1.2, 1.8, "white", "螺母", fs=7)
rect(c, 2.2, -2.0, 7.2, 2.0, PLATE_C, "底板 2.0", "w")
arrow(c, (4.0, -3.6), (4.0, 0.6)); c.text(4.3, -3.6, "螺絲", fontsize=8, color="#c33", va="top")
clean(c, "③ 貼牆柱：PCB 下方的牆內側加厚，\n螺絲固定點可以放在牆邊任何位置", (-0.5, 12.5), (-6, 15))
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.text(0.5, 0.01, "底板固定方式比較（剖面／俯視示意，不按比例）", ha="center", fontsize=10, color="#555")
fig.savefig("docs/plate_options.png", dpi=130)

# ---- 2. USB-C going through the +Y wall -----------------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(15, 5.5))
titles = ["① 垂直往上裝：USB 前端撞到孔下方的牆", "② 斜著把前端插進孔", "③ 前端到位後轉平、放到定位"]
for k, a in enumerate(ax):
    rect(a, 10, 0, 2, 14, WALL_C)
    rect(a, 10, 7.2, 2, 3.0, "white")                      # opening
    a.text(11, 8.7, "開孔", ha="center", va="center", fontsize=8)
    a.text(11, 3.5, "牆", ha="center", va="center", fontsize=9)
    rect(a, -2, 10, 10, 1.5, "#ddd")                       # skin
    a.text(-1.5, 11.9, "蒙皮", fontsize=8)
    clean(a, titles[k], (-3, 13), (-3.5, 14.5))
pcb = lambda a, dx, dy, ang: None


def board(a, dx, dy, ang):
    """main/core board + USB front, rotated by ang about the USB front tip, then shifted."""
    t = np.radians(ang); R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    tip = np.array([9.2, 8.7])
    place = lambda pts: [tuple(tip + R @ (np.array(p) - tip) + np.array([dx, dy])) for p in pts]
    a.add_patch(Polygon(place([(-1.5, 8.0), (8.4, 8.0), (8.4, 8.8), (-1.5, 8.8)]), fc=PCB_C, ec="k"))
    a.add_patch(Polygon(place([(5.6, 8.8), (9.2, 8.8), (9.2, 11.0), (5.6, 11.0)]) if False else place([(5.6, 7.2), (9.2, 7.2), (9.2, 8.0), (5.6, 8.0)]), fc=PART_C, ec="k"))
    return place


board(ax[0], 0, -3.5, 0)
ax[0].plot([9.2, 9.2], [-0.5, 8.2], "r:", lw=1); arrow(ax[0], (4, -4.5), (4, -2.0)); ax[0].text(6.5, 2.0, "USB 前端比板邊多 1.36，\n已進入牆的範圍", fontsize=8, color="#c33")
ax[0].text(10.4, -1.2, "✕", fontsize=22, color="#c33", ha="center")
board(ax[1], 0.3, -0.4, 14)
arrow(ax[1], (3, 3.5), (6, 4.8))
ax[1].text(0.0, 2.0, "前端先進孔，\n板子斜 10–15°", fontsize=8, color="#c33")
board(ax[2], 0, 0, 0)
ax[2].text(2.0, 3.2, "再轉平，放回\n螺絲柱／軸體定位", fontsize=8, color="#c33")
fig.tight_layout(rect=(0, 0.04, 1, 0.93))
fig.text(0.5, 0.01, "核心板／USB 與 +Y 牆開孔的組裝示意（側視，+Y 向右；不按比例）", ha="center", fontsize=10, color="#555")
fig.savefig("docs/usb_insertion.png", dpi=130)
