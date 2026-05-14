SEAM Location Resolution Update v1.3

Files:
- seam_operational_synthesis.py
- index.html
- ledger.html

Fixes:
- Adds structured location object to every operational event.
- No more Unresolved if coordinates exist.
- Adds area/country/state/city/locality fallback.
- FOLLOW uses county/area style location.
- TARGET uses city/state/country + lat/long.
- FULL LOCK uses best full place + lat/long.
- Ledger uses full location string.

Run:
python seam_operational_synthesis.py

Then publish:
git add -A
git commit -m "Add operational location resolution"
git push origin main
