"""Headless rendering of build123d shapes to PNG with pyvista (for agent feedback)."""

from pathlib import Path

import numpy as np
import pyvista as pv

COLORS = {"main_board": "seagreen", "core_board_e73": "royalblue", "thumb_cluster": "darkorange",
          "top_skin": "gold"}
VIEWS = {"iso": "iso", "top": "xy", "front": "xz", "side": "yz"}


def to_mesh(shape, tolerance=0.1):
    verts, tris = shape.tessellate(tolerance)
    if not verts:
        return None
    pts = np.array([[v.X, v.Y, v.Z] for v in verts])
    faces = np.hstack([[3, *t] for t in tris])
    return pv.PolyData(pts, faces)


def render(shapes, path, view="iso", section=None, size=(1200, 900), tolerance=0.1):
    """shapes: {name: Shape}. section: (axis, value) keeps the side below `value`, e.g. ("y", -60)."""
    pl = pv.Plotter(off_screen=True, window_size=size)
    for name, shape in shapes.items():
        mesh = to_mesh(shape, tolerance)
        if mesh is None:
            continue
        if section:
            axis, value = section
            normal = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
            origin = tuple(value if a == axis else 0 for a in "xyz")
            mesh = mesh.clip(normal=normal, origin=origin, invert=True)
        pl.add_mesh(mesh, color=COLORS.get(name, "lightgray"))
    pl.camera_position = VIEWS[view]
    pl.reset_camera()
    if view == "iso":
        pl.camera.azimuth = 180
    pl.show_axes()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pl.screenshot(str(path))
    pl.close()
