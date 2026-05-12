from pathlib import Path
from datetime import datetime, timezone
import json

SOURCE = "NOAA_SWPC"

record = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE,
    "payload": {
        "sample": "latest_observation"
    }
}

Path("data/source_logs").mkdir(parents=True, exist_ok=True)

path = Path("data/source_logs/noaa_swpc.ndjson")

with path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")

print(f"[SEAM] sampled NOAA_SWPC")
