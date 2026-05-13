"""
continuum_cross_stream_reconcile.py
Version: 1.3
"""

from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LIVE_EVENT_PATH = ROOT / "reports" / "live_event_state.json"
TRACK_PATH = ROOT / "reports" / "persistent_field_tracks_current.json"

REPORT_OUTPUT = ROOT / "reports" / "cross_stream_manifolds_current.json"
DASHBOARD_OUTPUT = ROOT / "data" / "latest.json"

def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def classify_sources(sources):
    live = []
    delayed = []
    for source in sources or []:
        normalized = str(source).replace("\\\\", "/").lower()
        if "/raw/" in normalized:
            live.append(source)
        elif "/curated/" in normalized:
            delayed.append(source)
    return live, delayed

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize_probability(value):
    try:
        value = float(value)
    except Exception:
        return 0
    value = max(0.0, min(1.0, value))
    return round(value * 100)

def derive_lock_percentage(event):
    seam_phi = float(
        event.get(
            "forecast_confidence",
            event.get("seam_phi", 0.0)
        ) or 0.0
    )

    lock_state = str(event.get("lock_state", "MONITOR")).upper()

    state_boost = {
        "MONITOR": 0.15,
        "FOLLOW": 0.35,
        "TARGET": 0.55,
        "HARD LOCK": 0.75,
        "CONFIRMED": 0.90
    }.get(lock_state, 0.10)

    probability = (
        seam_phi * 0.65
        + state_boost * 0.35
    )

    return normalize_probability(probability)

def derive_track_viability(track):
    if not track:
        return 0

    count = int(track.get("event_count", 0))

    velocity = track.get("velocity_vector", {})

    delta_lat = abs(float(velocity.get("delta_latitude", 0.0)))
    delta_lon = abs(float(velocity.get("delta_longitude", 0.0)))

    motion_penalty = min(
        1.0,
        (delta_lat + delta_lon) * 5.0
    )

    base = min(1.0, math.log10(count + 1) / 2.0)

    viability = max(
        0.0,
        base - (motion_penalty * 0.35)
    )

    return normalize_probability(viability)

def nearest_track(event, tracks):
    lat = event.get("latitude")
    lon = event.get("longitude")

    if lat is None or lon is None:
        return None

    best = None
    best_distance = 999999

    for track in tracks:
        tlat = track.get("current_latitude")
        tlon = track.get("current_longitude")

        if tlat is None or tlon is None:
            continue

        distance = haversine_miles(
            float(lat),
            float(lon),
            float(tlat),
            float(tlon)
        )

        if distance < best_distance:
            best_distance = distance
            best = track

    return best

def region_label(event):
    regime = str(event.get("primary_regime", "event")).upper()
    lat = float(event.get("latitude", 0.0))
    lon = float(event.get("longitude", 0.0))
    return f"{regime} {lat:.2f}, {lon:.2f}"

def build_hypothesis(event, live_count, delayed_count):
    regime = str(event.get("primary_regime", "event")).upper()
    verification = event.get("verification_state", "UNVERIFIED")
    lead_time = int(event.get("lead_time_seconds", 0))
    return (
        f"{regime} target "
        f"{verification.lower()} | "
        f"lead {lead_time}s | "
        f"live {live_count} / delayed {delayed_count}"
    )

def reconcile(events, tracks):
    manifolds = []
    dashboard_events = []

    for index, event in enumerate(events):
        lat = event.get("latitude")
        lon = event.get("longitude")

        if lat is None or lon is None:
            continue

        live_sources, delayed_sources = classify_sources(
            event.get("sources", [])
        )

        live_count = len(live_sources)
        delayed_count = len(delayed_sources)

        track = nearest_track(event, tracks)

        likelihood = derive_lock_percentage(event)
        persistence = derive_track_viability(track)

        trajectory = (
            "stable"
            if persistence > 70
            else "tracking"
            if persistence > 40
            else "volatile"
        )

        dashboard_event = {
            "event_id": event.get("event_id", f"EVT-{index:06d}"),
            "region": region_label(event),
            "hypothesis": build_hypothesis(event, live_count, delayed_count),
            "realization_probability": likelihood,
            "persistence": persistence,
            "observation_count": event.get("observation_count", 0),
            "lat": lat,
            "lon": lon,
            "state": event.get("lock_state", "MONITOR"),
            "trajectory": trajectory,
            "primary_regime": event.get("primary_regime", "unknown"),
            "verification_state": event.get("verification_state", "UNVERIFIED"),
            "lead_time_seconds": int(event.get("lead_time_seconds", 0)),
            "live_source_count": live_count,
            "delayed_source_count": delayed_count,
            "sources": event.get("sources", []),
            "evidence": [
                f"verification_{event.get('verification_state', 'unknown').lower()}",
                f"live_sources_{live_count}",
                f"delayed_sources_{delayed_count}"
            ],
            "contradictions": []
        }

        dashboard_events.append(dashboard_event)

        manifolds.append({
            "manifold_id": f"MANI-{index:05d}",
            "event_id": dashboard_event["event_id"],
            "likelihood": likelihood,
            "persistence": persistence
        })

    return manifolds, dashboard_events

def export_manifolds(manifolds):
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifold_count": len(manifolds),
        "manifolds": manifolds
    }
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def export_dashboard(events):
    DASHBOARD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "event_count": len(events),
        "active_events": events
    }
    with open(DASHBOARD_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def main():
    live_payload = load_json(LIVE_EVENT_PATH)
    track_payload = load_json(TRACK_PATH)

    events = live_payload.get("events", [])
    tracks = track_payload.get("tracks", [])

    print()
    print("=== SEAM CROSS-STREAM RECONCILIATION v1.3 ===")
    print()

    print(f"Input events: {len(events)}")
    print(f"Persistent tracks: {len(tracks)}")

    manifolds, dashboard_events = reconcile(events, tracks)

    export_manifolds(manifolds)
    export_dashboard(dashboard_events)

    print(f"Manifolds: {len(manifolds)}")
    print(f"Dashboard events: {len(dashboard_events)}")
    print(f"Dashboard export: {DASHBOARD_OUTPUT}")
    print()

if __name__ == "__main__":
    main()
