"""
SEAM Curated Reconciliation Update v1.0

Purpose
-------
Adds:
- curated ingestion
- official reconciliation
- lead-time computation
- lock velocity computation
- delta export to latest.json

Integration Point
-----------------
Inject into:
    seam_operational_synthesis.py
"""

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

CURATED_DIR = ROOT / "curated"
PREVIOUS_STATE = ROOT / "state" / "previous_operational_state.json"

MAX_CURATED_MATCH_DISTANCE_KM = 80.0
MAX_CURATED_MATCH_TIME_HOURS = 12.0

# -------------------------------------------------------------------
# PREVIOUS STATE LOAD
# -------------------------------------------------------------------

def load_previous_state():
    if not PREVIOUS_STATE.exists():
        return {}

    try:
        return json.loads(
            PREVIOUS_STATE.read_text(
                encoding="utf-8",
                errors="replace"
            )
        )
    except Exception:
        return {}

# -------------------------------------------------------------------
# SAVE CURRENT STATE
# -------------------------------------------------------------------

def save_current_state(state):
    PREVIOUS_STATE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    PREVIOUS_STATE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )

# -------------------------------------------------------------------
# CURATED RECORD LOAD
# -------------------------------------------------------------------

def load_curated_records():

    records = []

    if not CURATED_DIR.exists():
        return records

    for path in CURATED_DIR.rglob("*.json"):

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )
            )

        except Exception:
            continue

        if isinstance(payload, list):
            records.extend(payload)

        elif isinstance(payload, dict):

            if isinstance(payload.get("features"), list):
                records.extend(payload["features"])

            elif isinstance(payload.get("events"), list):
                records.extend(payload["events"])

            else:
                records.append(payload)

    return records

# -------------------------------------------------------------------
# CURATED MATCH
# -------------------------------------------------------------------

def curated_match(event, curated):

    if event.get("regime") != curated.get("regime"):
        return False

    event_time = parse_time(
        event.get("acquisition_utc")
    )

    curated_time = parse_time(
        curated.get("time")
        or curated.get("timestamp")
        or curated.get("updated")
    )

    if event_time and curated_time:

        delta = abs(
            (event_time - curated_time).total_seconds()
        ) / 3600

        if delta > MAX_CURATED_MATCH_TIME_HOURS:
            return False

    try:

        ev_lat = float(event.get("latitude"))
        ev_lon = float(event.get("longitude"))

        cu_lat = float(curated.get("latitude"))
        cu_lon = float(curated.get("longitude"))

        dist = math.sqrt(
            (ev_lat - cu_lat) ** 2 +
            (ev_lon - cu_lon) ** 2
        ) * 111.0

        if dist > MAX_CURATED_MATCH_DISTANCE_KM:
            return False

    except Exception:
        pass

    return True

# -------------------------------------------------------------------
# APPLY CURATED RECONCILIATION
# -------------------------------------------------------------------

def inject_curated_reconciliation(events):

    curated_records = load_curated_records()

    for event in events:

        for curated in curated_records:

            if not curated_match(event, curated):
                continue

            official_time = (
                curated.get("time")
                or curated.get("timestamp")
                or curated.get("updated")
            )

            lead_seconds = None

            try:

                lead_seconds = int(
                    (
                        parse_time(official_time)
                        - parse_time(
                            event.get("acquisition_utc")
                        )
                    ).total_seconds()
                )

            except Exception:
                pass

            event["verification_state"] = {
                "official_confirmation": True,
                "official_source": curated.get(
                    "source",
                    "CURATED"
                ),
                "official_record_id": curated.get(
                    "id"
                ),
                "official_classification": curated.get(
                    "classification"
                )
                or curated.get("title")
                or curated.get("event"),
                "official_timestamp_utc": official_time,
                "lead_time_seconds": lead_seconds,
                "magnitude_delta": None,
                "spatial_error_km": None,
                "classification_agreement": None,
            }

            break

# -------------------------------------------------------------------
# LOCK VELOCITY COMPUTATION
# -------------------------------------------------------------------

def compute_lock_velocity(events):

    previous = load_previous_state()

    previous_events = previous.get(
        "events",
        []
    )

    for event in events:

        best = None

        for prior in previous_events:

            if (
                prior.get("signature")
                == event.get("signature")
            ):

                best = prior
                break

        if not best:
            continue

        try:

            old_lock = float(
                best.get("recursive_lock", 0)
            )

            new_lock = float(
                event.get("recursive_lock", 0)
            )

            old_time = parse_time(
                best.get("generated_utc")
                or previous.get("generated_utc")
            )

            new_time = utc_now()

            delta_minutes = max(
                1.0,
                (
                    new_time - old_time
                ).total_seconds() / 60
            )

            velocity = (
                new_lock - old_lock
            ) / delta_minutes

            event[
                "lock_velocity_per_minute"
            ] = round(
                velocity,
                2
            )

            if velocity > 0.05:
                direction = "↑"

            elif velocity < -0.05:
                direction = "↓"

            else:
                direction = "→"

            event["lock_direction"] = direction

        except Exception:

            event[
                "lock_velocity_per_minute"
            ] = None

            event[
                "lock_direction"
            ] = "→"

# -------------------------------------------------------------------
# FINAL SYNTHESIS INSERTION
# -------------------------------------------------------------------

"""
Insert before:
    export_dashboard(state)

Run:

    inject_curated_reconciliation(events)

    compute_lock_velocity(events)

    save_current_state(state)
"""
