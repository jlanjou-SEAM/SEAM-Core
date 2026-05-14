"""
SEAM UNIFIED RECURSIVE FIELD BUILDER v2.0

Critical Fix:
-------------
Restores recursive observation extraction.

Previous broken behavior:
- treated each acquired file as ONE observation

Correct behavior:
- recursively explodes:
    FeatureCollections
    arrays
    entries
    events
    station feeds
    payload lists
    nested observations

into atomic manifold observations.
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
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def normalize_record(record, source_file, layer):
    if not isinstance(record, dict):
        return None

    record["_source_file"] = str(source_file.name)
    record["_layer"] = layer
    record["_ingested_utc"] = utc_now()

    if "payload" not in record:
        record["payload"] = record.copy()

    return record

def recurse_extract(node, source_file, layer, out):

    if node is None:
        return

    # GeoJSON FeatureCollection
    if isinstance(node, dict):

        if node.get("type") == "FeatureCollection":
            for feat in node.get("features", []):
                recurse_extract(feat, source_file, layer, out)
            return

        # GeoJSON Feature
        if node.get("type") == "Feature":
            normalized = normalize_record(node, source_file, layer)
            if normalized:
                out.append(normalized)
            return

        # Generic feed arrays
        for key in [
            "features",
            "entries",
            "events",
            "observations",
            "stations",
            "records",
            "items",
            "data",
            "results"
        ]:
            value = node.get(key)

            if isinstance(value, list):
                for item in value:
                    recurse_extract(item, source_file, layer, out)
                return

        # Generic observation-like object
        if len(node.keys()) >= 2:
            normalized = normalize_record(node, source_file, layer)
            if normalized:
                out.append(normalized)

        return

    if isinstance(node, list):
        for item in node:
            recurse_extract(item, source_file, layer, out)

def extract_file(path: Path, layer):
    payload = load_json(path)

    if payload is None:
        return []

    observations = []

    recurse_extract(payload, path, layer, observations)

    return observations

def main():

    print()
    print("=== SEAM UNIFIED FIELD v2.0 ===")
    print()

    observations = []

    raw_files = []
    decoded_files = []

    if RAW_DIR.exists():
        raw_files = [
            p for p in RAW_DIR.rglob("*")
            if p.suffix.lower() in VALID_EXT
        ]

    if DECODED_DIR.exists():
        decoded_files = [
            p for p in DECODED_DIR.rglob("*")
            if p.suffix.lower() in VALID_EXT
        ]

    for file in raw_files:
        observations.extend(extract_file(file, "raw"))

    for file in decoded_files:
        observations.extend(extract_file(file, "decoded"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    field = {
        "schema": "SEAM_UNIFIED_RECURSIVE_FIELD",
        "version": "2.0",
        "generated_utc": utc_now(),
        "observation_count": len(observations),
        "raw_file_count": len(raw_files),
        "decoded_file_count": len(decoded_files),
        "observations": observations,
    }

    OUTPUT.write_text(
        json.dumps(field, indent=2),
        encoding="utf-8"
    )

    print(f"RAW files: {len(raw_files)}")
    print(f"DECODED files: {len(decoded_files)}")
    print(f"Observations: {len(observations)}")
    print(f"Output: {OUTPUT}")
    print()

if __name__ == "__main__":
    main()
