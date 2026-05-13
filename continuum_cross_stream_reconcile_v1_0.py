"""
continuum_cross_stream_reconcile.py
Cross-Stream Recursive Event Reconciliation
Version: 1.0

Purpose
-------
Correlate independently inferred LIVE and DELAYED events
without collapsing lineage during ingestion.

This stage preserves:
- temporal separation
- source lineage
- prediction timing
- official confirmation timing

Correlation Thresholds
----------------------
distance <= 0.5 miles
time delta <= 5 minutes

Important:
-----------
This stage DOES NOT hard-merge events.

It creates:
- candidate correlated identities
- manifold relationships
- reinforcement structures

The persistent tracking layer later determines:
- continuity
- movement
- divergence
- confirmation state
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


ROOT = Path(__file__).resolve().parent

LIVE_PATH = ROOT / "analysis" / "live_targets.json"
DELAYED_PATH = ROOT / "analysis" / "stale_targets.json"

OUTPUT_PATH = ROOT / "reports" / "cross_stream_manifolds_current.json"

DISTANCE_THRESHOLD_MILES = 0.5
TIME_THRESHOLD_SECONDS = 300


# ============================================================
# HELPERS
# ============================================================

def load_json(path: Path):
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):

            if "events" in payload:
                return payload["events"]

            if "targets" in payload:
                return payload["targets"]

            return []

    except Exception as e:
        print(f"[RECONCILE] Failed loading {path}: {e}")

    return []


def parse_time(value: str):

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except Exception:
        return None


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


def temporal_delta_seconds(a, b):

    ta = parse_time(a)
    tb = parse_time(b)

    if not ta or not tb:
        return 999999

    return abs((ta - tb).total_seconds())


# ============================================================
# EVENT CORRELATION
# ============================================================

def correlate(live_events, delayed_events):

    manifolds = []

    manifold_index = 0

    for live in live_events:

        live_lat = live.get("latitude")
        live_lon = live.get("longitude")

        if live_lat is None or live_lon is None:
            continue

        live_time = (
            live.get("forecast_lock_utc")
            or live.get("first_seen_utc")
            or live.get("timestamp_utc")
        )

        correlated = []

        for delayed in delayed_events:

            delayed_lat = delayed.get("latitude")
            delayed_lon = delayed.get("longitude")

            if delayed_lat is None or delayed_lon is None:
                continue

            delayed_time = (
                delayed.get("official_registration_utc")
                or delayed.get("first_seen_utc")
                or delayed.get("timestamp_utc")
            )

            distance = haversine_miles(
                float(live_lat),
                float(live_lon),
                float(delayed_lat),
                float(delayed_lon)
            )

            delta_t = temporal_delta_seconds(
                live_time,
                delayed_time
            )

            if (
                distance <= DISTANCE_THRESHOLD_MILES
                and delta_t <= TIME_THRESHOLD_SECONDS
            ):

                correlated.append({
                    "delayed_event_id":
                        delayed.get(
                            "event_id",
                            delayed.get(
                                "canonical_event_id",
                                "UNKNOWN"
                            )
                        ),

                    "distance_miles": round(distance, 4),

                    "time_delta_seconds": int(delta_t),

                    "verification_state":
                        delayed.get(
                            "verification_state",
                            "UNVERIFIED"
                        ),

                    "forecast_confidence":
                        delayed.get(
                            "forecast_confidence",
                            delayed.get("seam_phi", 0.0)
                        ),

                    "source_count":
                        delayed.get("source_count", 0)
                })

        manifolds.append({
            "manifold_id":
                f"MANI-{manifold_index:05d}",

            "timestamp_utc":
                datetime.now(timezone.utc).isoformat(),

            "live_event_id":
                live.get(
                    "event_id",
                    live.get(
                        "canonical_event_id",
                        "UNKNOWN"
                    )
                ),

            "primary_regime":
                live.get(
                    "primary_regime",
                    "unknown"
                ),

            "lock_state":
                live.get(
                    "lock_state",
                    "MONITOR"
                ),

            "latitude": live_lat,
            "longitude": live_lon,

            "forecast_confidence":
                live.get(
                    "forecast_confidence",
                    live.get("seam_phi", 0.0)
                ),

            "observation_count":
                live.get(
                    "observation_count",
                    0
                ),

            "correlated_event_count":
                len(correlated),

            "correlated_events":
                correlated
        })

        manifold_index += 1

    return manifolds


# ============================================================
# EXPORT
# ============================================================

def export(manifolds):

    OUTPUT_PATH.parent.mkdir(
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

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print()
    print("=== CROSS-STREAM RECONCILIATION ===")
    print()
    print(f"Live events: {len(manifolds)}")
    print(f"Threshold distance: {DISTANCE_THRESHOLD_MILES} miles")
    print(f"Threshold time: {TIME_THRESHOLD_SECONDS} seconds")
    print(f"Output: {OUTPUT_PATH}")
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    live_events = load_json(LIVE_PATH)
    delayed_events = load_json(DELAYED_PATH)

    print()
    print("=== SEAM CROSS-STREAM RECONCILIATION ===")
    print()
    print(f"Live events loaded: {len(live_events)}")
    print(f"Delayed events loaded: {len(delayed_events)}")

    manifolds = correlate(
        live_events,
        delayed_events
    )

    export(manifolds)


if __name__ == "__main__":
    main()
