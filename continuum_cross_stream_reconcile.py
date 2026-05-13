
from __future__ import annotations
import json, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LIVE_EVENT_PATH = ROOT / "reports" / "live_event_state.json"
TRACK_PATH = ROOT / "reports" / "persistent_field_tracks_current.json"

DASHBOARD_OUTPUT = ROOT / "data" / "latest.json"

ACTIVE_WINDOW_HOURS = 48
MANIFOLD_THRESHOLD = 0.70

def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00"))
    except Exception:
        return None

def within_active_window(event):
    now = datetime.now(timezone.utc)

    timestamps = [
        event.get("forecast_lock_utc"),
        event.get("official_registration_utc"),
        event.get("last_seen_utc"),
        event.get("first_seen_utc")
    ]

    for ts in timestamps:
        parsed = parse_time(ts)
        if not parsed:
            continue

        if (now - parsed) <= timedelta(hours=ACTIVE_WINDOW_HOURS):
            return True

    return False

def normalize_probability(value):
    try:
        value = float(value)
    except Exception:
        return 0

    value = max(0.0, min(1.0, value))
    return round(value * 100)

def derive_manifold_lock(event):
    raw_value = (
        event.get("manifold_lock")
        or event.get("seam_phi")
        or event.get("forecast_confidence")
        or 0.0
    )

    return normalize_probability(raw_value)

def export_dashboard(events):

    payload = {
        "generated_utc":
            datetime.now(timezone.utc).isoformat(),

        "active_window_hours":
            ACTIVE_WINDOW_HOURS,

        "manifold_threshold":
            MANIFOLD_THRESHOLD,

        "event_count":
            len(events),

        "active_events":
            events
    }

    DASHBOARD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(DASHBOARD_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def reconcile(events):

    dashboard_events = []

    for event in events:

        if not within_active_window(event):
            continue

        likelihood = derive_manifold_lock(event)

        if likelihood < int(MANIFOLD_THRESHOLD * 100):
            continue

        dashboard_events.append({

            "event_id":
                event.get("event_id"),

            "region":
                f"{event.get('primary_regime','EVENT').upper()} "
                f"{float(event.get('latitude',0.0)):.2f}, "
                f"{float(event.get('longitude',0.0)):.2f}",

            "hypothesis":
                f"{event.get('primary_regime','EVENT').upper()} "
                f"target "
                f"{event.get('verification_state','UNVERIFIED').lower()}",

            "realization_probability":
                likelihood,

            "persistence":
                event.get("persistence", 15),

            "observation_count":
                event.get("observation_count", 0),

            "lat":
                event.get("latitude", 0.0),

            "lon":
                event.get("longitude", 0.0),

            "state":
                event.get("lock_state", "MONITOR"),

            "trajectory":
                "tracking",

            "sources":
                event.get("sources", []),

            "evidence": [],
            "contradictions": []
        })

    dashboard_events = sorted(
        dashboard_events,
        key=lambda x: x["realization_probability"],
        reverse=True
    )

    return dashboard_events

def main():

    live_payload = load_json(LIVE_EVENT_PATH)

    events = live_payload.get("events", [])

    print()
    print("=== SEAM ACTIVE FILTERING v1.5 ===")
    print()

    print(f"Input events: {len(events)}")

    dashboard_events = reconcile(events)

    export_dashboard(dashboard_events)

    print(f"Dashboard events: {len(dashboard_events)}")
    print(f"Output: {DASHBOARD_OUTPUT}")
    print()

if __name__ == "__main__":
    main()
