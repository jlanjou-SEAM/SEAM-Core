SEAM Tiered Threshold Filtering v1.7

New operational manifold bands:

95%+  -> CRITICAL
90%+  -> ACTIVE
85%+  -> MONITOR

Below 85%:
- excluded from dashboard
- retained historically

Additional filtering preserved:
- only events active within last 12 hours

Expected result:
- dramatically fewer dashboard tiles
- stronger recursive target concentration
- clearer manifold hierarchy

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
git commit -m "Add tiered manifold threshold filtering"
git push origin main
