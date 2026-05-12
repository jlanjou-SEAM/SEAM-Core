# SEAM Pipeline

1. `runtime.bat`
2. `collector_launcher.py`
3. source collectors append raw NDJSON
4. `seam_engine.py` reads all accumulated raw stream logs
5. SEAM engine emits active target analysis
6. `latest.json` is written
7. Git delta sync publishes to GitHub Pages
8. `index.html` renders SEAM analysis

The raw data table is not the final product. It is the substrate.

The dashboard presents SEAM's active target analysis.
