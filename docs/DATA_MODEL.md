# SEAM Data Model

## Source Logs

Path:

```txt
data/source_logs/<source>.ndjson
```

Purpose:

- append-only raw sample history
- source-level audit trail
- local accumulation of observational fabric

Each line is one JSON object.

## Manifold Registry

Path:

```txt
data/manifolds/active_manifolds.json
```

Purpose:

- persistent active target continuity
- prevents target loss between runtime cycles
- keeps TARGET/FOLLOW/MONITOR state stable across updates

## Public Runtime Snapshot

Paths:

```txt
latest.json
active_events.json
```

Purpose:

- public dashboard input
- operational snapshot
- regenerated from persistent manifold registry

## Dashboard Fields

The dashboard expects active event objects with:

```json
{
  "region": "Hawaii Volcanic Chain",
  "lat": 19.2632,
  "lon": -155.3913,
  "state": "TARGET",
  "hypothesis": "Persistent shallow seismic activation",
  "probability": 0.68,
  "persistence": 0.74,
  "trajectory": "South drift 3 km/hr",
  "sources": ["USGS", "IRIS", "EMSC"],
  "evidence": ["quake clustering"],
  "contradictions": ["quiet geomagnetic context"]
}
```
