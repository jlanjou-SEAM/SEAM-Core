@echo off
title Continuum Logger v1.1
cd /d C:\CleanRoom

echo ==========================================================
echo CONTINUUM LOGGER v1.1
echo FULL RECURSIVE SEAM PIPELINE
echo ==========================================================
echo.

:loop

echo ==========================================================
echo [%date% %time%] STARTING PIPELINE CYCLE
echo ==========================================================
echo.

REM ==========================================================
REM STEP 1: DUAL ACQUISITION
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 1: DUAL ACQUISITION
echo ----------------------------------------------------------
python continuum_dual_acquisition_runtime.py

echo.

REM ==========================================================
REM STEP 2: DECODE PAYLOAD PIPELINE
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 2: DECODE PAYLOAD PIPELINE
echo ----------------------------------------------------------
python continuum_decoded_payload_pipeline.py

echo.

REM ==========================================================
REM STEP 3: SPACE-TIME EVENT BUS
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 3: SPACE-TIME EVENT BUS
echo ----------------------------------------------------------
python continuum_spacetime_event_bus.py

echo.

REM ==========================================================
REM STEP 4: SPATIAL AGGREGATE
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 4: SPATIAL AGGREGATE
echo ----------------------------------------------------------
python continuum_spatial_aggregate.py

echo.

REM ==========================================================
REM STEP 5: CROSS-STREAM RECONCILIATION
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 5: CROSS-STREAM RECONCILIATION
echo ----------------------------------------------------------
python continuum_cross_stream_reconcile.py

echo.

REM ==========================================================
REM STEP 6: PERSISTENT FIELD TRACKING
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 6: PERSISTENT FIELD TRACKING
echo ----------------------------------------------------------
python continuum_persistent_field_tracking.py

echo.

REM ==========================================================
REM STEP 7: FORECAST CONE ENGINE
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 7: FORECAST CONE ENGINE
echo ----------------------------------------------------------
python continuum_forecast_cone_engine.py

echo.

REM ==========================================================
REM STEP 8: STAGE-2 SEAM RECONCILIATION
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 8: STAGE-2 SEAM RECONCILIATION
echo ----------------------------------------------------------
python continuum_stage2_seam_reconcile.py

echo.

REM ==========================================================
REM STEP 9: FORECAST CORRELATION ENGINE
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 9: FORECAST CORRELATION ENGINE
echo ----------------------------------------------------------
python continuum_forecast_correlation_engine.py

echo.

REM ==========================================================
REM STEP 10: FINAL DASHBOARD EXPORT REFRESH
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 10: FINAL DASHBOARD EXPORT REFRESH
echo ----------------------------------------------------------
python continuum_cross_stream_reconcile.py

echo.

REM ==========================================================
REM STEP 11: GIT PUBLISH
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 11: GIT PUBLISH
echo ----------------------------------------------------------
git add -A
git commit -m "SEAM runtime auto-update"
git push origin main

echo.

REM ==========================================================
REM STEP 12: STATUS SUMMARY
REM ==========================================================
echo ----------------------------------------------------------
echo STEP 12: STATUS SUMMARY
echo ----------------------------------------------------------

echo.
echo RAW FILES:
dir raw /s /b | find /c ":"

echo.
echo CURATED FILES:
dir curated /s /b | find /c ":"

echo.
echo DASHBOARD EVENTS:
powershell -Command "(Get-Content data\latest.json | ConvertFrom-Json).event_count"

echo.

echo ==========================================================
echo PIPELINE COMPLETE
echo ==========================================================
echo.

echo Sleeping 10 seconds...
timeout /t 10 /nobreak > nul

goto loop
