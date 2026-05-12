# Collector Adapter Contract

Each collector must be executable as a standalone Python file from the repository root.

Example:

```bash
python usgs.py
```

## Required Behavior

A collector must:

- create `data/source_logs/` if missing
- append exactly one latest-sample record per run
- write NDJSON
- preserve raw payload
- avoid classification
- avoid event inference
- print a short completion line

## Required Record Shape

```json
{
  "timestamp_utc": "2026-05-08T00:00:00Z",
  "source": "USGS",
  "payload": {
    "sample": "latest_observation"
  }
}
```

## Forbidden Behavior

Collectors should not:

- classify events
- score probability
- create targets
- overwrite source logs
- clear old records
- write `latest.json`
- modify the manifold registry

SEAM inference and target persistence occur after collection.
