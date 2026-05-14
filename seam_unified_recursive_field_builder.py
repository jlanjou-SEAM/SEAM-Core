"""
SEAM Unified Recursive Field Builder v2.0
Canonical filename:
    seam_unified_recursive_field_builder.py

Purpose:
--------
Read raw/ and decoded/ only.
Recursively extract observations inside acquired files.
Write combined/seam_unified_recursive_field_48h.json

Critical:
---------
Do not read curated/, combined/, reports/, data/, logs/, state/, archive/.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

RAW_DIR = ROOT / "raw"
DECODED_DIR = ROOT / "decoded"
OUTPUT = ROOT / "combined" / "seam_unified_recursive_field_48h.json"

VALID_EXT = {".json", ".geojson"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def normalize_record(record, source_file: Path, layer: str):
    if not isinstance(record, dict):
        return None

    # Preserve the original object as payload, but expose basic metadata.
    return {
        "observation_id": None,
        "source_file": str(source_file.relative_to(ROOT)),
        "source": source_file.parts[-3] if len(source_file.parts) >= 3 else source_file.parent.name,
        "epistemic_layer": layer,
        "regime": infer_regime(record, source_file),
        "ingested_utc": utc_now(),
        "payload": record,
    }


def infer_regime(record, source_file: Path):
    text = (str(source_file) + " " + json.dumps(record, default=str)[:2000]).lower()

    if any(k in text for k in ["earthquake", "quake", '"mag"', "seismic", "usgs", "emsc"]):
        return "seismic"
    if any(k in text for k in ["radiation", "radiological", "safecast", "cpm", "dose"]):
        return "radiological"
    if any(k in text for k in ["xray", "solar", "goes", "kp", "geomagnetic", "swpc"]):
        return "space_weather"
    if any(k in text for k in ["ionosphere", "hamsci", "madrigal", "radio"]):
        return "radio_ionospheric"
    if any(k in text for k in ["marine", "ocean", "buoy", "argo"]):
        return "marine"
    if any(k in text for k in ["storm", "wind", "lightning", "weather", "nexrad"]):
        return "atmospheric_electric"

    return "unknown"


def recurse_extract(node, source_file: Path, layer: str, out: list):
    if node is None:
        return

    if isinstance(node, dict):
        if node.get("type") == "FeatureCollection" and isinstance(node.get("features"), list):
            for feat in node["features"]:
                recurse_extract(feat, source_file, layer, out)
            return

        if node.get("type") == "Feature":
            rec = normalize_record(node, source_file, layer)
            if rec:
                rec["observation_id"] = f"OBS-{len(out):08d}"
                out.append(rec)
            return

        for key in [
            "features", "entries", "events", "observations", "stations",
            "records", "items", "data", "results", "measurements", "samples"
        ]:
            value = node.get(key)
            if isinstance(value, list):
                for item in value:
                    recurse_extract(item, source_file, layer, out)
                return

        # Treat remaining dict as a record if it has useful structure.
        if len(node) >= 2:
            rec = normalize_record(node, source_file, layer)
            if rec:
                rec["observation_id"] = f"OBS-{len(out):08d}"
                out.append(rec)
        return

    if isinstance(node, list):
        for item in node:
            recurse_extract(item, source_file, layer, out)


def extract_file(path: Path, layer: str):
    payload = load_json(path)
    if payload is None:
        return []

    observations = []
    recurse_extract(payload, path, layer, observations)
    return observations


def collect_files(folder: Path):
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in VALID_EXT
    )


def main():
    print()
    print("=== SEAM UNIFIED FIELD v2.0 ===")
    print()

    raw_files = collect_files(RAW_DIR)
    decoded_files = collect_files(DECODED_DIR)

    observations = []
    for file in raw_files:
        observations.extend(extract_file(file, "raw"))
    for file in decoded_files:
        observations.extend(extract_file(file, "decoded"))

    # Renumber globally after combined extraction.
    for i, obs in enumerate(observations):
        obs["observation_id"] = f"OBS-{i:08d}"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    field = {
        "schema": "SEAM_UNIFIED_RECURSIVE_FIELD",
        "version": "2.0",
        "generated_utc": utc_now(),
        "input_layers": ["raw", "decoded"],
        "excluded_layers": ["curated", "combined", "reports", "data", "logs", "state", "archive"],
        "raw_file_count": len(raw_files),
        "decoded_file_count": len(decoded_files),
        "observation_count": len(observations),
        "observations": observations,
    }

    OUTPUT.write_text(json.dumps(field, indent=2), encoding="utf-8")

    print(f"RAW files: {len(raw_files)}")
    print(f"DECODED files: {len(decoded_files)}")
    print(f"Observations: {len(observations)}")
    print(f"Output: {OUTPUT}")
    print()


if __name__ == "__main__":
    main()
