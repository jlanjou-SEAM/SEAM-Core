Continuum Dual Acquisition Runtime v1.0

This replaces the non-executing acquisition stub.

What it does:
- reads config/dual_acquisition_sources.json
- uses the full configured source list
- fetches primary_raw and secondary_curated endpoints
- routes GeoJSON / FeatureCollection payloads to raw/<source>/...
- routes all non-GeoJSON reports to curated/<source>/...
- routes all secondary_curated endpoints to curated/<source>/...
- writes logs/acquisition_log.jsonl
- writes state/source_health.json

Install:
1. Copy continuum_dual_acquisition_runtime.py into C:\CleanRoom
2. Overwrite the existing file.
3. Run:

   python continuum_dual_acquisition_runtime.py

4. Verify:

   dir raw
   dir curated
   Get-Content logs\acquisition_log.jsonl -Tail 20

Then run the existing Continuum Logger batch again.
