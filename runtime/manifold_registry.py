from pathlib import Path
from datetime import datetime, timezone
import json
from collections import defaultdict

SOURCE_LOG_DIR = Path("data/source_logs")
MANIFOLD_DIR = Path("data/manifolds")
MANIFOLD_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY = MANIFOLD_DIR / "active_manifolds.json"

SOURCE_TO_DOMAIN = {
    "USGS": "Seismic",
    "EMSC": "Seismic",
    "IRIS": "Seismic",
    "NOAA_SWPC": "Solar",
    "GOES": "Solar",
    "KiwiSDR": "RF",
    "SatNOGS": "Orbital",
    "Blitzortung": "Atmospheric",
    "OpenSky": "Transit",
    "Safecast": "Radiological"
}

DOMAIN_TO_TARGET = {
    "Seismic": {
        "region":"Pacific Seismic Arc",
        "hypothesis":"Persistent seismic recurrence manifold",
        "trajectory":"tectonic migration"
    },
    "Solar": {
        "region":"Solar Weather Envelope",
        "hypothesis":"Elevated geomagnetic interaction potential",
        "trajectory":"solar wind propagation"
    },
    "RF": {
        "region":"RF Observation Grid",
        "hypothesis":"Persistent RF anomaly recurrence",
        "trajectory":"multi-band propagation"
    },
    "Orbital": {
        "region":"Orbital Telemetry Shell",
        "hypothesis":"Elevated orbital telemetry clustering",
        "trajectory":"orbital persistence"
    },
    "Atmospheric": {
        "region":"Atmospheric Electrical Corridor",
        "hypothesis":"Electrical storm recurrence manifold",
        "trajectory":"storm line propagation"
    },
    "Transit": {
        "region":"Transit Observation Mesh",
        "hypothesis":"Transit density anomaly persistence",
        "trajectory":"air corridor continuity"
    },
    "Radiological": {
        "region":"Radiological Observation Grid",
        "hypothesis":"Background radiological deviation persistence",
        "trajectory":"environmental drift"
    }
}

def read_source_counts():
    counts = defaultdict(int)

    if not SOURCE_LOG_DIR.exists():
        return counts

    for file in SOURCE_LOG_DIR.glob("*.ndjson"):
        try:
            for line in file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    source = record.get("source")

                    if source:
                        counts[source] += 1
        except Exception:
            pass

    return counts

def synthesize_manifolds():
    counts = read_source_counts()

    domain_strength = defaultdict(int)
    domain_sources = defaultdict(list)

    for source, count in counts.items():
        domain = SOURCE_TO_DOMAIN.get(source)

        if domain:
            domain_strength[domain] += count
            domain_sources[domain].append(source)

    active_events = []

    for domain, strength in domain_strength.items():
        template = DOMAIN_TO_TARGET.get(domain)

        if not template:
            continue

        probability = min(0.35 + (strength * 0.01), 0.98)
        persistence = min(0.40 + (strength * 0.008), 0.96)

        state = "MONITOR"

        if probability >= 0.70:
            state = "TARGET"
        elif probability >= 0.50:
            state = "FOLLOW"

        active_events.append({
            "id": domain.lower().replace(" ","-"),
            "region": template["region"],
            "lat": 0,
            "lon": 0,
            "state": state,
            "hypothesis": template["hypothesis"],
            "probability": round(probability, 2),
            "persistence": round(persistence, 2),
            "trajectory": template["trajectory"],
            "sources": sorted(domain_sources[domain]),
            "evidence": [
                f"{strength} accumulated observations",
                f"{len(domain_sources[domain])} contributing sources",
                "cross-cycle persistence"
            ],
            "contradictions": []
        })

    active_events = sorted(
        active_events,
        key=lambda x: x["probability"],
        reverse=True
    )

    registry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "active_events": active_events
    }

    REGISTRY.write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8"
    )

    Path("latest.json").write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8"
    )

    Path("active_events.json").write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8"
    )

    print(f"[SEAM] synthesized {len(active_events)} dynamic manifolds")

if __name__ == "__main__":
    synthesize_manifolds()
