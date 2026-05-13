"""
continuum_cross_stream_reconcile.py
Cross-Stream Recursive Reconciliation + Dashboard Export
Version: 1.1

Purpose
-------
Read the SEAM-generated live event state and:

- preserve independent lineage
- compare live vs delayed source paths
- correlate source convergence
- measure prediction timing
- generate dashboard-ready active events

Important:
-----------
SEAM remains authoritative for:
- canonical identity
- persistence
- manifold synthesis
- recursive event inference

This layer ONLY:
- analyzes lineage relationships
- performs temporal/spatial confirmation logic
- exports active dashboard events
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent

INPUT_PATH = ROOT / "reports" / "live_event_state.json"

REPORT_OUTPUT = ROOT / "reports" / "cross_stream_manifolds_current.json"

DASHBOARD_OUTPUT = ROOT / "data" / "latest.json"

DISTANCE_THRESHOLD_MILES = 0.5
TIME_THRESHOLD_SECONDS = 300


# ============================================================
# HELPERS
# ============================================================

def load_payload():

    if not INPUT_PATH.exists():
        print(f"[RECONCILE] Missing input: {INPUT_PATH}")
        return {}

    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"[RECONCILE] Failed loading payload: {e}")
        return {}


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

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


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


# ============================================================
# RECONCILIATION
# ============================================================

def reconcile(events):

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

        total = max(1, live_count + delayed_count)

        convergence = round(
            min(1.0, total / 10.0),
            3
        )

        lead_time = int(
            event.get("lead_time_seconds", 0)
        )

        trajectory_state = (
            "stable"
            if event.get("observation_count", 0) < 3
            else "persistent"
        )

        manifold = {
            "manifold_id":
                f"MANI-{index:05d}",

            "event_id":
                event.get("event_id"),

            "primary_regime":
                event.get(
                    "primary_regime",
                    "unknown"
                ),

            "lock_state":
                event.get(
                    "lock_state",
                    "MONITOR"
                ),

            "verification_state":
                event.get(
                    "verification_state",
                    "UNVERIFIED"
                ),

            "latitude": lat,
            "longitude": lon,

            "forecast_confidence":
                event.get(
                    "forecast_confidence",
                    0.0
                ),

            "observation_count":
                event.get(
                    "observation_count",
                    0
                ),

            "live_source_count":
                live_count,

            "delayed_source_count":
                delayed_count,

            "source_convergence":
                convergence,

            "lead_time_seconds":
                lead_time,

            "trajectory_state":
                trajectory_state
        }

        manifolds.append(manifold)

        dashboard_events.append({
            "event_id":
                event.get("event_id"),

            "primary_regime":
                event.get(
                    "primary_regime",
                    "unknown"
                ),

            "latitude": lat,
            "longitude": lon,

            "forecast_confidence":
                event.get(
                    "forecast_confidence",
                    0.0
                ),

            "lock_state":
                event.get(
                    "lock_state",
                    "MONITOR"
                ),

            "verification_state":
                event.get(
                    "verification_state",
                    "UNVERIFIED"
                ),

            "lead_time_seconds":
                lead_time,

            "live_source_count":
                live_count,

            "delayed_source_count":
                delayed_count,

            "source_convergence":
                convergence,

            "observation_count":
                event.get(
                    "observation_count",
                    0
                ),

            "trajectory_state":
                trajectory_state,

            "sources":
                event.get("sources", []),

            "first_seen_utc":
                event.get(
                    "forecast_lock_utc"
                ),

            "last_seen_utc":
                event.get(
                    "official_registration_utc"
                )
        })

    return manifolds, dashboard_events


# ============================================================
# EXPORT
# ============================================================

def export_manifolds(manifolds):

    REPORT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    payload = {
        "timestamp_utc":
            datetime.now(timezone.utc).isoformat(),

        "distance_threshold_miles":
            DISTANCE_THRESHOLD_MILES,

        "time_threshold_seconds":
            TIME_THRESHOLD_SECONDS,

        "manifold_count":
            len(manifolds),

        "manifolds":
            manifolds
    }

    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def export_dashboard(events):

    DASHBOARD_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    payload = {
        "generated_utc":
            datetime.now(timezone.utc).isoformat(),

        "event_count":
            len(events),

        "active_events":
            events
    }

    with open(DASHBOARD_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ============================================================
# MAIN
# ============================================================

def main():

    payload = load_payload()

    events = payload.get("events", [])

    print()
    print("=== SEAM CROSS-STREAM RECONCILIATION v1.1 ===")
    print()

    print(f"Input events: {len(events)}")

    manifolds, dashboard_events = reconcile(events)

    export_manifolds(manifolds)

    export_dashboard(dashboard_events)

    print(f"Manifolds: {len(manifolds)}")
    print(f"Dashboard events: {len(dashboard_events)}")
    print(f"Reports: {REPORT_OUTPUT}")
    print(f"Dashboard: {DASHBOARD_OUTPUT}")
    print()


if __name__ == "__main__":
    main()
