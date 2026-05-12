from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json
import math
import hashlib

SOURCE_LOG_DIR = Path("data/source_logs")
ANALYSIS_DIR = Path("data/analysis")
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_REGISTRY = ANALYSIS_DIR / "target_registry.json"

STREAM_TARGET_MAP = {
    "USGS": ("Global Seismic Fabric", 19.4, -155.2),
    "EMSC": ("Global Seismic Fabric", 35.7, 140.2),
    "IRIS": ("Global Seismic Fabric", 44.1, -123.9),

    "NOAA_SWPC": ("Solar-Geospace Envelope", 0.0, 0.0),
    "GOES": ("Solar-Geospace Envelope", 0.0, 0.0),
    "StanfordSID": ("Solar-Geospace Envelope", 37.4, -122.1),

    "KiwiSDR": ("RF Spectral Mesh", 34.1, -117.8),
    "WebSDR": ("RF Spectral Mesh", 52.1, 5.1),
    "ReverseBeaconNetwork": ("RF Spectral Mesh", 40.0, -74.0),

    "LOFAR": ("Radio Astronomy Spectral Array", 52.9, 6.9),
    "VLA": ("Radio Astronomy Spectral Array", 34.1, -107.6),

    "Blitzortung": ("Atmospheric Electrical Grid", 29.8, -95.3),
    "LightningMaps": ("Atmospheric Electrical Grid", 35.0, -97.0),

    "OpenSky": ("Transit Observation Mesh", 51.5, -0.1),
    "ADSBExchange": ("Transit Observation Mesh", 33.9, -118.4),

    "Safecast": ("Environmental Observation Grid", 37.7, 140.4),

    "NOAA_Buoys": ("Marine-Oceanic Sensor Field", 21.3, -157.8),
    "ARGO": ("Marine-Oceanic Sensor Field", -14.2, -170.1)
}

def utc_now():
    return datetime.now(timezone.utc)

def load_registry():
    if not TARGET_REGISTRY.exists():
        return {"targets": []}

    try:
        return json.loads(TARGET_REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {"targets": []}

def save_registry(registry):
    TARGET_REGISTRY.write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8"
    )

def read_stream_records():
    records_by_target = defaultdict(list)

    for path in SOURCE_LOG_DIR.glob("*.ndjson"):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except Exception:
                continue

            stream = record.get("stream") or path.stem

            target_info = STREAM_TARGET_MAP.get(stream)

            if not target_info:
                continue

            target_name = target_info[0]
            records_by_target[target_name].append(record)

    return records_by_target

def generate_signature(name):
    return hashlib.sha1(name.encode()).hexdigest()[:16].upper()

def calculate_probability(count, stream_count, previous_probability=0.25):
    probability = min(
        0.18 + math.log1p(count) * 0.10 + stream_count * 0.045,
        0.97
    )

    return round((probability * 0.65) + (previous_probability * 0.35), 4)

def determine_state(probability):
    if probability >= 0.80:
        return "CRITICAL"
    if probability >= 0.65:
        return "TARGET"
    if probability >= 0.45:
        return "FOLLOW"
    return "MONITOR"

def synthesize_targets():
    registry = load_registry()
    previous = {
        target["target_signature"]: target
        for target in registry.get("targets", [])
    }

    records_by_target = read_stream_records()

    active_targets = []

    for target_name, records in records_by_target.items():
        streams = sorted(set(
            record.get("stream", "unknown")
            for record in records
        ))

        stream_count = len(streams)
        count = len(records)

        latitudes = []
        longitudes = []

        for stream in streams:
            info = STREAM_TARGET_MAP.get(stream)

            if info:
                latitudes.append(info[1])
                longitudes.append(info[2])

        centroid_lat = round(sum(latitudes) / max(len(latitudes), 1), 4)
        centroid_lon = round(sum(longitudes) / max(len(longitudes), 1), 4)

        signature = generate_signature(target_name)

        prior = previous.get(signature)

        if prior:
            initial_lock = prior["initial_lock_timestamp_utc"]
            persistence_cycles = prior.get("persistence_cycles", 0) + 1
            previous_probability = prior.get("event_probability", 0.25)
        else:
            initial_lock = utc_now().isoformat()
            persistence_cycles = 1
            previous_probability = 0.25

        probability = calculate_probability(
            count,
            stream_count,
            previous_probability
        )

        coherence_score = round(
            min((stream_count * 0.12) + (count * 0.0025), 0.96),
            4
        )

        lock_confidence = round(
            min((probability * 0.72) + (coherence_score * 0.28), 0.97),
            4
        )

        now = utc_now()

        eta_start = now + timedelta(hours=max(1, 12 - stream_count))
        eta_end = eta_start + timedelta(hours=24)

        target = {
            "target_signature": signature,
            "state": determine_state(probability),
            "region": target_name,
            "target_lat": centroid_lat,
            "target_lon": centroid_lon,
            "initial_lock_timestamp_utc": initial_lock,
            "last_update_utc": now.isoformat(),
            "lock_age_seconds": int(
                (now - datetime.fromisoformat(initial_lock)).total_seconds()
            ),
            "persistence_cycles": persistence_cycles,
            "event_probability": probability,
            "realization_probability": probability,
            "lock_confidence": lock_confidence,
            "coherence_score": coherence_score,
            "eta_window_start_utc": eta_start.isoformat(),
            "eta_window_end_utc": eta_end.isoformat(),
            "trajectory_vector": f"{stream_count * 3} km/hr inferred drift",
            "source_intersections": stream_count,
            "sources": streams,
            "observation_count": count,
            "hypothesis": "SEAM recursive analysis over raw retrieval streams",
            "evidence": [
                f"{count} accumulated raw observations",
                f"{stream_count} intersecting retrieval streams",
                f"{persistence_cycles} persistence cycles"
            ],
            "contradictions": []
        }

        active_targets.append(target)

    active_targets = sorted(
        active_targets,
        key=lambda t: t["event_probability"],
        reverse=True
    )

    snapshot = {
        "timestamp_utc": utc_now().isoformat(),
        "schema": "SEAM.analysis.v2",
        "active_events": active_targets
    }

    save_registry({
        "timestamp_utc": snapshot["timestamp_utc"],
        "targets": active_targets
    })

    Path("latest.json").write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8"
    )

    Path("active_events.json").write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8"
    )

    print(f"[SEAM] persistent registry updated with {len(active_targets)} targets")

if __name__ == "__main__":
    synthesize_targets()
