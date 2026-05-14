@echo off
setlocal enabledelayedexpansion
cd /d C:\CleanRoom

echo.
echo === SEAM CLEAN RUNTIME UPDATE v1.4 ===
echo.

python continuum_dual_acquisition_runtime.py
if errorlevel 1 goto fail

python seam_retention_manager.py
if errorlevel 1 goto fail

python seam_unified_recursive_field_builder.py
if errorlevel 1 goto fail

python seam_operational_synthesis.py
if errorlevel 1 goto fail

echo.
echo === GIT DEPLOY ===
echo.

git add -A
if errorlevel 1 goto fail

git commit -m "SEAM operational runtime update"
if errorlevel 1 echo No git changes to commit.

git push origin main
if errorlevel 1 goto fail

echo.
echo SEAM update complete.
goto end

:fail
echo.
echo SEAM update failed. See console output above.
exit /b 1

:end
endlocal
