"""Detail diagram of the 'feet right under the screw posts' option (not to scale in section)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
from shapely.geometry import MultiPoint, Point

import outline
import params
import topcase
from placeholders import battery_holder

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
WALL_C, PLATE_C, PCB_C, BAT_C, SKIN_C, FOOT_C = "#e0b030", "#9a9a9a", "#3d8f5a", "#7a3a8a", "#f0d080", "#333333"


def rect(ax, x, y, w, h, c, label=None, tc="k", fs=9, lw=1):
    ax.add_patch(Rectangle((x, y), w, h, fc=c, ec="k", lw=lw))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=tc)


def arrow(ax, p, q, c="#c33", lw=2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, color=c, lw=lw))


def dim(ax, p, q, text, off=(0, 0), fs=8, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<->", mutation_scale=9, color="k", lw=0.8))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, fontsize=fs, ha=ha, va="center")


def poly(ax, g, **kw):
    ax.add_patch(Polygon(np.array(g.exterior.coords), closed=True, **kw))


# ---- data for the plan view -------------------------------------------------------------------------
out = outline.case_outline_polygon("left")
posts = topcase.post_positions("left")
hull = MultiPoint(posts).convex_hull
keys = []
for cut in topcase.key_cutouts("left"):
    b = cut.bounding_box()
    keys.append(((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2))
outside = [k for k in keys if not hull.contains(Point(k))]
bb = battery_holder("left").bounding_box()
print("posts", [tuple(round(v, 1) for v in p) for p in posts])
print("keys", len(keys), "outside the post polygon", len(outside))

fig, ax = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw={"width_ratios": [1, 1.25]})

# ---- (a) section through one post --------------------------------------------------------------------
a = ax[0]
rect(a, 0, 0, 2, 26, WALL_C)
a.text(1, 24.5, "上蓋牆", ha="center", va="top", fontsize=9, rotation=90)
rect(a, 2.2, 24.0, 14.0, 2.0, SKIN_C, "蒙皮（鍵軸從這裡按下）", fs=8)
rect(a, 4.0, 4.0, 5.0, 20.0, WALL_C)                                  # post
a.text(8.5, 16.0, "柱\nØ7.8", ha="center", va="center", fontsize=8)
rect(a, 5.7, 4.0, 1.6, 3.0, "white", "螺母", fs=6)                    # nut pocket
rect(a, 6.1, 7.0, 0.8, 11.0, "white")                                   # blind hole
rect(a, 2.2, 2.0, 14.0, 2.0, PLATE_C, "下蓋底板 2.0", "w")
rect(a, 6.0, 2.0, 1.0, 2.1, "white")                                    # through hole
rect(a, 4.9, 1.6, 3.2, 0.8, "white")                                    # counterbore
rect(a, 5.0, 1.4, 3.0, 1.0, "#bbb")                                     # screw head
a.plot([6.5, 6.5], [1.5, 10.5], color="#888", lw=2)
rect(a, 3.0, -0.6, 7.0, 2.0, FOOT_C, "腳墊（蓋住螺絲頭）", "w", fs=8)
a.text(10.6, 0.4, "厚約 1.8–2.0\n貼在螺絲正下方", fontsize=8, va="center")
rect(a, 10.0, 3.0, 6.0, 0.0, "none")
rect(a, 11.0, 4.0, 5.2, 6.0, BAT_C, "電池盒", "w", fs=8)
rect(a, 2.2, 15.0, 1.6, 0.0, "none")
rect(a, 9.4, 22.0, 6.8, 1.6, PCB_C, "PCB", "w", fs=7)
a.plot([-1.5, 17.5], [-0.6, -0.6], color="#555", lw=1, ls=":")
a.text(17.6, -0.6, "桌面", fontsize=8, va="center", color="#555")
dim(a, (-0.8, -0.6), (-0.8, 0.0), "")
a.text(-1.2, 1.0, "牆底邊離桌面\n約 1.0–1.2", fontsize=8, ha="right", va="center")
arrow(a, (13.5, 22.0), (13.5, 20.0))
a.text(14.0, 21.2, "按鍵敲擊", fontsize=8, color="#c33")
arrow(a, (6.5, 20.5), (6.5, 5.0), lw=1.6)
arrow(a, (6.5, 3.0), (6.5, 0.9), lw=1.6)
a.text(9.6, 14.0, "力走 蒙皮 → 柱子\n→ 底板 → 腳墊 → 桌面\n（底板幾乎不彎）", fontsize=8, color="#c33", va="center")
a.set_xlim(-6, 22)
a.set_ylim(-3, 27.5)
a.set_aspect("equal")
a.axis("off")
a.set_title("(a) 穿過螺絲柱的剖面（腳墊在柱子正下方）", fontsize=12, pad=8)

# ---- (b) plan view: posts, feet, support polygon, keys ----------------------------------------------
c = ax[1]
poly(c, out, fc="#f3e3b0", ec="k", lw=1)
c.add_patch(Rectangle((bb.min.X, bb.min.Y), bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, fc=BAT_C, ec="k", alpha=0.35))
c.text((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, "電池盒", ha="center", color="k", fontsize=8)
poly(c, hull, fc="#cfe8cf", ec="#2a7a2a", lw=1.5, alpha=0.6)
for k in keys:
    ok = hull.contains(Point(k))
    c.add_patch(Rectangle((k[0] - 6.5, k[1] - 6.5), 13.0, 13.0, fc="none", ec="#2a7a2a" if ok else "#c33", lw=1.2 if ok else 1.8))
for x, y in posts:
    c.add_patch(Circle((x, y), 5.0, fc=FOOT_C, ec="k"))
    c.add_patch(Circle((x, y), 1.4, fc="white", ec="k"))
c.text(35, -148, f"鍵 {len(keys)} 個，{len(outside)} 個在腳墊圍成的範圍外（紅框）", fontsize=9, color="#c33", ha="center")
c.text(35, -156, "綠色區域 = 4 個腳墊圍成的支撐範圍", fontsize=9, color="#2a7a2a", ha="center")
c.text(35, -164, "黑圈 = 腳墊（位置同螺絲柱）", fontsize=9, ha="center")
c.set_xlim(-12, 175)
c.set_ylim(-182, -25)
c.set_aspect("equal")
c.axis("off")
c.set_title("(b) 俯視：4 個腳墊與支撐範圍", fontsize=12, pad=8)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.text(0.5, 0.005, "做法 2：腳墊貼在螺絲柱正下方（剖面不按比例）", ha="center", fontsize=10, color="#555")
fig.savefig("docs/option_feet_detail.png", dpi=120)
