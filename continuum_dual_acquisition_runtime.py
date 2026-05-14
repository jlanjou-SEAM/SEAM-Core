"""
continuum_dual_acquisition_runtime.py
Version: 2.3

SEAM Epistemic Acquisition Runtime

Changes from v2.2:
------------------
1. Timeout reduced from 6s to 2s.
2. Curated/official endpoints are first-class fetch routes.
3. Existing production config compatibility preserved:
   - primary_raw       -> raw/
   - secondary_curated -> decoded/
   - curated           -> curated/
   - official          -> curated/

Expected:
---------
Sources configured: 40
Fetch tasks: ~55+ depending on config
Successful fetches: ~50+
"""

from __future__ import annotations

import concurrent.futures
import json
import mimetypes
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent

CONFIG_PATH = ROOT / "config" / "dual_acquisition_sources.json"

RAW_DIR = ROOT / "raw"
DECODED_DIR = ROOT / "decoded"
CURATED_DIR = ROOT / "curated"

LOG_DIR = ROOT / "logs"
STATE_DIR = ROOT / "state"

ACQUISITION_LOG = LOG_DIR / "acquisition_log.jsonl"
SOURCE_HEALTH = STATE_DIR / "source_health.json"

CONNECT_TIMEOUT_SECONDS = 2
MAX_WORKERS = 16
MAX_BYTES = 50_000_000

USER_AGENT = "SEAM-CleanRoom-Epistemic-Acquisition/2.3"

VALID_EPISTEMIC_LAYERS = {"raw", "decoded", "curated"}

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
    epistemic_layer: str
    regime: str
    latency_class: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def infer_epistemic_layer(source_cfg: Dict[str, Any], endpoint: Dict[str, Any], route_name: str) -> str:
    explicit = (
        endpoint.get("epistemic_layer")
        or source_cfg.get("epistemic_layer")
        or source_cfg.get("layer")
    )

    if explicit:
        layer = str(explicit).lower().strip()
        if layer in VALID_EPISTEMIC_LAYERS:
            return layer

    # Hard route rules.
    if route_name == "primary_raw":
        return "raw"

    if route_name == "secondary_curated":
        return "decoded"

    if route_name in {"curated", "official"}:
        return "curated"

    # Soft official marker fallback.
    source_text = json.dumps(source_cfg, default=str).lower()
    endpoint_text = json.dumps(endpoint, default=str).lower()

    official_markers = [
        "official",
        "nws",
        "noaa_spc",
        "spc",
        "warning",
        "watch",
        "advisory",
        "bulletin",
        "storm_report",
        "official_report",
    ]

    if any(marker in source_text or marker in endpoint_text for marker in official_markers):
        return "curated"

    return "raw"


def output_root_for_layer(layer: str) -> Path:
    if layer == "raw":
        return RAW_DIR
    if layer == "decoded":
        return DECODED_DIR
    if layer == "curated":
        return CURATED_DIR
    return RAW_DIR


def content_extension(url: str, content_type: str, payload: bytes) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()

    if suffix in {".json", ".geojson", ".txt", ".csv", ".xml"}:
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


def wrap_non_json_payload(task: AcquisitionTask, payload: bytes, status: int, content_type: str) -> bytes:
    wrapper = {
        "timestamp_utc": utc_now().isoformat(),
        "source": task.source,
        "stream": task.stream,
        "url": task.url,
        "epistemic_layer": task.epistemic_layer,
        "regime": task.regime,
        "latency_class": task.latency_class,
        "configured_route": task.configured_route,
        "status": status,
        "content_type": content_type,
        "bytes": len(payload),
        "payload_text": payload.decode("utf-8", errors="replace")[:200_000],
    }

    return json.dumps(wrapper, indent=2).encode("utf-8")


def destination_for(task: AcquisitionTask, payload: bytes, content_type: str) -> Tuple[Path, str]:
    original_ext = content_extension(task.url, content_type, payload)
    ext = original_ext

    source_name = sanitize(task.source)
    stream_name = sanitize(task.stream)

    root = output_root_for_layer(task.epistemic_layer)

    if ext not in {".json", ".geojson"}:
        ext = ".json"

    filename = f"{utc_stamp()}_{stream_name}_{task.epistemic_layer}{ext}"

    return root / source_name / utc_date() / filename, original_ext


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
        "updated_utc": utc_now().isoformat(),
    }

    SOURCE_HEALTH.write_text(json.dumps(health, indent=2), encoding="utf-8")


def add_endpoint_tasks(tasks: List[AcquisitionTask], source_cfg: Dict[str, Any], route_name: str) -> None:
    source_name = source_cfg.get("source", "unknown")
    source_route = source_cfg.get("routing", "")

    endpoints = source_cfg.get(route_name, []) or []

    for endpoint in endpoints:
        url = endpoint.get("url")
        name = endpoint.get("name")

        if not url or not name:
            continue

        layer = infer_epistemic_layer(source_cfg, endpoint, route_name)

        tasks.append(
            AcquisitionTask(
                source=source_name,
                stream=name,
                url=url,
                configured_route=route_name,
                source_route=source_route,
                epistemic_layer=layer,
                regime=str(endpoint.get("regime") or source_cfg.get("regime") or "unknown"),
                latency_class=str(endpoint.get("latency_class") or source_cfg.get("latency_class") or route_name),
            )
        )


def build_tasks(config: Dict[str, Any]) -> List[AcquisitionTask]:
    tasks: List[AcquisitionTask] = []

    for source_cfg in config.get("sources", []):
        if not source_cfg.get("enabled", False):
            continue

        if source_cfg.get("routing", "") in NO_VALID_ENDPOINT_ROUTINGS:
            continue

        # Production compatibility routes.
        add_endpoint_tasks(tasks, source_cfg, "primary_raw")
        add_endpoint_tasks(tasks, source_cfg, "secondary_curated")

        # New first-class epistemic routes.
        add_endpoint_tasks(tasks, source_cfg, "decoded")
        add_endpoint_tasks(tasks, source_cfg, "curated")
        add_endpoint_tasks(tasks, source_cfg, "official")

    return tasks


def fetch(task: AcquisitionTask) -> Dict[str, Any]:
    started = time.time()

    request = Request(
        task.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/geo+json, application/json, text/plain, */*",
        },
    )

    try:
        with urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS) as response:
            raw_status = getattr(response, "status", 200)
            status = int(raw_status) if raw_status is not None else 200
            content_type = response.headers.get("Content-Type", "")
            payload = response.read(MAX_BYTES + 1)

            truncated = len(payload) > MAX_BYTES

            if truncated:
                payload = payload[:MAX_BYTES]

            destination, original_ext = destination_for(task, payload, content_type)
            destination.parent.mkdir(parents=True, exist_ok=True)

            if original_ext not in {".json", ".geojson"}:
                payload_to_write = wrap_non_json_payload(task, payload, status, content_type)
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
                "epistemic_layer": task.epistemic_layer,
                "regime": task.regime,
                "latency_class": task.latency_class,
                "status": status,
                "success": 200 <= status < 400,
                "content_type": content_type,
                "bytes": len(payload),
                "truncated": truncated,
                "output": str(destination.relative_to(ROOT)),
                "elapsed_seconds": elapsed,
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
        "epistemic_layer": task.epistemic_layer,
        "regime": task.regime,
        "latency_class": task.latency_class,
        "status": "ERROR",
        "success": False,
        "error": reason,
        "elapsed_seconds": elapsed,
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
    print("=== SEAM EPISTEMIC ACQUISITION RUNTIME v2.3 ===")
    print()

    for folder in [RAW_DIR, DECODED_DIR, CURATED_DIR, LOG_DIR, STATE_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    config = load_config()
    tasks = build_tasks(config)

    route_counts: Dict[str, int] = {}
    layer_counts: Dict[str, int] = {}

    for task in tasks:
        route_counts[task.configured_route] = route_counts.get(task.configured_route, 0) + 1
        layer_counts[task.epistemic_layer] = layer_counts.get(task.epistemic_layer, 0) + 1

    print(f"Config: {CONFIG_PATH}")
    print(f"Sources configured: {len(config.get('sources', []))}")
    print(f"Fetch tasks: {len(tasks)}")
    print(f"Task routes: {route_counts}")
    print(f"Task layers: {layer_counts}")
    print(f"Workers: {MAX_WORKERS}")
    print(f"Timeout: {CONNECT_TIMEOUT_SECONDS}s")
    print()

    results = acquire_all(tasks)

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    raw_count = sum(1 for r in successes if r.get("epistemic_layer") == "raw")
    decoded_count = sum(1 for r in successes if r.get("epistemic_layer") == "decoded")
    curated_count = sum(1 for r in successes if r.get("epistemic_layer") == "curated")

    print("Acquisition complete.")
    print(f"Successful fetches: {len(successes)}")
    print(f"Failed fetches: {len(failures)}")
    print(f"RAW files: {raw_count}")
    print(f"DECODED files: {decoded_count}")
    print(f"CURATED files: {curated_count}")
    print(f"Log: {ACQUISITION_LOG}")
    print(f"Health: {SOURCE_HEALTH}")
    print()

    if failures:
        print("Failed streams:")
        for row in failures[:20]:
            print(f"  - {row.get('source')}:{row.get('stream')} :: {row.get('error') or row.get('status')}")
        if len(failures) > 20:
            print(f"  ... {len(failures) - 20} more")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
