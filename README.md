# STEX

**Stencil Topology Editor eXperimental**

STEX is a desktop application for transforming artwork into structurally sound, manufacturable stencils while preserving the artist's original vision.

## Current Alpha Goal

Load a black/white stencil image, inspect it, detect unsupported white islands, and show the result visually.

## Current Features

- Arcade/synthwave-style interface
- Insert image
- Zoom and pan canvas
- Forge white-island detection engine
- Topology Check
- Red overlay boxes around unsupported white islands
- Example test image

## Core Rule

White = stencil material that remains.  
Black = cutout space.  

White islands are failures.  
Black islands are acceptable.

## Automatic Windows Build

This repo includes a GitHub Actions workflow at:

`.github/workflows/windows-build.yml`

When changes are pushed to `main`, GitHub should build a Windows executable artifact named:

`STEX-Windows-Build`

## STEX Philosophy

STEX suggests.  
The artist decides.
