SEAM dashboard schema correction v1.2

Install:
1. Replace C:\CleanRoom\continuum_cross_stream_reconcile.py
2. Replace C:\CleanRoom\js\runtime-ui.js

Then run:
python continuum_cross_stream_reconcile.py

Verify:
Get-Content data\latest.json -Head 40

Publish:
git add -A
git commit -m "Fix dashboard event schema mapping"
git push origin main

Expected dashboard corrections:
- no more Unknown Region
- real coordinates appear
- hypothesis text appears
- confidence maps to Likelihood
- source convergence maps to Persistence
- trajectory and verification status appear
