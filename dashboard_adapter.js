/*
SEAM Dashboard Adapter v1.0

Purpose:
--------
Map:
    data/latest.json

into dashboard tile structures.

New SEAM fields:
----------------
recursive_lock
lock_state
signature
course
observation_count
persistence_state
verification_state
lock_thresholds
forecast_state
*/

async function loadSEAMOperationalState() {

    const response = await fetch('./data/latest.json');

    if (!response.ok) {
        throw new Error(
            `Failed loading latest.json (${response.status})`
        );
    }

    return await response.json();
}


function normalizeEvent(event) {

    const verification =
        event.verification_state || {};

    const persistence =
        event.persistence_state || {};

    const forecast =
        event.forecast_state || {};

    const thresholds =
        event.lock_thresholds || {};

    return {

        id:
            event.event_id,

        title:
            event.signature,

        regime:
            event.regime,

        location:
            event.street_cross,

        coordinates:
            event.lat_long,

        latitude:
            event.latitude,

        longitude:
            event.longitude,

        lock:
            event.recursive_lock,

        lockState:
            event.lock_state,

        trajectory:
            event.course,

        magnitude:
            event.magnitude,

        observations:
            event.observation_count,

        persistence:
            persistence.persistence_score || 0,

        viability:
            persistence.field_viability || 'UNKNOWN',

        trajectoryStability:
            persistence.trajectory_stability || 0,

        operationalPriority:
            event.operational_priority,

        dashboardPriority:
            event.dashboard_priority,

        signature:
            event.signature,

        signatureFamily:
            event.signature_family,

        topology:
            event.manifold_topology || {},

        evidence:
            event.evidence_summary || [],

        contradictions:
            event.contradictions || [],

        forecastConfidence:
            forecast.forecast_confidence || 0,

        projectionState:
            forecast.projection_state || 'UNKNOWN',

        estimatedDecay:
            forecast.estimated_decay_utc || null,

        officialConfirmation:
            verification.official_confirmation || false,

        officialSource:
            verification.official_source || null,

        officialClassification:
            verification.official_classification || null,

        officialTimestamp:
            verification.official_timestamp_utc || null,

        leadTimeSeconds:
            verification.lead_time_seconds || null,

        threshold85:
            thresholds['85_percent_utc'] || null,

        threshold90:
            thresholds['90_percent_utc'] || null,

        threshold95:
            thresholds['95_percent_utc'] || null
    };
}


async function buildSEAMDashboardDataset() {

    const payload =
        await loadSEAMOperationalState();

    const events =
        payload.active_events || [];

    return events.map(normalizeEvent);
}
