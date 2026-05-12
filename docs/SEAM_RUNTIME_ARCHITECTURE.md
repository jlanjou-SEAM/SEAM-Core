# SEAM Runtime Architecture

## Purpose

SEAM is structured as a local acquisition and inference runtime that publishes an operational dashboard through GitHub Pages.

## Runtime Layers

| Layer | Responsibility |
|---|---|
| Source adapters | Pull latest sample from each source |
| Source logs | Append raw records to NDJSON logs |
| Manifold registry | Preserve active target continuity |
| Snapshot synthesis | Emit `latest.json` and `active_events.json` |
| Git delta sync | Commit only changed runtime artifacts |
| GitHub Pages | Render public operational dashboard |

## Current Operational Sequence

```txt
runtime.bat
  ↓
continuous_runtime.py
  ↓
source adapters
  ↓
data/source_logs/*.ndjson
  ↓
runtime/manifold_registry.py
  ↓
data/manifolds/active_manifolds.json
  ↓
latest.json
active_events.json
  ↓
git add/commit/push
  ↓
GitHub Pages
```

## Design Rule

The web interface is not hosted locally. Local runtime only creates and publishes data.
