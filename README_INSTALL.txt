SEAM Active Event Filtering v1.5

Corrections:
- only events active within last 48 hours appear on tile dashboard
- manifold threshold filtering added (70%)
- historical events excluded from active tile view
- authoritative manifold lock preserved

Install:
Replace:
C:\CleanRoom\continuum_cross_stream_reconcile.py

Then run:
python continuum_cross_stream_reconcile.py

Then publish:
git add -A
git commit -m "Add active event filtering"
git push origin main
