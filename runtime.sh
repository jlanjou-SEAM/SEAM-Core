#!/bin/bash

source venv/bin/activate

echo "[SEAM] Starting continuous runtime mode..."
python3 continuous_runtime.py --record-target 5000 --interval 300

echo "[SEAM] Runtime updates will write to latest.json"
echo "[SEAM] Push changes to GitHub to publish dashboard updates."
