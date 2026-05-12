Extract into C:\CleanRoom and overwrite:

continuum_dual_acquisition_runtime.py

Run remains:

python continuum_unified_realtime_runtime.py

This is a real functional acquisition replacement:
- uses existing config/dual_acquisition_sources.json
- no requests dependency
- parallel raw acquisition
- parallel curated acquisition
- writes raw files
- writes curated files
- source health quarantine
- skips known no_valid_endpoint sources
- preserves single-pass behavior for unified runtime
