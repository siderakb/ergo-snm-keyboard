"""Read board geometry (outline, mounting holes, switches) from .kicad_pcb files.

Coordinates are KiCad absolute coordinates (mm, +Y down), unchanged.
"""

import math
import re
from pathlib import Path

PCB_DIR = Path(__file__).resolve().parents[2] / "pcb"


def _tokens(text):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)


def _parse(tokens):
    pos = 0

    def read():
        nonlocal pos
        pos += 1
        node = []
        while tokens[pos] != ")":
            if tokens[pos] == "(":
                node.append(read())
            else:
                node.append(tokens[pos].strip('"'))
                pos += 1
        pos += 1
        return node

    return read()


def _children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def load_board(name):
    path = PCB_DIR / name / f"{name}.kicad_pcb"
    return _parse(_tokens(path.read_text(encoding="utf8")))


def footprints(board):
    """Yield (library_name, reference, x, y, rotation, layer)."""
    for fp in _children(board, "footprint"):
        at = _children(fp, "at")[0]
        ref = next((p[2] for p in _children(fp, "property") if p[1] == "Reference"), "?")
        layer = _children(fp, "layer")[0][1]
        rot = float(at[3]) if len(at) > 3 else 0.0
        yield fp[1].split(":")[-1], ref, float(at[1]), float(at[2]), rot, layer


def mounting_holes(board):
    return [(r, x, y) for lib, r, x, y, _, _ in footprints(board) if "MountingHole" in lib]


def switches(board):
    return [(r, x, y, rot) for lib, r, x, y, rot, _ in footprints(board) if lib.startswith("SW_MX_Kailh_Choc")]


def outline_bbox(board):
    pts = []
    for g in board:
        if not (isinstance(g, list) and g and g[0].startswith("gr_")):
            continue
        if ["layer", "Edge.Cuts"] not in g:
            continue
        for key in ("start", "end", "center", "mid"):
            pts += [(float(e[1]), float(e[2])) for e in _children(g, key)]
        for pts_node in _children(g, "pts"):
            pts += [(float(e[1]), float(e[2])) for e in _children(pts_node, "xy")]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _xy(node):
    return (float(node[1]), float(node[2]))


def _arc_points(start, mid, end, step_deg=5.0):
    """Points along the arc start -> mid -> end (circle through the three points), start and end included."""
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in ((x1, y1), (x2, y2), (x3, y3)))
    sweep = (a3 - a1) % (2 * math.pi)
    if (a2 - a1) % (2 * math.pi) > sweep:      # mid is not on the counter-clockwise way: go clockwise
        sweep -= 2 * math.pi
    n = max(2, int(abs(math.degrees(sweep)) / step_deg) + 1)
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


def _edge_segments(board):
    """Edge.Cuts lines/arcs as point lists, including those inside footprints (e.g. mouse bites),
    which are transformed to board coordinates (KiCad rotation: positive = counter-clockwise, y down)."""
    def seg(g, to_board):
        start, end = to_board(_xy(_children(g, "start")[0])), to_board(_xy(_children(g, "end")[0]))
        if g[0].endswith("line"):
            return [start, end]
        return _arc_points(start, to_board(_xy(_children(g, "mid")[0])), end)

    out = [seg(g, lambda p: p) for g in board
           if isinstance(g, list) and g and g[0] in ("gr_line", "gr_arc") and ["layer", "Edge.Cuts"] in g]
    for fp in _children(board, "footprint"):
        at = _children(fp, "at")[0]
        ox, oy, rot = float(at[1]), float(at[2]), math.radians(float(at[3]) if len(at) > 3 else 0.0)
        c, s = math.cos(rot), math.sin(rot)
        to_board = lambda p, ox=ox, oy=oy, c=c, s=s: (ox + p[0] * c + p[1] * s, oy - p[0] * s + p[1] * c)
        out += [seg(g, to_board) for g in fp
                if isinstance(g, list) and g and g[0] in ("fp_line", "fp_arc") and ["layer", "Edge.Cuts"] in g]
    return out


def outline_loops(board, tol=1e-3):
    """Closed Edge.Cuts loops as lists of (x, y) KiCad points (arcs discretised, no repeated end point)."""
    segs = _edge_segments(board)
    close = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1]) < tol
    loops = []
    while segs:
        loop = segs.pop(0)
        while not close(loop[0], loop[-1]):
            for i, seg in enumerate(segs):
                if close(loop[-1], seg[0]):
                    loop += seg[1:]
                elif close(loop[-1], seg[-1]):
                    loop += seg[::-1][1:]
                else:
                    continue
                segs.pop(i)
                break
            else:
                raise ValueError("Edge.Cuts outline is not closed")
        loops.append(loop[:-1])
    return loops


def outline_area(board):
    """Board area: the largest loop minus the other loops (cut-outs between panel tabs, slots)."""
    areas = sorted((abs(polygon_area(l)) for l in outline_loops(board)), reverse=True)
    return areas[0] - sum(areas[1:])


def polygon_area(loop):
    """Signed shoelace area (positive for counter-clockwise in a y-up frame)."""
    return 0.5 * sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(loop, loop[1:] + loop[:1]))


if __name__ == "__main__":
    for n in ("main_board", "thumb_cluster", "core_board_e73"):
        b = load_board(n)
        print(n, "bbox", outline_bbox(b))
        print("  holes", mounting_holes(b))
        print("  switches", len(switches(b)))
