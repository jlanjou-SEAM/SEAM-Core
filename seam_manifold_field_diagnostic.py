"""
seam_manifold_field_diagnostic.py

Purpose:
--------
Inspect actual manifold-related fields coming from:
- reports/live_event_state.json

Goal:
-----
Determine which field truly contains:
- manifold lock
- recursive lock probability
- convergence score

Outputs:
--------
- field_frequency_report.json
- field_value_samples.json
- console summary
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

INPUT_PATH = ROOT / "reports" / "live_event_state.json"

FREQ_OUTPUT = ROOT / "reports" / "field_frequency_report.json"
SAMPLE_OUTPUT = ROOT / "reports" / "field_value_samples.json"


TARGET_FIELDS = [
    "manifold_lock",
    "manifold_lock_percentage",
    "lock_percentage",
    "seam_phi",
    "forecast_confidence",
    "lock_state",
    "verification_state",
    "source_count",
    "observation_count",
]


def load_payload():

    if not INPUT_PATH.exists():
        print(f"[ERROR] Missing input: {INPUT_PATH}")
        return {}

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def inspect_events(events):

    field_counts = Counter()

    samples = defaultdict(list)

    unique_values = defaultdict(set)

    for event in events:

        for field in TARGET_FIELDS:

            if field in event:

                value = event.get(field)

                field_counts[field] += 1

                if len(samples[field]) < 20:
                    samples[field].append(value)

                try:
                    unique_values[field].add(str(value))
                except Exception:
                    pass

    summary = {}

    for field in TARGET_FIELDS:

        summary[field] = {
            "present_count": field_counts[field],
            "unique_values": len(unique_values[field]),
            "sample_values": samples[field][:10]
        }

    return summary


def main():

    payload = load_payload()

    events = payload.get("events", [])

    print()
    print("=== SEAM MANIFOLD FIELD DIAGNOSTIC ===")
    print()

    print(f"Events loaded: {len(events)}")
    print()

    summary = inspect_events(events)

    for field, data in summary.items():

        print(f"{field}")
        print(f"  present_count : {data['present_count']}")
        print(f"  unique_values : {data['unique_values']}")
        print(f"  sample_values : {data['sample_values']}")
        print()

    with open(FREQ_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(SAMPLE_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Frequency report: {FREQ_OUTPUT}")
    print(f"Sample report: {SAMPLE_OUTPUT}")
    print()


if __name__ == "__main__":
    main()
