# Forge API

Forge is the manufacturability engine inside STEX.

STEX is the application.

Forge is the engine.

## Purpose

Forge answers one question:

> Can this artwork become a manufacturable stencil?

## Current API

```python
from stex.core.forge import ForgeEngine

forge = ForgeEngine(
    threshold=180,
    min_island_area=40,
)

report = forge.inspect_file("my_stencil.png")

print(report.summary())
print(report.white_island_count)
print(report.is_cut_ready)
```

## Current Detection

Forge currently detects:

- Unsupported white islands

## Core Rule

White = stencil material that remains.  
Black = cutout / hole.

Therefore:

- White islands are critical failures.
- Black islands are acceptable.
- Every white region must connect to supported material.

## Report Model

Forge returns a `ForgeReport`.

A report contains:

- image width
- image height
- list of problems
- cut-ready status
- summary text

## Problem Model

Each problem contains:

- problem type
- severity
- label
- message
- bounding box
- centroid
- area in pixels
- metadata

## Future API Goals

Forge should eventually support:

```python
forge.find_white_islands()
forge.find_weak_spans()
forge.suggest_ribs()
forge.validate_export()
forge.inspect_multicolor_layers()
forge.export_svg()
```

## Design Principle

Forge should never alter artwork silently.

Forge inspects and suggests.

The artist decides.
