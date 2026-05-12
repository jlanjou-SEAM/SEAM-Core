import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COLLECTORS = [
    ("usgs", "collect_usgs_feeds"),
    ("emsc", "collect_emsc_feeds"),
    ("noaa", "collect_noaa_feeds"),
]

def count_records(payload: Any) -> int:
    if isinstance(payload, list):
        total = 0
        for item in payload:
            if isinstance(item, dict):
                total += len(item.get("events", []))
                total += len(item.get("records", []))
            else:
                total += 1
        return total

    if isinstance(payload, dict):
        return len(payload.get("events", [])) + len(payload.get("records", []))

    return 0

def run_once(record_target: int) -> dict:
    print("[BOOT] SEAM finite bootstrap started", flush=True)
    print(f"[BOOT] target records per source: {record_target}", flush=True)

    source_results = []
    total_records = 0

    for module_name, function_name in COLLECTORS:
        print(f"[BOOT] testing collector {module_name}.{function_name}", flush=True)

        try:
            module = importlib.import_module(module_name)
            collector = getattr(module, function_name)
            payload = collector()

            records = count_records(payload)
            total_records += records

            source_results.append({
                "collector": module_name,
                "function": function_name,
                "status": "ok",
                "records": records
            })

            print(f"[BOOT] {module_name} ok records={records}", flush=True)

        except Exception as exc:
            source_results.append({
                "collector": module_name,
                "function": function_name,
                "status": "error",
                "error": str(exc),
                "records": 0
            })

            print(f"[BOOT] {module_name} failed: {exc}", flush=True)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "finite_bootstrap",
        "record_target_per_source": record_target,
        "source_results": source_results,
        "total_records": total_records
    }

    Path("logs").mkdir(exist_ok=True)
    Path("logs/bootstrap_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not Path("latest.json").exists():
        Path("latest.json").write_text(json.dumps({
            "timestamp_utc": report["timestamp_utc"],
            "active_events": [],
            "bootstrap_report": report
        }, indent=2), encoding="utf-8")

    print("[BOOT] finite bootstrap complete", flush=True)
    print("[BOOT] report written to logs/bootstrap_report.json", flush=True)
    return report

def main():
    parser = argparse.ArgumentParser(description="SEAM finite bootstrap runner")
    parser.add_argument("--record-target", type=int, default=5000)
    args = parser.parse_args()
    run_once(args.record_target)

if __name__ == "__main__":
    main()
