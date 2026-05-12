@echo off
title SEAM Bootstrap

if not exist venv (
  python -m venv venv
)

call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

python collector_launcher.py
python seam_engine.py

echo [SEAM] Bootstrap complete. Run runtime.bat for continuous analysis updates.

pause
