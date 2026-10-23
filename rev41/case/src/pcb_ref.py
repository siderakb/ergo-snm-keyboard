"""Read board geometry (outline, mounting holes, switches) from .kicad_pcb files.

Coordinates are KiCad absolute coordinates (mm, +Y down), unchanged.
"""

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


if __name__ == "__main__":
    for n in ("main_board", "thumb_cluster", "core_board_e73"):
        b = load_board(n)
        print(n, "bbox", outline_bbox(b))
        print("  holes", mounting_holes(b))
        print("  switches", len(switches(b)))
