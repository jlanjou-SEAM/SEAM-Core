"""
continuum_cross_stream_reconcile.py
Version: 1.7

Tiered manifold thresholds added.

Operational Bands:
------------------
95%+  -> CRITICAL
90%+  -> ACTIVE
85%+  -> MONITOR

Below 85%:
- excluded from active dashboard
- retained in historical pipeline

12-hour active filter preserved.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent

LIVE_EVENT_PATH = ROOT / "reports" / "live_event_state.json"
TRACK_PATH = ROOT / "reports" / "persistent_field_tracks_current.json"

DASHBOARD_OUTPUT = ROOT / "data" / "latest.json"


ACTIVE_WINDOW_HOURS = 12

CRITICAL_THRESHOLD = 95
ACTIVE_THRESHOLD = 90
MONITOR_THRESHOLD = 85

FUTURE_TOLERANCE_MINUTES = 10


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
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    except Exception:
        return None


def event_times(event):

    fields = [
        "last_seen_utc",
        "official_registration_utc",
        "forecast_lock_utc",
        "first_seen_utc",
        "timestamp_utc",
        "created_utc"
    ]

    results = []

    for field in fields:

        parsed = parse_time(
            event.get(field)
        )

        if parsed:
            results.append(parsed)

    return results


def normalize_manifold_lock(value):

    try:
        raw = float(value)
    except Exception:
        return 0

    if raw <= 1.0:
        return round(raw * 100)

    if raw <= 100:
        return round(raw)

    return 100


def manifold_lock(event):

    for field in [
        "manifold_lock",
        "manifold_lock_percentage",
        "lock_percentage",
        "seam_phi",
        "forecast_confidence"
    ]:

        value = event.get(field)

        if value is not None:
            return normalize_manifold_lock(value)

    return 0


def classify_sources(sources):

    live = []
    delayed = []

    for source in sources or []:

        normalized = str(source).replace("\\", "/").lower()

        if "/raw/" in normalized:
            live.append(source)

        elif "/curated/" in normalized:
            delayed.append(source)

    return live, delayed


def track_viability(track):

    if not track:
        return 0

    count = int(track.get("event_count", 0))

    velocity = track.get("velocity_vector", {})

    delta_lat = abs(
        float(velocity.get("delta_latitude", 0.0))
    )

    delta_lon = abs(
        float(velocity.get("delta_longitude", 0.0))
    )

    motion_penalty = min(
        1.0,
        (delta_lat + delta_lon) * 5.0
    )

    base = min(
        1.0,
        math.log10(count + 1) / 2.0
    )

    viability = max(
        0.0,
        base - (motion_penalty * 0.35)
    )

    return round(viability * 100)


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

        distance = (
            abs(float(lat) - float(tlat))
            + abs(float(lon) - float(tlon))
        )

        if distance < best_distance:
            best_distance = distance
            best = track

    return best


def region_label(event):

    regime = str(
        event.get("primary_regime", "event")
    ).upper()

    lat = float(event.get("latitude", 0.0))
    lon = float(event.get("longitude", 0.0))

    return f"{regime} {lat:.2f}, {lon:.2f}"


def build_hypothesis(event):

    regime = str(
        event.get("primary_regime", "event")
    ).upper()

    verification = event.get(
        "verification_state",
        "UNVERIFIED"
    )

    lead_time = int(
        event.get("lead_time_seconds", 0)
    )

    return (
        f"{regime} target "
        f"{verification.lower()} | "
        f"lead {lead_time}s"
    )


def threshold_state(lock):

    if lock >= CRITICAL_THRESHOLD:
        return "CRITICAL"

    if lock >= ACTIVE_THRESHOLD:
        return "ACTIVE"

    if lock >= MONITOR_THRESHOLD:
        return "MONITOR"

    return None


def reconcile(events, tracks):

    now = datetime.now(timezone.utc)

    dashboard_events = []

    stats = {
        "input_events": len(events),
        "filtered_old": 0,
        "filtered_future": 0,
        "filtered_missing_time": 0,
        "filtered_threshold": 0,
        "critical_targets": 0,
        "active_targets": 0,
        "monitor_targets": 0
    }

    for index, event in enumerate(events):

        times = event_times(event)

        if not times:
            stats["filtered_missing_time"] += 1
            continue

        newest = max(times)

        if newest > now + timedelta(
            minutes=FUTURE_TOLERANCE_MINUTES
        ):
            stats["filtered_future"] += 1
            continue

        if (
            now - newest
        ) > timedelta(hours=ACTIVE_WINDOW_HOURS):

            stats["filtered_old"] += 1
            continue

        lock = manifold_lock(event)

        state = threshold_state(lock)

        if not state:
            stats["filtered_threshold"] += 1
            continue

        if state == "CRITICAL":
            stats["critical_targets"] += 1

        elif state == "ACTIVE":
            stats["active_targets"] += 1

        elif state == "MONITOR":
            stats["monitor_targets"] += 1

        live_sources, delayed_sources = classify_sources(
            event.get("sources", [])
        )

        track = nearest_track(event, tracks)

        persistence = track_viability(track)

        dashboard_events.append({

            "event_id":
                event.get(
                    "event_id",
                    f"EVT-{index:06d}"
                ),

            "region":
                region_label(event),

            "hypothesis":
                build_hypothesis(event),

            "realization_probability":
                lock,

            "persistence":
                persistence,

            "state":
                state,

            "trajectory":
                (
                    "stable"
                    if persistence > 70
                    else "tracking"
                ),

            "observation_count":
                event.get(
                    "observation_count",
                    0
                ),

            "lat":
                event.get("latitude", 0.0),

            "lon":
                event.get("longitude", 0.0),

            "sources":
                event.get("sources", []),

            "evidence": [
                f"live_sources_{len(live_sources)}",
                f"delayed_sources_{len(delayed_sources)}"
            ],

            "contradictions": []
        })

    dashboard_events = sorted(
        dashboard_events,
        key=lambda x: (
            x["realization_probability"],
            x["persistence"]
        ),
        reverse=True
    )

    stats["dashboard_events"] = len(
        dashboard_events
    )

    return dashboard_events, stats


def export_dashboard(events, stats):

    payload = {

        "generated_utc":
            datetime.now(timezone.utc).isoformat(),

        "active_window_hours":
            ACTIVE_WINDOW_HOURS,

        "thresholds": {
            "critical": CRITICAL_THRESHOLD,
            "active": ACTIVE_THRESHOLD,
            "monitor": MONITOR_THRESHOLD
        },

        "stats":
            stats,

        "event_count":
            len(events),

        "active_events":
            events
    }

    DASHBOARD_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        DASHBOARD_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(payload, f, indent=2)


def main():

    live_payload = load_json(
        LIVE_EVENT_PATH
    )

    track_payload = load_json(
        TRACK_PATH
    )

    events = live_payload.get(
        "events",
        []
    )

    tracks = track_payload.get(
        "tracks",
        []
    )

    print()
    print("=== SEAM CROSS-STREAM RECONCILIATION v1.7 ===")
    print()

    print(f"Input events: {len(events)}")
    print(f"Persistent tracks: {len(tracks)}")

    dashboard_events, stats = reconcile(
        events,
        tracks
    )

    export_dashboard(
        dashboard_events,
        stats
    )

    print()
    print(f"Critical targets: {stats['critical_targets']}")
    print(f"Active targets: {stats['active_targets']}")
    print(f"Monitor targets: {stats['monitor_targets']}")
    print(f"Dashboard events: {stats['dashboard_events']}")
    print(f"Filtered old: {stats['filtered_old']}")
    print(f"Filtered threshold: {stats['filtered_threshold']}")
    print(f"Dashboard export: {DASHBOARD_OUTPUT}")
    print()


if __name__ == "__main__":
    main()
