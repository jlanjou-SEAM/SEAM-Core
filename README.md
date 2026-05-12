# SEAM Full Analysis Runtime Repository

This is the full current runtime repository.

## Pipeline

```txt
raw stream collectors
→ append NDJSON records
→ seam_engine.py
→ active target analysis
→ latest.json
→ GitHub Pages dashboard
```

## Important

The webpage does not analyze raw data.

The local runtime calls `seam_engine.py` after every collection cycle. The engine parses accumulated raw stream logs and writes `latest.json` / `active_events.json`.

## Run

First setup:

```bat
start.bat
```

Continuous updates:

```bat
runtime.bat
```
