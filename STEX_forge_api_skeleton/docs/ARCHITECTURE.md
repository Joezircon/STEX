# STEX Architecture

## STEX vs Forge

**STEX** is the desktop application.

**Forge** is the manufacturability engine.

## Why separate them?

Because Forge may eventually be used by:

- STEX
- an Inkscape plugin
- a Photoshop plugin
- a web app
- command-line tools
- Cricut/laser workflows

## Current Architecture

```text
Image
  ↓
ForgeEngine
  ↓
ForgeReport
  ↓
STEX UI
  ↓
Canvas Overlay / Inspector
```

## Module Responsibilities

### STEX UI

- windows
- buttons
- arcade interface
- user interaction
- Ribot
- file dialogs

### Canvas

- image display
- zoom
- pan
- overlays
- selection
- rib preview

### Forge Engine

- topology inspection
- white island detection
- weak span detection
- export validation
- rib suggestions

### Rib Engine

- creates ribs
- previews ribs
- stores rib objects
- applies accepted ribs

### Export Engine

- PNG export
- SVG export
- Cricut-ready output
- Mosaic Mode output
