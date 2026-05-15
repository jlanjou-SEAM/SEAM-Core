"""
SEAM Unified Recursive Field Builder v2.1
Persistent Semantic Continuity Upgrade
"""

import json
from pathlib import Path

ROLLING_LEDGER = Path(
    "combined/seam_semantic_continuum_48h.json"
)


def load_existing_ledger():

    if not ROLLING_LEDGER.exists():
        return []

    try:
        return json.loads(
            ROLLING_LEDGER.read_text(encoding="utf-8")
        )
    except Exception:
        return []


def persist_semantic_continuity(events):

    ledger = load_existing_ledger()

    existing = {
        e.get("event_id"): e
        for e in ledger
    }

    for event in events:

        eid = event.get("event_id")

        if not eid:
            continue

        if eid in existing:

            old = existing[eid]

            history = old.get(
                "classification_history",
                []
            )

            history.extend(
                event.get(
                    "classification_history",
                    []
                )
            )

            event["classification_history"] = history

        existing[eid] = event

    final = list(existing.values())

    ROLLING_LEDGER.write_text(
        json.dumps(final, indent=2),
        encoding="utf-8"
    )

    return final
