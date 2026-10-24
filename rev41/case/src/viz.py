"""Headless rendering of build123d shapes to PNG with pyvista (for agent feedback)."""

from pathlib import Path

import numpy as np
import pyvista as pv

COLORS = {"main_board": "seagreen", "core_board_e73": "royalblue", "thumb_cluster": "darkorange",
          "top_skin": "gold", "top_walls": "orange", "top_posts": "red"}
COLORS.update({"usb": "silver", "switch": "magenta", "battery_holder": "purple", "battery": "cyan", "bottom_case": "lightgray", "battery_door": "royalblue"})
VIEWS = {"iso": "iso", "top": "xy", "front": "xz", "side": "yz", "bottom": "xy"}


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
            if mesh.n_points == 0:
                continue
        pl.add_mesh(mesh, color=next((c for k, c in COLORS.items() if name == k or name.startswith(k + "_")), "lightgray"))
    pl.camera_position = VIEWS[view]
    pl.reset_camera()
    if view == "iso":
        pl.camera.azimuth = 180
    if view == "bottom":                  # look up from below, X to the right
        pl.camera.elevation = 180
        pl.camera.up = (0, -1, 0)
    pl.show_axes()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pl.screenshot(str(path))
    pl.close()
