"""
Continuum Logger v1.0
SEAM Runtime Deployment Export Layer

Purpose:
- Run the Continuum runtime
- Normalize active target events
- Export deployment-ready JSON
- Push refreshed dashboard state to GitHub Pages

Expected deployment layout:

C:\CleanRoom
│
├── continuum_unified_realtime_runtime.py
├── Continuum_Logger_v1_0.py
├── data\
│   └── latest.json
│
├── css\
├── js\
└── index.html

"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

REFRESH_INTERVAL_SECONDS = 10

DEPLOY_JSON_PATH = Path("data/latest.json")

GIT_COMMIT_MESSAGE = "SEAM runtime auto-update"

# ============================================================
# RUNTIME IMPORT
# ============================================================

try:
    import continuum_unified_realtime_runtime as runtime
except Exception as runtime_import_error:
    print("[SEAM] Failed importing runtime:")
    print(runtime_import_error)
    sys.exit(1)

# ============================================================
# EVENT NORMALIZATION
# ============================================================

def normalize_event(raw_event):
    """
    Convert runtime event structures into dashboard schema.
    """

    return {
        "region": raw_event.get("region", "Unknown Region"),
        "hypothesis": raw_event.get(
            "hypothesis",
            "SEAM analysis unavailable"
        ),

        "realization_probability": float(
            raw_event.get("realization_probability", 0.0)
        ),

        "persistence": float(
            raw_event.get("persistence", 0.0)
        ),

        "observation_count": int(
            raw_event.get("observation_count", 0)
        ),

        "lat": float(raw_event.get("lat", 0.0)),
        "lon": float(raw_event.get("lon", 0.0)),

        "state": raw_event.get("state", "MONITOR"),

        "trajectory": raw_event.get(
            "trajectory",
            "unknown"
        ),

        "sources": raw_event.get("sources", []),

        "evidence": raw_event.get("evidence", []),

        "contradictions": raw_event.get(
            "contradictions",
            []
        )
    }

# ============================================================
# EXPORT
# ============================================================

def export_dashboard_events(events):
    """
    Write deployment-ready dashboard snapshot.
    """

    DEPLOY_JSON_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    payload = {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "event_count": len(events),
        "active_events": events
    }

    with open(DEPLOY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(
        f"[SEAM] Exported {len(events)} events -> "
        f"{DEPLOY_JSON_PATH}"
    )

# ============================================================
# GIT PUBLISH
# ============================================================

def run_git_command(args):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result.returncode == 0

def publish_to_github():
    """
    Commit and push updated deployment snapshot.
    """

    print("[SEAM] Publishing dashboard update...")

    run_git_command(["git", "add", "-A"])

    commit_ok = run_git_command([
        "git",
        "commit",
        "-m",
        GIT_COMMIT_MESSAGE
    ])

    # Commit may fail if nothing changed.
    if not commit_ok:
        print("[SEAM] No new git changes detected.")

    push_ok = run_git_command([
        "git",
        "push",
        "origin",
        "main"
    ])

    if push_ok:
        print("[SEAM] GitHub Pages update pushed.")
    else:
        print("[SEAM] Git push failed.")

# ============================================================
# RUNTIME COLLECTION
# ============================================================

def collect_runtime_events():
    """
    Adapter layer for runtime integration.

    Replace this section with actual runtime hooks if needed.
    """

    #
    # OPTION 1:
    # Runtime exposes active events directly.
    #
    if hasattr(runtime, "active_events"):
        return runtime.active_events

    #
    # OPTION 2:
    # Runtime exposes callable.
    #
    if hasattr(runtime, "get_active_events"):
        return runtime.get_active_events()

    #
    # OPTION 3:
    # Placeholder test event.
    #
    return [
        {
            "region": "SEAM Runtime Online",
            "hypothesis":
                "Continuum Logger export pipeline operational.",

            "realization_probability": 0.82,
            "persistence": 0.74,
            "observation_count": 3,

            "lat": 0.0,
            "lon": 0.0,

            "state": "FOLLOW",

            "trajectory": "stable",

            "sources": [
                "continuum_runtime",
                "deployment_pipeline"
            ],

            "evidence": [
                "runtime_initialized",
                "export_active",
                "github_publish_enabled"
            ],

            "contradictions": []
        }
    ]

# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print("=" * 60)
    print("Continuum Logger v1.0")
    print("SEAM Runtime Deployment Export Layer")
    print("=" * 60)

    while True:

        try:

            print("\n[SEAM] Collecting runtime events...")

            raw_events = collect_runtime_events()

            normalized_events = [
                normalize_event(event)
                for event in raw_events
            ]

            export_dashboard_events(normalized_events)

            publish_to_github()

            print(
                f"[SEAM] Sleeping "
                f"{REFRESH_INTERVAL_SECONDS}s..."
            )

        except Exception as runtime_error:

            print("[SEAM] Runtime cycle failed:")
            print(runtime_error)

        time.sleep(REFRESH_INTERVAL_SECONDS)

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    main()
