@echo off
title SEAM Analysis Runtime

call venv\Scripts\activate

echo [SEAM] Starting analysis runtime...

python collector_launcher.py
python continuous_runtime.py

pause
