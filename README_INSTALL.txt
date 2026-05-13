SEAM Metric Correction v1.4

Authoritative mapping restored.

Likelihood:
    manifold_lock (direct from SEAM)

Persistence:
    long-term track viability

Removed:
- lock-state weighting
- probability boosting
- heuristic confidence blending
- source-count scoring

Install:
--------
Replace:
    C:\CleanRoom\continuum_cross_stream_reconcile.py

Run:
----
python continuum_cross_stream_reconcile.py

Publish:
--------
git add -A
git commit -m "Restore authoritative manifold lock mapping"
git push origin main
