# STEX Stencil Rules

## Core Rule

White represents material that remains.

Black represents cutout space.

Therefore:

- White islands are failures.
- Black islands are acceptable.
- Every white region should connect back to the outside material or another supported white region.

## Rule 1: No Unsupported White Islands

If a white piece would fall out after cutting, the design fails.

## Rule 2: Supports Should Look Intentional

Supports should be part of the artwork whenever possible.

They can look like fur, feathers, cracks, shadows, water, teeth roots, wrinkles, or mechanical ribs.

## Rule 3: Strength Matters

Even if a white section is technically connected, it may still be too thin or weak. STEX should warn about fragile spans.

## Rule 4: The Artist Decides

STEX may suggest ribs, but the artist approves them.
