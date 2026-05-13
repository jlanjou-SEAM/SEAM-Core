const REFRESH_SECONDS = 10;
let refreshRemaining = REFRESH_SECONDS;

function updateClock(){
  const now = new Date();
  const timeEl = document.getElementById("user-time");
  const dateEl = document.getElementById("user-date");
  const countdownEl = document.getElementById("refresh-countdown");

  if(timeEl){
    timeEl.textContent =
      now.toLocaleTimeString([], {
        hour:"2-digit",
        minute:"2-digit",
        second:"2-digit",
        timeZoneName:"short"
      });
  }

  if(dateEl){
    dateEl.textContent =
      now.toLocaleDateString(undefined, {
        weekday:"short",
        year:"numeric",
        month:"short",
        day:"2-digit"
      });
  }

  if(countdownEl){
    countdownEl.textContent =
      `refresh 00:${String(refreshRemaining).padStart(2,"0")}`;
  }

  refreshRemaining--;

  if(refreshRemaining < 0){
    refreshRemaining = REFRESH_SECONDS;
  }
}

function probabilityClass(probability){
  if(probability >= 70) return { box:"prob-critical", text:"prob-critical-text" };
  if(probability >= 55) return { box:"prob-high", text:"prob-high-text" };
  if(probability >= 35) return { box:"prob-medium", text:"prob-medium-text" };
  return { box:"prob-low", text:"prob-low-text" };
}

function shortRegion(event){
  if(event.region && event.region !== "Unknown Region") return event.region;

  const regime = event.primary_regime || "event";
  const lat = Number(event.lat ?? event.latitude ?? 0);
  const lon = Number(event.lon ?? event.longitude ?? 0);

  if(lat !== 0 || lon !== 0){
    return `${String(regime).toUpperCase()} ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
  }

  return String(regime || "Unknown Region").toUpperCase();
}

function normalizePercent(value, fallback=0){
  const raw = Number(value ?? fallback ?? 0);
  if(Number.isNaN(raw)) return 0;
  if(raw <= 1) return Math.round(raw * 100);
  return Math.round(raw);
}

function normalizeEvent(event){
  const probability = normalizePercent(
    event.realization_probability ??
    event.probability ??
    event.forecast_confidence ??
    event.likelihood,
    0
  );

  const persistence = normalizePercent(
    event.persistence ??
    event.persistence_score ??
    event.source_convergence ??
    event.convergence,
    0
  );

  const probClass = probabilityClass(probability);

  const state =
    event.state ||
    event.lock_state ||
    event.verification_state ||
    "MONITOR";

  const lat = Number(event.lat ?? event.latitude ?? 0);
  const lon = Number(event.lon ?? event.longitude ?? 0);

  const verification = event.verification_state || "UNVERIFIED";
  const leadTime = Number(event.lead_time_seconds ?? 0);
  const liveSources = Number(event.live_source_count ?? 0);
  const delayedSources = Number(event.delayed_source_count ?? 0);
  const regime = event.primary_regime || event.regime || "unknown";

  const hypothesis =
    event.hypothesis ||
    event.analysis ||
    `${String(regime).toUpperCase()} target ${verification.toLowerCase()} | lead ${leadTime}s | live ${liveSources} / delayed ${delayedSources}`;

  const evidence = event.evidence || [
    `${verification.toLowerCase()}`,
    `live_sources_${liveSources}`,
    `delayed_sources_${delayedSources}`
  ];

  const contradictions = event.contradictions || [];

  return {
    target: shortRegion(event),
    coordinateRegion: event.region || `${String(regime).toUpperCase()} ${lat.toFixed(4)}, ${lon.toFixed(4)}`,
    hypothesis,
    probability,
    persistence,
    observations: event.observation_count || event.observations || 0,
    location: `${lat.toFixed(4)}, ${lon.toFixed(4)}`,
    state,
    stateClass: state === "TARGET" ? "state-critical" : state === "FOLLOW" ? "state-follow" : "state-monitor",
    cardClass: state === "TARGET" ? "target-critical" : state === "FOLLOW" ? "target-follow" : "",
    probabilityBoxClass: probClass.box,
    probabilityTextClass: probClass.text,
    evidence,
    contradictions,
    sources: event.sources || [],
    trajectory: event.trajectory || event.trajectory_state || "stable"
  };
}

function renderEvents(events){
  const root = document.getElementById("forecast-root");

  if(!root){
    console.error("Missing required DOM node: #forecast-root");
    return;
  }

  if(!events || events.length === 0){
    root.innerHTML = `<div class="empty-state">No active SEAM target analysis available.</div>`;
    return;
  }

  const sortedEvents = [...events].sort((a,b) => b.probability - a.probability);
  root.innerHTML = sortedEvents.map(renderCard).join("");
}

function renderCard(event){
  const lockBadge = event.state === "TARGET" ? `<span class="target-lock">LOCK</span>` : "";

  return `
    <article class="forecast-card ${event.cardClass}">
      <div class="card-head">
        <div class="target-row">
          <div class="target">${escapeHTML(event.target)} ${lockBadge}</div>
          <div class="obs">OBS ${escapeHTML(event.observations)}</div>
        </div>
        <div class="location" title="${escapeHTML(event.coordinateRegion)}">${escapeHTML(event.location)}</div>
      </div>

      <div class="card-body">
        <div class="forecast-text">${escapeHTML(event.hypothesis)}</div>

        <div class="metric-row">
          <div class="metric ${event.probabilityBoxClass}">
            <div class="label">Likelihood</div>
            <div class="metric-main">
              <span class="primary ${event.probabilityTextClass}">${event.probability}%</span>
            </div>
          </div>

          <div class="metric inten">
            <div class="label">Persistence</div>
            <div class="metric-main">
              <span class="primary intensity">${event.persistence}%</span>
            </div>
          </div>
        </div>

        <div class="info-row">
          <div class="info-box">
            <div class="label">State</div>
            <div class="info-value ${event.stateClass}">${escapeHTML(event.state)}</div>
          </div>

          <div class="info-box">
            <div class="label">Trajectory</div>
            <div class="info-value">${escapeHTML(event.trajectory)}</div>
          </div>
        </div>

        <div class="track-line full-width-track">
          <div class="label">Sources</div>
          <div class="track-value">${escapeHTML(event.sources.join(" • "))}</div>
        </div>

        <div class="factor-row">
          <div class="factor-box">
            <div class="label">Evidence</div>
            <div class="factor-list">${renderList(event.evidence, "pos", "+")}</div>
          </div>

          <div class="factor-box">
            <div class="label">Contradictions</div>
            <div class="factor-list">${renderList(event.contradictions, "neg", "−")}</div>
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderList(items, className, prefix){
  if(!items || items.length === 0){
    return `<div class="${className}">${prefix} none</div>`;
  }

  return items.slice(0,3).map(item =>
    `<div class="${className}">${prefix} ${escapeHTML(String(item).replaceAll("_"," "))}</div>`
  ).join("");
}

function escapeHTML(value){
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#039;"
  }[char]));
}

async function loadRuntime(){
  try{
    const response = await fetch("./data/latest.json?v=" + Date.now(), { cache:"no-store" });
    const runtime = await response.json();
    const rawEvents = runtime.active_events || runtime.candidate_hypotheses || runtime.events || [];
    renderEvents(rawEvents.map(normalizeEvent));
    refreshRemaining = REFRESH_SECONDS;
  }catch(error){
    console.error("SEAM runtime fetch failed", error);
    const root = document.getElementById("forecast-root");
    if(root){
      root.innerHTML =
        `<div class="empty-state">SEAM runtime fetch failed. Check data/latest.json.</div>`;
    }
  }
}

updateClock();
loadRuntime();
setInterval(updateClock, 1000);
setInterval(loadRuntime, REFRESH_SECONDS * 1000);
