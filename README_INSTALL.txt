SEAM Clean Runtime Rebuild v1.4

Purpose
-------
Fix filename mismatches and standardize the retrieval-to-deployment runtime.
This is a real rebuild, not wrapper aliases.

Canonical runtime files
-----------------------
continuum_dual_acquisition_runtime.py
seam_retention_manager.py
seam_unified_recursive_field_builder.py
seam_operational_synthesis.py
index.html
ledger.html
SEAM_Run_Update.bat
.gitignore

Runtime order
-------------
1. python continuum_dual_acquisition_runtime.py
2. python seam_retention_manager.py
3. python seam_unified_recursive_field_builder.py
4. python seam_operational_synthesis.py
5. git add -A
6. git commit -m "SEAM operational runtime update"
7. git push origin main

Install
-------
1. Extract all files into C:\CleanRoom
2. Run optional cleanup:
   powershell -ExecutionPolicy Bypass -File CLEANUP_DEPRECATED_FILES.ps1
3. Run:
   SEAM_Run_Update.bat

Notes
-----
The GitHub repository currently contains older names such as continuum_retention_manager.py and older patch files. This package standardizes the local runtime around the script names used in the operational batch.
