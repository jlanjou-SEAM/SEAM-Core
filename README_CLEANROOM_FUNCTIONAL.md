# CleanRoom Functional Replacement

Replace `C:\CleanRoom` with this folder content.

Run:

```powershell
python continuum_unified_realtime_runtime.py
```

Compatibility run:

```powershell
python continuum_unified_realtime_runtime_FIXED.py
```

Runtime sequence:

1. acquisition single pass
2. incremental decode from raw and curated JSON/GeoJSON
3. spacetime canonical event bus
4. spatial aggregate
5. cross-stream manifold reconcile
6. persistent field tracking
7. forecast cones
8. SEAM master reconciliation
9. forecast/official registration correlation
10. live index output

Primary frontend output:

`reports/live_event_state.json`

Other current outputs:

- `reports/canonical_spacetime_events_current.json`
- `reports/spatial_aggregate_current.json`
- `reports/cross_stream_manifolds_current.json`
- `reports/persistent_field_tracks_current.json`
- `reports/forecast_cones_current.json`
- `reports/seam_master_reconciliation_current.json`
- `reports/seam_master_reconciliation_current.md`

This package intentionally excludes prior test bundles, old patch zips, and historical raw/curated payload archives.
