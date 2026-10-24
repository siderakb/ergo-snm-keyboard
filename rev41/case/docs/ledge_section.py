"""Schematic cross-section of the top case wall and the bottom plate: current vs. proposed ledge (not to scale in X)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
WALL, PLATE, CLEAR, EXT = 2.0, 2.0, 0.2, 8.0
WALL_H = 9.0


def panel(ax, title, recess, ledge):
    ax.set_title(title, fontsize=13, pad=12)
    # outside is to the left, inside to the right; z = 0 is the bottom edge of the wall
    ax.add_patch(Rectangle((0, 0), WALL, WALL_H, fc="#e0b030", ec="k"))
    ax.text(WALL / 2, WALL_H - 0.6, "上蓋牆\n2.0", ha="center", va="top", fontsize=9)
    if ledge:
        ax.add_patch(Rectangle((WALL, 0), ledge[0], ledge[1], fc="#e0b030", ec="k"))
        ax.text(WALL + ledge[0] / 2, ledge[1] / 2, "托邊", ha="center", va="center", fontsize=9)
    x0 = WALL + CLEAR
    ax.add_patch(Rectangle((x0, recess), EXT, PLATE, fc="#9a9a9a", ec="k"))
    ax.text(x0 + EXT / 2, recess + PLATE / 2, "下蓋底板 2.0", ha="center", va="center", fontsize=10, color="w")
    ax.annotate("", (-0.8, 0), (-0.8, recess), arrowprops=dict(arrowstyle="<->"))
    ax.text(-1.1, recess / 2, f"內縮 {recess:g}", ha="right", va="center", fontsize=9)
    ax.annotate("", (WALL, -0.9), (x0, -0.9), arrowprops=dict(arrowstyle="<->"))
    ax.text(WALL + CLEAR / 2, -2.2, "間隙 0.2", ha="center", va="top", fontsize=9)
    ax.text(-0.3, -0.5, "外側", ha="right", va="top", fontsize=9, color="#555")
    ax.text(WALL + EXT, -0.5, "內側", ha="right", va="top", fontsize=9, color="#555")
    ax.axhline(0, color="#c33", lw=1, ls="--")
    ax.text(WALL + EXT, 0.15, "牆底邊（從底下看到的接縫在這裡）", ha="right", va="bottom", fontsize=8, color="#c33")
    ax.set_xlim(-4.5, WALL + EXT + 0.5)
    ax.set_ylim(-4, WALL_H + 0.5)
    ax.set_aspect("equal")
    ax.axis("off")


fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
panel(axes[0], "目前：底板只靠螺絲，邊緣沒有支撐", 0.8, None)
panel(axes[1], "建議：牆內側加托邊，底板坐在上面", 2.0, (2.5, 2.0))
axes[1].annotate("", (WALL + 2.5, -0.9), (WALL, -0.9), arrowprops=dict(arrowstyle="<->"))
axes[1].text(WALL + 5.0, -1.4, "托邊寬 2.5 × 厚 2.0", ha="center", va="top", fontsize=9)
axes[1].text(WALL + 4.5, 5.6, "螺絲把底板往上拉，\n壓在托邊與固定柱上", ha="center", fontsize=9, color="#333")
fig.text(0.5, 0.02, "牆邊剖面示意（單位 mm，Z 向上，示意圖不按比例）", ha="center", fontsize=10, color="#555")
fig.tight_layout(rect=(0, 0.05, 1, 0.93))
fig.savefig("docs/ledge_section.png", dpi=150)
