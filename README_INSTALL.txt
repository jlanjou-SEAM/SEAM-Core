Continuum Logger v1.1
Full Recursive SEAM Pipeline

This rebuilt orchestrator now reflects the actual finalized architecture.

Pipeline:
---------
1. Dual acquisition
2. Decode pipeline
3. Space-time event synthesis
4. Spatial aggregation
5. Cross-stream reconciliation
6. Persistent field tracking
7. Forecast cone generation
8. Stage-2 recursive reconciliation
9. Forecast correlation
10. Final dashboard export refresh
11. Git publish
12. Status summary

Important:
----------
continuum_cross_stream_reconcile.py now:
- preserves live vs delayed lineage
- analyzes source convergence
- exports data/latest.json directly

Install:
--------
Replace:
    C:\CleanRoom\Continuum_Logger_v1_0_FIXED.bat

with:
    Continuum_Logger_v1_1.bat

Run:
    .\Continuum_Logger_v1_1.bat
