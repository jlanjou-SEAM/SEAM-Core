SEAM Live UI Refresh v1.2

Files:
- index.html
- ledger.html

Updates:
- 10 second auto refresh on both pages
- visible countdown timer
- human-readable UTC timestamps on STATUS cards
- ISO/UTC precision retained on LOG page
- manifold velocity field display if present
- observation/source/detector line support
- FULL DATA RECORDING remains at top
- LOG / STATUS buttons preserved

Install:
Replace index.html and ledger.html.

Publish:
git add -A
git commit -m "Update SEAM UI refresh and lifecycle display"
git push origin main
