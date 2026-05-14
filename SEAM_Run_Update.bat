@echo off
title SEAM Operational Runtime
cd /d %~dp0

:SEAM_LOOP

cls
echo.
echo ==========================================
echo        SEAM OPERATIONAL RUNTIME
echo ==========================================
echo.

echo [1/6] Acquisition Runtime
python continuum_dual_acquisition_runtime.py

echo.
echo [2/6] Retention Management
python seam_retention_manager.py

echo.
echo [3/6] Unified Recursive Field
python seam_unified_recursive_field_builder.py

echo.
echo [4/6] Operational Synthesis
python seam_operational_synthesis.py

echo.
echo [5/6] Git Update
git add -A

git commit -m "SEAM automated operational update"

git push origin main

echo.
echo [6/6] Runtime Pause
echo Waiting 30 seconds before next cycle...
echo.

timeout /t 30 /nobreak >nul

goto SEAM_LOOP
