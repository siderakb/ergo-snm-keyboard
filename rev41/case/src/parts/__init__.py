"""Case part registry.

Each module in this package builds one part and registers it:

    register("top_case", build_top_case, material="sla")

`build` takes no arguments and returns a build123d Shape in the case frame
(see CLAUDE.md). `material` is "sla" (JLC Black Resin) or "mjf" (PA12).
"""

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Callable

PARTS = {}


@dataclass
class Part:
    name: str
    build: Callable
    material: str


def register(name, build, material):
    if material not in ("sla", "mjf"):
        raise ValueError(f"unknown material {material!r}")
    PARTS[name] = Part(name, build, material)


def load_parts():
    """Import every part module and return {name: (Part, Shape)}."""
    for mod in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{mod.name}")
    out = {}
    for name, part in PARTS.items():
        shape = part.build()
        shape.label = name
        out[name] = (part, shape)
    return out
