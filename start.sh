#!/bin/bash

echo "[SEAM] Initializing finite bootstrap runtime..."

if [ ! -d "venv" ]; then
  echo "[SEAM] Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "[SEAM] Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[SEAM] Preparing runtime files..."
python3 collector_launcher.py

echo "[SEAM] Running finite bootstrap test..."
python3 bootstrap_runner.py --record-target 5000

echo "[SEAM] Bootstrap complete."
echo "[SEAM] Review logs/bootstrap_report.json"
echo "[SEAM] Commit and push updates to GitHub Pages."
