@echo off

echo.
echo === SEAM OPERATIONAL UPDATE ===
echo.

python continuum_dual_acquisition_runtime.py

python seam_retention_manager.py

python seam_unified_recursive_field_builder.py

python seam_operational_synthesis.py

echo.
echo === COMPLETE ===
echo.
pause
