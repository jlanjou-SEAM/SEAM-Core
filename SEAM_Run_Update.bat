@echo off
title SEAM Semantic Runtime v2.0

cd /d %~dp0

:SEAM_LOOP

cls

echo.
echo ==========================================
echo       SEAM SEMANTIC RUNTIME v2.0
echo ==========================================
echo.

echo [1/8] Acquisition Runtime
python continuum_dual_acquisition_runtime.py

echo.
echo [2/8] Retention Management
python seam_retention_manager.py

echo.
echo [3/8] Unified Recursive Field
python seam_unified_recursive_field_builder.py

echo.
echo [4/8] Operational Synthesis
python seam_operational_synthesis.py

echo.
echo [5/8] Telemetry Publish

git checkout telemetry

git checkout main -- data/latest.json
git checkout main -- reports/seam_recursive_operational_state.json

git add data/latest.json
git add reports/seam_recursive_operational_state.json

git diff --cached --quiet

if errorlevel 1 (

    git commit -m "SEAM semantic telemetry update"

    git push origin telemetry

)

git checkout main

echo.
echo [6/8] Cleanup Runtime Caches

if exist raw del /q /s raw\* >nul 2>&1
if exist decoded del /q /s decoded\* >nul 2>&1

echo.
echo [7/8] Semantic Continuity Preserved

echo.
echo [8/8] Pause 30s

timeout /t 30 /nobreak >nul

goto SEAM_LOOP
