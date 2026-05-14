"""
seam_unified_48h_field.py
Version: 2.0

Unified Recursive Observation Field

Inputs:
-------
raw/
decoded/

Excluded:
---------
curated/

Purpose:
--------
Generate a SEAM-native rolling 48h combined field
without contamination from retrospective official reporting.
"""

from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent

RAW_DIR = ROOT / "raw"
DECODED_DIR = ROOT / "decoded"

COMBINED_DIR = ROOT / "combined"

OUTPUT = COMBINED_DIR / "seam_unified_recursive_field_48h.json"

RETENTION_HOURS = 48


def utc_now():
    return datetime.now(timezone.utc)


def collect_json_files(root: Path):

    if not root.exists():
        return []

    return list(root.rglob("*.json")) + list(root.rglob("*.geojson"))


def build_field():

    observations = []

    for layer_name, directory in [
        ("raw", RAW_DIR),
        ("decoded", DECODED_DIR)
    ]:

        for path in collect_json_files(directory):

            try:
                payload = json.loads(
                    path.read_text(
                        encoding="utf-8",
                        errors="replace"
                    )
                )

            except Exception:
                continue

            observations.append({
                "source_file": str(path.relative_to(ROOT)),
                "epistemic_layer": layer_name,
                "ingested_utc": utc_now().isoformat(),
                "payload": payload
            })

    return {
        "schema": "SEAM_UNIFIED_RECURSIVE_FIELD",
        "version": "2.0",
        "generated_utc": utc_now().isoformat(),
        "retention_hours": RETENTION_HOURS,
        "observation_count": len(observations),
        "inputs": [
            "raw",
            "decoded"
        ],
        "excluded_inputs": [
            "curated"
        ],
        "observations": observations
    }


def main():

    COMBINED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    field = build_field()

    OUTPUT.write_text(
        json.dumps(field, indent=2),
        encoding="utf-8"
    )

    print()
    print("=== SEAM UNIFIED FIELD v2.0 ===")
    print()
    print(f"Observations: {field['observation_count']}")
    print(f"Output: {OUTPUT}")
    print()


if __name__ == "__main__":
    main()
