"""
continuum_dual_acquisition_runtime.py
Continuum Dual Acquisition Runtime
Version: 1.0

Purpose:
- Load config/dual_acquisition_sources.json
- Fetch all enabled configured source endpoints
- Keep live GeoJSON separate from delayed / already-analyzed reports
- Write live GeoJSON into raw/<source>/...
- Write all non-GeoJSON reports into curated/<source>/...
- Write configured secondary_curated reports into curated/<source>/...
- Preserve metadata without semantic interpretation
- Produce acquisition log and health state
- Feed downstream decoded/event/analysis stages

Classification rule:
- GeoJSON payloads are live data
- All other source reports are delayed/analyzed reports
"""

from __future__ import annotations

import concurrent.futures
import json
import mimetypes
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent

CONFIG_PATH = ROOT / "config" / "dual_acquisition_sources.json"

RAW_DIR = ROOT / "raw"
CURATED_DIR = ROOT / "curated"
LOG_DIR = ROOT / "logs"
STATE_DIR = ROOT / "state"

ACQUISITION_LOG = LOG_DIR / "acquisition_log.jsonl"
SOURCE_HEALTH = STATE_DIR / "source_health.json"

CONNECT_TIMEOUT_SECONDS = 6
MAX_WORKERS = 16
MAX_BYTES = 5_000_000

USER_AGENT = "SEAM-CleanRoom-Continuum-Acquisition/1.0"

LIVE_EXTENSIONS = {".geojson"}
JSON_EXTENSIONS = {".json", ".geojson"}

NO_VALID_ENDPOINT_ROUTINGS = {
    "awaiting_endpoint",
    "no_valid_endpoint"
}


@dataclass
class AcquisitionTask:
    source: str
    stream: str
    url: str
    configured_route: str
    source_route: str


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_stamp() -> str:
    return utc_now().strftime("%H%M%S")


def utc_date() -> str:
    return utc_now().strftime("%Y-%m-%d")


def sanitize(value: str) -> str:
    value = str(value or "unknown").strip()
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "unknown"


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing acquisition config: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def content_extension(url: str, content_type: str, payload: bytes) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()

    if suffix in JSON_EXTENSIONS:
        return suffix

    lowered_type = (content_type or "").lower()

    if "geo+json" in lowered_type or "geojson" in lowered_type:
        return ".geojson"

    if "json" in lowered_type:
        try:
            data = json.loads(payload.decode("utf-8", errors="ignore"))
            if isinstance(data, dict) and data.get("type") == "FeatureCollection":
                return ".geojson"
        except Exception:
            pass
        return ".json"

    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None

    if guessed:
        return guessed

    return ".payload"


def is_geojson_payload(url: str, content_type: str, payload: bytes) -> bool:
    ext = content_extension(url, content_type, payload)

    if ext == ".geojson":
        return True

    try:
        data = json.loads(payload.decode("utf-8", errors="ignore"))
        return isinstance(data, dict) and data.get("type") == "FeatureCollection"
    except Exception:
        return False


def wrap_non_json_payload(
    task: AcquisitionTask,
    payload: bytes,
    status: int,
    content_type: str,
    route_class: str
) -> bytes:
    wrapper = {
        "timestamp_utc": utc_now().isoformat(),
        "source": task.source,
        "stream": task.stream,
        "url": task.url,
        "route_class": route_class,
        "status": status,
        "content_type": content_type,
        "bytes": len(payload),
        "payload_text": payload.decode("utf-8", errors="replace")[:200_000]
    }

    return json.dumps(wrapper, indent=2).encode("utf-8")


def destination_for(
    task: AcquisitionTask,
    payload: bytes,
    content_type: str
) -> Tuple[Path, str, str]:
    """
    Return destination path, route class, extension.

    Rule:
    - GeoJSON is live data -> raw/<source>/...
    - Everything else is delayed/analyzed report -> curated/<source>/...
    - Explicit secondary_curated always goes to curated/<source>/...
    """

    detected_geojson = is_geojson_payload(task.url, content_type, payload)
    detected_ext = content_extension(task.url, content_type, payload)

    source_name = sanitize(task.source)
    stream_name = sanitize(task.stream)

    if task.configured_route == "secondary_curated":
        route_class = "delayed_report"
        root = CURATED_DIR
        ext = ".json" if detected_ext not in JSON_EXTENSIONS else detected_ext
        filename = f"{utc_stamp()}_{stream_name}_curated{ext}"
    elif detected_geojson:
        route_class = "live_geojson"
        root = RAW_DIR
        ext = ".geojson"
        filename = f"{utc_stamp()}_{stream_name}_live{ext}"
    else:
        route_class = "delayed_report"
        root = CURATED_DIR
        ext = ".json" if detected_ext not in JSON_EXTENSIONS else detected_ext
        filename = f"{utc_stamp()}_{stream_name}_delayed{ext}"

    return root / source_name / utc_date() / filename, route_class, ext


def append_log(record: Dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with ACQUISITION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def update_health(source: str, stream: str, ok: bool, reason: str = "") -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        health = json.loads(SOURCE_HEALTH.read_text(encoding="utf-8"))
    except Exception:
        health = {}

    key = f"{source}:{stream}"

    health[key] = {
        "source": source,
        "stream": stream,
        "ok": ok,
        "reason": reason,
        "updated_utc": utc_now().isoformat()
    }

    SOURCE_HEALTH.write_text(json.dumps(health, indent=2), encoding="utf-8")


def build_tasks(config: Dict[str, Any]) -> List[AcquisitionTask]:
    tasks: List[AcquisitionTask] = []

    for source_cfg in config.get("sources", []):
        if not source_cfg.get("enabled", False):
            continue

        source_name = source_cfg.get("source", "unknown")
        source_route = source_cfg.get("routing", "")

        if source_route in NO_VALID_ENDPOINT_ROUTINGS:
            continue

        for endpoint in source_cfg.get("primary_raw", []) or []:
            url = endpoint.get("url")
            name = endpoint.get("name")

            if url and name:
                tasks.append(
                    AcquisitionTask(
                        source=source_name,
                        stream=name,
                        url=url,
                        configured_route="primary_raw",
                        source_route=source_route
                    )
                )

        for endpoint in source_cfg.get("secondary_curated", []) or []:
            url = endpoint.get("url")
            name = endpoint.get("name")

            if url and name:
                tasks.append(
                    AcquisitionTask(
                        source=source_name,
                        stream=name,
                        url=url,
                        configured_route="secondary_curated",
                        source_route=source_route
                    )
                )

    return tasks


def fetch(task: AcquisitionTask) -> Dict[str, Any]:
    started = time.time()

    request = Request(
        task.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/geo+json, application/json, text/plain, */*"
        }
    )

    try:
        with urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            content_type = response.headers.get("Content-Type", "")
            payload = response.read(MAX_BYTES + 1)

            truncated = len(payload) > MAX_BYTES

            if truncated:
                payload = payload[:MAX_BYTES]

            destination, route_class, ext = destination_for(task, payload, content_type)

            destination.parent.mkdir(parents=True, exist_ok=True)

            if ext not in JSON_EXTENSIONS:
                payload_to_write = wrap_non_json_payload(
                    task=task,
                    payload=payload,
                    status=status,
                    content_type=content_type,
                    route_class=route_class
                )
                destination = destination.with_suffix(".json")
            else:
                payload_to_write = payload

            destination.write_bytes(payload_to_write)

            elapsed = round(time.time() - started, 3)

            record = {
                "timestamp_utc": utc_now().isoformat(),
                "source": task.source,
                "stream": task.stream,
                "url": task.url,
                "configured_route": task.configured_route,
                "route_class": route_class,
                "status": status,
                "success": 200 <= status < 400,
                "content_type": content_type,
                "bytes": len(payload),
                "truncated": truncated,
                "output": str(destination.relative_to(ROOT)),
                "elapsed_seconds": elapsed
            }

            append_log(record)
            update_health(task.source, task.stream, record["success"], "" if record["success"] else f"HTTP {status}")

            return record

    except HTTPError as exc:
        reason = f"HTTP {exc.code}"
    except URLError as exc:
        reason = f"URL error: {exc.reason}"
    except Exception as exc:
        reason = str(exc)

    elapsed = round(time.time() - started, 3)

    record = {
        "timestamp_utc": utc_now().isoformat(),
        "source": task.source,
        "stream": task.stream,
        "url": task.url,
        "configured_route": task.configured_route,
        "route_class": "failed",
        "status": "ERROR",
        "success": False,
        "error": reason,
        "elapsed_seconds": elapsed
    }

    append_log(record)
    update_health(task.source, task.stream, False, reason)

    return record


def acquire_all(tasks: Iterable[AcquisitionTask]) -> List[Dict[str, Any]]:
    tasks = list(tasks)

    if not tasks:
        return []

    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch, task) for task in tasks]

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results


def main() -> int:
    print()
    print("=== CLEAN-ROOM DUAL ACQUISITION RUNTIME v1.0 ===")
    print()

    for folder in [RAW_DIR, CURATED_DIR, LOG_DIR, STATE_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    config = load_config()
    tasks = build_tasks(config)

    primary_count = sum(1 for task in tasks if task.configured_route == "primary_raw")
    curated_count = sum(1 for task in tasks if task.configured_route == "secondary_curated")

    print(f"Config: {CONFIG_PATH}")
    print(f"Sources configured: {len(config.get('sources', []))}")
    print(f"Fetch tasks: {len(tasks)}")
    print(f"Primary raw tasks: {primary_count}")
    print(f"Secondary curated tasks: {curated_count}")
    print(f"Workers: {MAX_WORKERS}")
    print(f"Timeout: {CONNECT_TIMEOUT_SECONDS}s")
    print()
    print("Routing rule:")
    print("  *.geojson / FeatureCollection -> raw/<source>/... live")
    print("  all other reports -> curated/<source>/... delayed")
    print("  secondary_curated -> curated/<source>/... delayed")
    print()

    results = acquire_all(tasks)

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]
    live = [r for r in successes if r.get("route_class") == "live_geojson"]
    delayed = [r for r in successes if r.get("route_class") == "delayed_report"]

    print("Acquisition complete.")
    print(f"Successful fetches: {len(successes)}")
    print(f"Failed fetches: {len(failures)}")
    print(f"Live GeoJSON files: {len(live)}")
    print(f"Delayed/curated report files: {len(delayed)}")
    print(f"Log: {ACQUISITION_LOG}")
    print(f"Health: {SOURCE_HEALTH}")
    print()

    if failures:
        print("Failed streams:")
        for row in failures[:20]:
            print(f"  - {row.get('source')}:{row.get('stream')} :: {row.get('error') or row.get('status')}")
        if len(failures) > 20:
            print(f"  ... {len(failures) - 20} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
