@echo off
title Continuum Logger v1.0
cd /d C:\CleanRoom

echo ==========================================================
echo CONTINUUM LOGGER v1.0
echo CLEAN-ROOM FULL PIPELINE ORCHESTRATOR
echo ==========================================================
echo.

:loop

echo ==========================================================
echo [%date% %time%] STARTING PIPELINE CYCLE
echo ==========================================================
echo.

echo ----------------------------------------------------------
echo STEP 1: ACQUISITION
echo ----------------------------------------------------------
python continuum_dual_acquisition_runtime.py

echo.
echo ----------------------------------------------------------
echo STEP 2: DECODE PIPELINE
echo ----------------------------------------------------------
python continuum_decoded_payload_pipeline.py

echo.
echo ----------------------------------------------------------
echo STEP 3: SPACE-TIME EVENT BUS
echo ----------------------------------------------------------
python continuum_spacetime_event_bus.py

echo.
echo ----------------------------------------------------------
echo STEP 4: SPATIAL AGGREGATE
echo ----------------------------------------------------------
python continuum_spatial_aggregate.py

echo.
echo ----------------------------------------------------------
echo STEP 5: CROSS-STREAM RECONCILIATION
echo ----------------------------------------------------------
python continuum_cross_stream_reconcile.py

echo.
echo ----------------------------------------------------------
echo STEP 6: PERSISTENT FIELD TRACKING
echo ----------------------------------------------------------
python continuum_persistent_field_tracking.py

echo.
echo ----------------------------------------------------------
echo STEP 7: FORECAST CONE ENGINE
echo ----------------------------------------------------------
python continuum_forecast_cone_engine.py

echo.
echo ----------------------------------------------------------
echo STEP 8: STAGE-2 SEAM RECONCILIATION
echo ----------------------------------------------------------
python continuum_stage2_seam_reconcile.py

echo.
echo ----------------------------------------------------------
echo STEP 9: FORECAST CORRELATION ENGINE
echo ----------------------------------------------------------
python continuum_forecast_correlation_engine.py

echo.
echo ----------------------------------------------------------
echo STEP 10: EXPORT DASHBOARD JSON
echo ----------------------------------------------------------
python continuum_dashboard_export.py

echo.
echo ----------------------------------------------------------
echo STEP 11: GIT PUBLISH
echo ----------------------------------------------------------
git add -A
git commit -m "SEAM runtime auto-update"
git push origin main

echo.
echo ==========================================================
echo PIPELINE COMPLETE
echo ==========================================================
echo.

echo Sleeping 10 seconds...
timeout /t 10 /nobreak > nul

goto loop
