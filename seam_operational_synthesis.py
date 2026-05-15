"""
SEAM Operational Synthesis v2.0
Complete Semantic Runtime Upgrade
"""

import json
from pathlib import Path
from datetime import datetime

INPUT_FIELD = Path(
    "combined/seam_unified_recursive_field_48h.json"
)

OUTPUT_REPORT = Path(
    "reports/seam_recursive_operational_state.json"
)

OUTPUT_LATEST = Path(
    "data/latest.json"
)

SEMANTIC_LEDGER = Path(
    "combined/seam_semantic_continuum_48h.json"
)

THRESHOLDS = {
    "follow": 50,
    "target": 75,
    "full": 95
}


def load_json(path):

    if not path.exists():
        return []

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return []


def infer_traits(event):

    traits = []

    regime = event.get("regime","")

    if regime == "thermal":
        traits.extend([
            "thermal escalation",
            "fuel dehydration"
        ])

    if regime == "atmospheric_electric":
        traits.extend([
            "dry lightning potential",
            "electrical instability"
        ])

    if regime == "seismic":
        traits.extend([
            "ground coupling",
            "crustal perturbation"
        ])

    return list(set(traits))


def infer_emergence(event):

    traits = event.get("manifold_traits", [])

    emergence = []

    if "dry lightning potential" in traits:
        emergence.append({
            "classification": "Wildfire Risk",
            "confidence": 0.42
        })

    if "ground coupling" in traits:
        emergence.append({
            "classification": "Seismic Event Potential",
            "confidence": 0.58
        })

    return emergence


def infer_classification(event):

    lock = float(event.get("recursive_lock",0))

    if lock >= THRESHOLDS["full"]:
        return "Operational Event"

    if lock >= THRESHOLDS["target"]:
        return "Stabilized Precursor Ecology"

    if lock >= THRESHOLDS["follow"]:
        return "Emergent Recursive Topology"

    return None


def update_history(old_history, state, confidence):

    timestamp = datetime.utcnow().isoformat() + "Z"

    if old_history:
        last = old_history[-1]

        if last.get("state") == state:
            return old_history

    old_history.append({
        "timestamp": timestamp,
        "state": state,
        "confidence": confidence
    })

    return old_history


def enrich_event(event, ledger):

    eid = event.get("event_id")

    prior = ledger.get(eid, {})

    history = prior.get(
        "classification_history",
        []
    )

    event["manifold_traits"] = infer_traits(event)

    event["possible_emergence"] = infer_emergence(event)

    classification = infer_classification(event)

    if classification:

        confidence = round(
            float(event.get("recursive_lock",0)) / 100.0,
            2
        )

        event["classified_as"] = classification

        event["classification_confidence"] = confidence

        event["classification_history"] = update_history(
            history,
            classification,
            confidence
        )

    return event


def main():

    observations = load_json(INPUT_FIELD)

    old_ledger = load_json(SEMANTIC_LEDGER)

    ledger_index = {
        e.get("event_id"): e
        for e in old_ledger
    }

    enriched = []

    for event in observations:

        enriched.append(
            enrich_event(event, ledger_index)
        )

    SEMANTIC_LEDGER.write_text(
        json.dumps(enriched, indent=2),
        encoding="utf-8"
    )

    operational = {
        "schema": "SEAM_RECURSIVE_OPERATIONAL_STATE",
        "version": "v2.0",
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "events": enriched
    }

    latest = {
        "generated_utc": operational["generated_utc"],
        "total_predictions": len(enriched),
        "verified_predictions": 0,
        "expired_predictions": 0,
        "hit_rate": "0.0%",
        "avg_lead": "--",
        "active_events": enriched
    }

    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_LATEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_REPORT.write_text(
        json.dumps(operational, indent=2),
        encoding="utf-8"
    )

    OUTPUT_LATEST.write_text(
        json.dumps(latest, indent=2),
        encoding="utf-8"
    )

    print("\\n=== SEAM OPERATIONAL SYNTHESIS v2.0 ===\\n")
    print(f"Events: {len(enriched)}")
    print(f"Report: {OUTPUT_REPORT}")
    print(f"Dashboard: {OUTPUT_LATEST}")


if __name__ == "__main__":
    main()
