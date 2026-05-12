async function loadJSON(path) {
    const res = await fetch(path + "?ts=" + Date.now());
    return await res.json();
}

async function refreshSEAM() {

    const [
        live,
        tracks,
        forecasts,
        manifolds,
        aggregates
    ] = await Promise.all([
        loadJSON("../reports/live_event_state.json"),
        loadJSON("../reports/persistent_field_tracks_current.json"),
        loadJSON("../reports/forecast_cones_current.json"),
        loadJSON("../reports/cross_stream_manifolds_current.json"),
        loadJSON("../reports/spatial_aggregate_current.json")
    ]);

    const state = {
        timestamp_utc:
            live.timestamp_utc,

        events:
            (live.events || []).map(e => ({
                id:
                    e.event_id,

                type:
                    e.primary_regime,

                status:
                    e.lock_state,

                verification:
                    e.verification_state,

                confidence:
                    e.forecast_confidence,

                lat:
                    e.latitude,

                lon:
                    e.longitude,

                lead_time:
                    e.lead_time_seconds,

                observations:
                    e.observation_count,

                sources:
                    e.source_count
            })),

        tracks:
            tracks.tracks || [],

        forecasts:
            forecasts.forecasts || [],

        manifolds:
            manifolds.manifolds || [],

        aggregates:
            aggregates.aggregates || []
    };

    window.SEAM_STATE = state;

    renderSummary(state);
    renderEvents(state.events);
}

function renderSummary(state) {

    const el =
        document.getElementById("summary");

    el.innerText =
        `events=${state.events.length} | ` +
        `tracks=${state.tracks.length} | ` +
        `forecasts=${state.forecasts.length} | ` +
        `manifolds=${state.manifolds.length}`;
}

function renderEvents(events) {

    const tbody =
        document.getElementById("events");

    tbody.innerHTML = "";

    for (const e of events.slice(0, 250)) {

        const tr =
            document.createElement("tr");

        tr.innerHTML = `
            <td>${e.id || ""}</td>
            <td>${e.type || ""}</td>
            <td>${e.status || ""}</td>
            <td>${e.verification || ""}</td>
            <td>${e.confidence || ""}</td>
            <td>${e.lat || ""}</td>
            <td>${e.lon || ""}</td>
            <td>${e.lead_time || ""}</td>
        `;

        tbody.appendChild(tr);
    }
}

refreshSEAM();
setInterval(refreshSEAM, 5000);
