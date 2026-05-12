import json
from pathlib import Path
from datetime import datetime, UTC, timedelta

ROOT = Path(__file__).resolve().parent

STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

HEALTH = STATE / "source_health.json"

QUARANTINE_MINUTES = 360

def now():
    return datetime.now(UTC)

def quarantine(name, reason):

    data = {}

    if HEALTH.exists():

        try:

            with open(HEALTH, "r", encoding="utf-8") as f:
                data = json.load(f)

        except Exception:
            data = {}

    data[name] = {
        "state": "QUARANTINED",
        "reason": reason,
        "retry_after_utc": (
            now() +
            timedelta(
                minutes=QUARANTINE_MINUTES
            )
        ).isoformat()
    }

    with open(HEALTH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

print()
print("=== CLEAN-ROOM SOURCE QUARANTINE ===")
print()
print(f"Quarantine window: {QUARANTINE_MINUTES} min")
print()
