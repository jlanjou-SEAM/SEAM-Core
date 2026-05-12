from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

SOURCE = "Safecast"
COLLECTOR = "safecast"

record = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "stream": SOURCE,
    "record_id": str(uuid.uuid4()),
    "metadata": {
        "collector": COLLECTOR,
        "mode": "raw_append_only",
        "classification": False,
        "inference": False
    },
    "payload": {
        "sample": "latest_observation",
        "raw": True
    }
}

Path("data/source_logs").mkdir(parents=True, exist_ok=True)

path = Path(f"data/source_logs/{SOURCE.lower()}.ndjson")

with path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\\n")

print(f"[SEAM] appended raw sample from {SOURCE}")
