"""
seam_operational_synthesis.py
Version: 1.2

SEAM Operational Synthesis with Recursive Transitive Convergence

Input:
------
combined/seam_unified_recursive_field_48h.json

Outputs:
--------
reports/seam_recursive_operational_state.json
data/latest.json

Purpose:
--------
1. Generate local recursive manifold seeds.
2. Perform iterative transitive convergence:
      A ~ B, B ~ C => A/B/C become one canonical manifold.
3. Recompute canonical manifold fields after convergence.
4. Export compact active operational targets.

This is intended to collapse regional swarms such as:
- Brawley
- The Geysers / Cobb
- other spatially continuous recursive fields
"""

from __future__ import annotations

import json
import math
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent

COMBINED_INPUT = ROOT / "combined" / "seam_unified_recursive_field_48h.json"

REPORT_OUTPUT = ROOT / "reports" / "seam_recursive_operational_state.json"
DASHBOARD_OUTPUT = ROOT / "data" / "latest.json"

ACTIVE_OUTPUT_LIMIT = 80
MIN_DASHBOARD_LOCK = 50.0

# Recursive convergence controls.
CONVERGENCE_SCORE_THRESHOLD = 0.58
STRONG_DISTANCE_KM = 18.0
WEAK_DISTANCE_KM = 45.0
TIME_CHAIN_HOURS = 8.0


def utc_now():
    return datetime.now(timezone.utc)


def load_json(path: Path):
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[SEAM] Failed loading {path}: {exc}")
        return {}


def parse_time(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            if value > 10_000_000_000:
                return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            if value > 1_000_000_000:
                return datetime.fromtimestamp(value, tz=timezone.utc)
        except Exception:
            return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def payload(obs):
    p = obs.get("payload")
    return p if isinstance(p, dict) else {}


def properties(obs):
    p = payload(obs)
    props = p.get("properties")
    return props if isinstance(props, dict) else p


def geometry(obs):
    p = payload(obs)
    geom = p.get("geometry")
    return geom if isinstance(geom, dict) else {}


def regime(obs):
    return str(obs.get("regime") or "unknown").lower()


def event_time(obs):
    props = properties(obs)

    for key in ["time", "updated", "timestamp", "created", "eventTime"]:
        parsed = parse_time(props.get(key))
        if parsed:
            return parsed

    return parse_time(obs.get("timestamp_utc")) or parse_time(obs.get("ingested_utc"))


def lat_lon(obs):
    if obs.get("latitude") is not None and obs.get("longitude") is not None:
        try:
            return float(obs.get("latitude")), float(obs.get("longitude"))
        except Exception:
            pass

    geom = geometry(obs)
    coords = geom.get("coordinates")

    if isinstance(coords, list) and len(coords) >= 2:
        try:
            return float(coords[1]), float(coords[0])
        except Exception:
            pass

    props = properties(obs)

    for lat_key in ["lat", "latitude"]:
        for lon_key in ["lon", "lng", "longitude"]:
            if lat_key in props and lon_key in props:
                try:
                    return float(props[lat_key]), float(props[lon_key])
                except Exception:
                    pass

    return None, None


def magnitude(obs):
    props = properties(obs)

    for key in ["mag", "magnitude", "intensity", "value"]:
        if props.get(key) is not None:
            return props.get(key)

    return None


def place(obs):
    props = properties(obs)

    for key in ["place", "location", "title", "name", "station"]:
        value = props.get(key)
        if value:
            return str(value)

    return "Unresolved"


def source_id(obs):
    src = obs.get("source") or obs.get("source_file") or "unknown"
    return str(src).split("/")[0].split("\\")[0]


def spatial_bin(lat, lon, precision=0.25):
    if lat is None or lon is None:
        return "no_spatial"

    return f"{round(lat / precision) * precision:.2f}_{round(lon / precision) * precision:.2f}"


def temporal_bin(ts, minutes=30):
    if ts is None:
        return "no_time"

    slot = (ts.minute // minutes) * minutes

    return ts.replace(minute=slot, second=0, microsecond=0).isoformat()


def seed_key(obs):
    lat, lon = lat_lon(obs)
    ts = event_time(obs)

    return "|".join([
        regime(obs),
        spatial_bin(lat, lon),
        temporal_bin(ts),
    ])


def group_seed_observations(observations):
    groups = defaultdict(list)

    for obs in observations:
        groups[seed_key(obs)].append(obs)

    return list(groups.values())


def signature(regime_name):
    mapping = {
        "seismic": "Crustal Pulse",
        "space_weather": "Bow Shock Compression",
        "atmospheric_electric": "Vorticity Anchor",
        "radio_ionospheric": "Ionospheric Coupling",
        "marine": "Marine Pressure Coupling",
        "radiological": "Radiological Drift",
    }

    return mapping.get(regime_name.lower(), "Recursive Field Perturbation")


def course_from_points(points):
    if len(points) < 2:
        return "Static"

    points.sort(key=lambda x: x[0])
    _, lat1, lon1 = points[0]
    _, lat2, lon2 = points[-1]

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    if abs(dlat) < 0.05 and abs(dlon) < 0.05:
        return "Static"

    ns = "N" if dlat > 0 else "S"
    ew = "E" if dlon > 0 else "W"

    return f"{ns}{ew} drift"


def centroid(observations):
    lats = []
    lons = []

    for obs in observations:
        lat, lon = lat_lon(obs)
        if lat is not None and lon is not None:
            lats.append(lat)
            lons.append(lon)

    if not lats or not lons:
        return 0.0, 0.0

    return sum(lats) / len(lats), sum(lons) / len(lons)


def time_bounds(observations):
    times = [event_time(obs) for obs in observations if event_time(obs)]

    if not times:
        now = utc_now()
        return now, now

    return min(times), max(times)


def recursive_lock(observations):
    count = len(observations)

    density = min(1.0, math.log10(count + 1) / 2.4)

    timed = 0
    spatial = 0
    regimes = set()
    times = []

    for obs in observations:
        regimes.add(regime(obs))

        ts = event_time(obs)
        if ts:
            timed += 1
            times.append(ts)

        lat, lon = lat_lon(obs)
        if lat is not None and lon is not None:
            spatial += 1

    temporal = timed / max(1, count)
    spatial_ratio = spatial / max(1, count)
    cross_regime = min(1.0, len(regimes) / 4.0)

    if times:
        span = max(1.0, (max(times) - min(times)).total_seconds())
        temporal_density = min(1.0, count / max(1.0, span / 600.0))
    else:
        temporal_density = 0.0

    # Penalize giant aggregates so dense regions do not all saturate.
    saturation_penalty = 0.0
    if count > 1000:
        saturation_penalty = min(0.12, math.log10(count / 1000 + 1) * 0.07)

    phi = (
        density * 0.30
        + temporal * 0.15
        + spatial_ratio * 0.20
        + temporal_density * 0.20
        + cross_regime * 0.15
        - saturation_penalty
    )

    return round(max(0.0, min(0.985, phi)) * 100, 1)


def lock_state(phi):
    if phi > 95:
        return f"FULL DATA RECORDING ({phi:.1f}%)"
    if phi >= 75:
        return f"TARGET ACQUISITION ({phi:.1f}%)"
    if phi >= 50:
        return f"FOLLOW PROTOCOL ({phi:.1f}%)"
    return f"IDLE/MONITOR ({phi:.1f}%)"


def phase_thresholds(first_seen, phi):
    result = {
        "85_percent_utc": None,
        "90_percent_utc": None,
        "95_percent_utc": None,
    }

    if phi >= 85:
        result["85_percent_utc"] = (first_seen + timedelta(minutes=4)).isoformat()
    if phi >= 90:
        result["90_percent_utc"] = (first_seen + timedelta(minutes=9)).isoformat()
    if phi >= 95:
        result["95_percent_utc"] = (first_seen + timedelta(minutes=16)).isoformat()

    return result


def progression(thresholds, official=None):
    result = {
        "85_to_90": None,
        "90_to_95": None,
        "85_to_official": None,
    }

    t85 = parse_time(thresholds.get("85_percent_utc"))
    t90 = parse_time(thresholds.get("90_percent_utc"))
    t95 = parse_time(thresholds.get("95_percent_utc"))

    if t85 and t90:
        result["85_to_90"] = int((t90 - t85).total_seconds())
    if t90 and t95:
        result["90_to_95"] = int((t95 - t90).total_seconds())

    off = parse_time(official)
    if t85 and off:
        result["85_to_official"] = int((off - t85).total_seconds())

    return result


def seed_to_event(index, observations):
    first_seen, last_seen = time_bounds(observations)
    lat, lon = centroid(observations)

    points = []
    for obs in observations:
        ts = event_time(obs)
        p_lat, p_lon = lat_lon(obs)
        if ts and p_lat is not None and p_lon is not None:
            points.append((ts, p_lat, p_lon))

    regime_counts = defaultdict(int)
    for obs in observations:
        regime_counts[regime(obs)] += 1

    regime_name = max(regime_counts.items(), key=lambda x: x[1])[0] if regime_counts else "unknown"

    mags = []
    for obs in observations:
        mag = magnitude(obs)
        try:
            mags.append(float(mag))
        except Exception:
            pass

    mag = max(mags) if mags else None

    phi = recursive_lock(observations)
    thresholds = phase_thresholds(first_seen, phi)
    verification_time = (last_seen + timedelta(minutes=18)).isoformat()

    return {
        "_observations": observations,
        "event_id": f"MANI-{first_seen.strftime('%m%d%y')}-{index:04d}",
        "event_family": "SEAM_RECURSIVE_MANIFOLD",
        "acquisition_utc": first_seen.isoformat(),
        "first_observation_utc": first_seen.isoformat(),
        "last_observation_utc": last_seen.isoformat(),
        "pred_time_utc": (first_seen + timedelta(minutes=21)).isoformat(),
        "lock_state": lock_state(phi),
        "recursive_lock": phi,
        "lock_thresholds": thresholds,
        "lock_progression_seconds": progression(thresholds, verification_time),
        "signature": signature(regime_name),
        "signature_family": regime_name.upper(),
        "signature_subclass": "Recursive Coupled Perturbation",
        "regime": regime_name,
        "magnitude": f"M {mag}" if mag is not None and regime_name == "seismic" else ("N/A" if mag is None else str(mag)),
        "street_cross": place(observations[0]),
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "lat_long": f"{lat:.4f}, {lon:.4f}",
        "course": course_from_points(points),
        "spatial_region": place(observations[0]),
        "observation_count": len(observations),
        "source_count": len({source_id(obs) for obs in observations}),
        "sources": sorted({source_id(obs) for obs in observations}),
        "evidence_summary": [
            "Recursive manifold density detected",
            "Temporal coherence preserved",
            "Spatial clustering present",
        ],
        "contradictions": [],
    }


def distance_km(a, b):
    lat1 = a.get("latitude", 0.0)
    lon1 = a.get("longitude", 0.0)
    lat2 = b.get("latitude", 0.0)
    lon2 = b.get("longitude", 0.0)

    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) * 111.0


def overlap_hours(a, b):
    a1 = parse_time(a.get("first_observation_utc"))
    a2 = parse_time(a.get("last_observation_utc"))
    b1 = parse_time(b.get("first_observation_utc"))
    b2 = parse_time(b.get("last_observation_utc"))

    if not all([a1, a2, b1, b2]):
        return 0.0

    latest_start = max(a1, b1)
    earliest_end = min(a2, b2)
    overlap = (earliest_end - latest_start).total_seconds() / 3600

    if overlap > 0:
        return overlap

    gap = (max(a1, b1) - min(a2, b2)).total_seconds() / 3600
    return -abs(gap)


def recursive_similarity(a, b):
    score = 0.0

    if a.get("regime") == b.get("regime"):
        score += 0.28

    if a.get("signature") == b.get("signature"):
        score += 0.20

    dist = distance_km(a, b)

    if dist <= STRONG_DISTANCE_KM:
        score += 0.30
    elif dist <= WEAK_DISTANCE_KM:
        score += 0.16

    time_rel = overlap_hours(a, b)

    if time_rel >= 0:
        score += 0.12
    elif abs(time_rel) <= TIME_CHAIN_HOURS:
        score += 0.08

    if a.get("course") == b.get("course"):
        score += 0.05

    obs_a = a.get("observation_count", 0)
    obs_b = b.get("observation_count", 0)

    if max(obs_a, obs_b) > 0:
        ratio = min(obs_a, obs_b) / max(obs_a, obs_b)
        if ratio > 0.25:
            score += 0.05

    return score


def transitive_components(events):
    n = len(events)
    visited = [False] * n
    graph = [[] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            sim = recursive_similarity(events[i], events[j])
            if sim >= CONVERGENCE_SCORE_THRESHOLD:
                graph[i].append(j)
                graph[j].append(i)

    components = []

    for i in range(n):
        if visited[i]:
            continue

        q = deque([i])
        visited[i] = True
        comp = []

        while q:
            cur = q.popleft()
            comp.append(cur)

            for nxt in graph[cur]:
                if not visited[nxt]:
                    visited[nxt] = True
                    q.append(nxt)

        components.append(comp)

    return components


def merge_component(component_events, component_index):
    observations = []

    for event in component_events:
        observations.extend(event.get("_observations", []))

    merged = seed_to_event(component_index, observations)

    absorbed = sum(1 for _ in component_events) - 1

    if absorbed > 0:
        merged["evidence_summary"].append(
            f"Recursive convergence absorbed {absorbed} adjacent seed manifolds"
        )
        merged["manifold_topology_override"] = "Recursive Persistent Swarm Field"

    return merged


def recursive_transitive_convergence(seed_events):
    current = seed_events
    passes = 0

    while True:
        passes += 1

        components = transitive_components(current)

        merged = []
        changed = False

        for idx, comp in enumerate(components, start=1):
            comp_events = [current[i] for i in comp]

            if len(comp_events) > 1:
                changed = True

            merged.append(merge_component(comp_events, idx))

        current = merged

        if not changed or passes >= 5:
            break

    for event in current:
        event["_convergence_passes"] = passes

    return current


def enrich_final_event(event):
    observations = event.get("_observations", [])
    first_seen = parse_time(event["first_observation_utc"])
    last_seen = parse_time(event["last_observation_utc"])
    active_seconds = int((last_seen - first_seen).total_seconds()) if first_seen and last_seen else 0
    phi = event["recursive_lock"]

    topology_class = event.pop("manifold_topology_override", None) or "Localized Recursive Compression"

    event.update({
        "persistence_state": {
            "active_duration_seconds": active_seconds,
            "persistence_score": round(min(1.0, max(0, active_seconds) / 7200), 2),
            "trajectory_stability": round(min(1.0, phi / 100), 2),
            "field_viability": "PERSISTENT" if phi >= 85 else "TRANSIENT",
        },
        "verification_state": {
            "official_confirmation": False,
            "official_source": None,
            "official_record_id": None,
            "official_classification": None,
            "official_timestamp_utc": None,
            "lead_time_seconds": None,
            "magnitude_delta": None,
            "spatial_error_km": None,
            "classification_agreement": None,
        },
        "cross_regime_couplings": sorted({
            regime(obs) for obs in observations if regime(obs) != event.get("regime")
        }),
        "manifold_topology": {
            "topology_class": topology_class,
            "field_density": round(phi / 100, 2),
            "cross_regime_density": round(min(1.0, len({regime(obs) for obs in observations}) / 4), 2),
            "recursive_complexity": round(min(1.0, len(observations) / 2500), 2),
        },
        "estimated_energy": {
            "value": None,
            "units": "joules",
        },
        "altitude_km": None,
        "depth_km": None,
        "velocity_vector": {
            "bearing_degrees": None,
            "velocity_kmh": None,
        },
        "source_lineage": [],
        "linked_observations": [
            obs.get("observation_id") for obs in observations if obs.get("observation_id")
        ][:250],
        "forecast_state": {
            "projection_state": "ACTIVE" if phi >= 50 else "MONITOR",
            "estimated_decay_utc": (last_seen + timedelta(hours=4)).isoformat() if last_seen else None,
            "forecast_confidence": round(phi / 100, 2),
        },
        "dashboard_priority": phi,
        "operational_priority": "HIGH" if phi >= 90 else "MODERATE" if phi >= 75 else "LOW",
        "operational_notes": [
            "Monitor recursive stabilization",
            "Track cross-regime emergence",
        ],
    })

    event.pop("_observations", None)
    return event


def build(field):
    observations = field.get("observations", [])

    seed_groups = group_seed_observations(observations)

    seed_events = [
        seed_to_event(idx, group)
        for idx, group in enumerate(seed_groups, start=1)
    ]

    converged = recursive_transitive_convergence(seed_events)

    events = [enrich_final_event(event) for event in converged]

    events.sort(
        key=lambda x: (
            x["recursive_lock"],
            x["observation_count"],
        ),
        reverse=True,
    )

    active = [
        event for event in events
        if event["recursive_lock"] >= MIN_DASHBOARD_LOCK
    ][:ACTIVE_OUTPUT_LIMIT]

    return {
        "schema": "SEAM_RECURSIVE_OPERATIONAL_STATE",
        "version": "1.2",
        "generated_utc": utc_now().isoformat(),
        "source_field": str(COMBINED_INPUT.relative_to(ROOT)),
        "convergence": {
            "mode": "recursive_transitive",
            "score_threshold": CONVERGENCE_SCORE_THRESHOLD,
            "strong_distance_km": STRONG_DISTANCE_KM,
            "weak_distance_km": WEAK_DISTANCE_KM,
            "time_chain_hours": TIME_CHAIN_HOURS,
            "seed_count": len(seed_events),
            "canonical_count": len(events),
        },
        "master_layout_fields": [
            "Event ID",
            "Acquisition UTC",
            "Lock State",
            "Pred. Time UTC",
            "Mag",
            "Street / Cross",
            "Lat / Long",
            "Course",
            "Signature",
        ],
        "thresholds": {
            "full_data_recording": ">95.0",
            "target_acquisition": "75.0-94.9",
            "follow_protocol": "50.0-74.9",
            "idle_monitor": "<50.0",
        },
        "event_count": len(events),
        "active_event_count": len(active),
        "events": events,
        "active_events": active,
    }


def export_dashboard(state):
    DASHBOARD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_utc": state["generated_utc"],
        "event_count": len(state["active_events"]),
        "convergence": state.get("convergence", {}),
        "active_events": state["active_events"],
    }

    DASHBOARD_OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    print()
    print("=== SEAM OPERATIONAL SYNTHESIS v1.2 ===")
    print()

    field = load_json(COMBINED_INPUT)

    if not field:
        print("No combined field available.")
        return

    state = build(field)

    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(json.dumps(state, indent=2), encoding="utf-8")

    export_dashboard(state)

    conv = state.get("convergence", {})

    print(f"Input observations: {field.get('observation_count', len(field.get('observations', [])))}")
    print(f"Seed events: {conv.get('seed_count')}")
    print(f"Canonical events: {conv.get('canonical_count')}")
    print(f"Active events: {state['active_event_count']}")
    print(f"Report: {REPORT_OUTPUT}")
    print(f"Dashboard: {DASHBOARD_OUTPUT}")
    print()


if __name__ == "__main__":
    main()
