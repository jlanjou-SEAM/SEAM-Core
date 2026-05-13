"""
continuum_dashboard_export_FIXED.py
SEAM deployment snapshot exporter
"""

import json
from pathlib import Path
from datetime import datetime

REPORT_PATH = Path("reports/live_event_state.json")
OUTPUT_PATH = Path("data/latest.json")

def load_runtime_events():

    if not REPORT_PATH.exists():
        print(f"[EXPORT] Missing report: {REPORT_PATH}")
        return []

    try:

        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        #
        # Guard invalid payloads
        #
        if isinstance(payload, int):
            print("[EXPORT] Integer payload detected.")
            return []

        if payload is None:
            print("[EXPORT] Null payload detected.")
            return []

        #
        # Direct list of events
        #
        if isinstance(payload, list):
            return payload

        #
        # Dictionary payload
        #
        if isinstance(payload, dict):

            if "active_events" in payload:
                return payload["active_events"]

            if "events" in payload:
                return payload["events"]

            if "region" in payload:
                return [payload]

            print("[EXPORT] Runtime payload contains no event array.")
            return []

        print(
            f"[EXPORT] Unsupported payload type: "
            f"{type(payload).__name__}"
        )

        return []

    except Exception as e:

        print(f"[EXPORT] Failed reading runtime state: {e}")
        return []

def normalize_event(event):

    return {
        "region": event.get("region", "Unknown Region"),

        "hypothesis": event.get(
            "hypothesis",
            "SEAM analysis unavailable"
        ),

        "realization_probability": float(
            event.get("realization_probability", 0.0)
        ),

        "persistence": float(
            event.get("persistence", 0.0)
        ),

        "observation_count": int(
            event.get("observation_count", 0)
        ),

        "lat": float(event.get("lat", 0.0)),
        "lon": float(event.get("lon", 0.0)),

        "state": event.get("state", "MONITOR"),

        "trajectory": event.get(
            "trajectory",
            "unknown"
        ),

        "sources": event.get("sources", []),

        "evidence": event.get("evidence", []),

        "contradictions": event.get(
            "contradictions",
            []
        )
    }

def export_dashboard():

    raw_events = load_runtime_events()

    #
    # Final safety guard
    #
    if not isinstance(raw_events, list):
        raw_events = []

    normalized = [
        normalize_event(event)
        for event in raw_events
    ]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    payload = {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "event_count": len(normalized),
        "active_events": normalized
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(
        f"[EXPORT] Wrote {len(normalized)} events -> "
        f"{OUTPUT_PATH}"
    )

if __name__ == "__main__":
    export_dashboard()
