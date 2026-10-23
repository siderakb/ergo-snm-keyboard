"""Geometry analysis used by tools/check.py: interference, wall thickness, process limits."""

import numpy as np
import vtk

import params
import viz


def _overlap(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.max.X <= bb.min.X or bb.max.X <= ba.min.X
                or ba.max.Y <= bb.min.Y or bb.max.Y <= ba.min.Y
                or ba.max.Z <= bb.min.Z or bb.max.Z <= ba.min.Z)


def interference_volume(a, b):
    """Volume (mm^3) of a & b. Both may be compounds; bounding boxes prefilter solid pairs."""
    total = 0.0
    for sa in a.solids():
        for sb in b.solids():
            if _overlap(sa, sb):
                total += (sa & sb).volume
    return total


def size_class_wall(material, max_dim):
    for limit, wall in params.MIN_WALL_BY_SIZE[material]:
        if max_dim <= limit:
            return wall
    return params.MIN_WALL_BY_SIZE[material][-1][1]


def within_max_size(shape, material):
    bb = shape.bounding_box()
    dims = sorted((bb.size.X, bb.size.Y, bb.size.Z), reverse=True)
    limit = sorted(params.MAX_SIZE[material], reverse=True)
    return all(d <= l for d, l in zip(dims, limit)), dims


def thin_spots(shape, min_wall, samples=4000, seed=0, tolerance=0.1):
    """Sample the surface and cast rays inward; return [(d, x, y, z)] where d < min_wall.

    Relies on the tessellation winding giving outward-facing normals.
    """
    mesh = viz.to_mesh(shape, tolerance)
    if mesh is None:
        return []
    mesh = mesh.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False)
    areas = mesh.compute_cell_sizes(length=False, area=True, volume=False)["Area"]
    centers = mesh.cell_centers().points
    normals = mesh.cell_data["Normals"]
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(areas), size=min(samples, len(areas)), replace=False, p=areas / areas.sum())

    loc = vtk.vtkStaticCellLocator()
    loc.SetDataSet(mesh)
    loc.BuildLocator()
    pts, ids = vtk.vtkPoints(), vtk.vtkIdList()
    spots = []
    for i in idx:
        p, n = centers[i], normals[i]
        p0, p1 = p - n * 1e-3, p - n * min_wall
        pts.Reset()
        ids.Reset()
        if loc.IntersectWithLine(p0, p1, 1e-6, pts, ids) and pts.GetNumberOfPoints():
            d = min(np.linalg.norm(np.array(pts.GetPoint(k)) - p) for k in range(pts.GetNumberOfPoints()))
            spots.append((float(d), *map(float, p)))
    return sorted(spots)
