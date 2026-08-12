/* QSFIN frontend — talks to the live FastAPI backend at /api/*. Every
   "LIVE" badge on the page corresponds to a real fetch() call below. */

const API = ""; // same-origin; backend serves this frontend too
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ---------------- Nav: toggle, smooth active-section highlight ----------------
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");
navToggle.addEventListener("click", () => {
  const open = navLinks.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
});
navLinks.querySelectorAll("a[data-section]").forEach(a => {
  a.addEventListener("click", () => navLinks.classList.remove("open"));
});

const sectionIds = ["problem", "pipeline", "explainability", "demo", "research", "roadmap", "about"];
const navMap = {};
navLinks.querySelectorAll("a[data-section]").forEach(a => navMap[a.dataset.section] = a);

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      Object.values(navMap).forEach(a => a.classList.remove("active"));
      const link = navMap[entry.target.id];
      if (link) link.classList.add("active");
    }
  });
}, { rootMargin: "-40% 0px -55% 0px" });
sectionIds.forEach(id => { const el = document.getElementById(id); if (el) sectionObserver.observe(el); });

// ---------------- Scroll reveal ----------------
document.querySelectorAll(".section, .stat-tile, .thread-card, .stage, .demo-card").forEach(el => el.classList.add("reveal"));
const revealObserver = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add("in"); obs.unobserve(entry.target); }
  });
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach(el => revealObserver.observe(el));

// ---------------- Animated stat counters (hero) ----------------
function animateCount(el) {
  const target = parseFloat(el.dataset.count);
  const suffix = el.dataset.suffix || "";
  if (prefersReducedMotion) { el.textContent = target + suffix; return; }
  const duration = 1000;
  const start = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * eased) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
const countObserver = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) { animateCount(entry.target); obs.unobserve(entry.target); }
  });
}, { threshold: 0.6 });
document.querySelectorAll(".stat-num[data-count]").forEach(el => countObserver.observe(el));

// ---------------- Problem bar fills ----------------
const barObserver = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const row = entry.target;
      const pct = row.dataset.pct;
      row.querySelector(".bar-fill").style.width = pct + "%";
      obs.unobserve(row);
    }
  });
}, { threshold: 0.4 });
document.querySelectorAll(".bar-row").forEach(el => barObserver.observe(el));

// ---------------- Pipeline: expand/collapse + connector draw-in ----------------
document.querySelectorAll(".stage-head").forEach(head => {
  head.addEventListener("click", () => {
    const stage = head.closest(".stage");
    const isOpen = stage.dataset.open === "true";
    stage.dataset.open = String(!isOpen);
    head.setAttribute("aria-expanded", String(!isOpen));
  });
});
const connector = document.getElementById("pipelineConnector");
const pipelineObserver = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) { connector.classList.add("in"); obs.disconnect(); }
  });
}, { threshold: 0.3 });
pipelineObserver.observe(document.getElementById("pipelineList"));

// ---------------- Live data: populate pipeline stats + explainability dossier ----------------
async function fetchJSON(path, opts) {
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

function setText(id, text) { const el = document.getElementById(id); if (el) el.textContent = text; }

async function loadLiveOverview() {
  try {
    const report = await fetchJSON("/api/case");
    setText("statEvidence", report.digital_twin_summary.n_evidence);
    setText("statRooms", report.digital_twin_summary.n_rooms);
    setText("statFindings", report.total_findings);
    setText("statAgentCount", report.agents_run.length);
    setText("statTopScenario", report.reasoning_layer.top_scenario);

    const opt = report.optimization_layer.result;
    setText("statQuboEnergy", `annealer energy ${opt.energy}, verified against exact brute-force optimum`);

    // Build a finding_id -> full finding lookup so the dossier can render
    // real supports/contradicts classification from structured data,
    // rather than pattern-matching the rendered explanation text (which
    // breaks on phrasing like "no CONTRADICTING alibi evidence" — that
    // sentence isn't itself a contradicting finding).
    const findingsById = {};
    report.findings.forEach(f => { findingsById[f.finding_id] = f; });
    renderDossier(report.reasoning_layer.ranking[0], findingsById);
  } catch (e) {
    console.error("Failed to load live overview", e);
    setText("dossierSummary", "Could not reach the QSFIN backend — is it running? (uvicorn webapp.backend.main:app)");
  }

  try {
    const fed = await fetchJSON("/api/federated");
    setText("statFedMean", `federated mean accuracy ${(fed.mean_federated * 100).toFixed(1)}% vs. centralized ceiling ${(fed.mean_centralized * 100).toFixed(1)}%`);
  } catch (e) { /* non-critical */ }
}

function renderDossier(scenario, findingsById) {
  setText("dossierScenarioId", `SCENARIO ${scenario.scenario_id}`);
  setText("dossierSummary", scenario.summary);
  setText("dossierRaw", (scenario.raw_score >= 0 ? "+" : "") + scenario.raw_score.toFixed(2));
  setText("dossierAdjusted", (scenario.adjusted_score >= 0 ? "+" : "") + scenario.adjusted_score.toFixed(2));

  const container = document.getElementById("dossierFindings");
  container.innerHTML = "";

  const supporting = (scenario.supporting_findings || [])
    .map(id => findingsById[id]).filter(Boolean)
    .sort((a, b) => b.confidence - a.confidence).slice(0, 3)
    .map(f => ({ f, cls: "supports" }));
  const contradicting = (scenario.contradicting_findings || [])
    .map(id => findingsById[id]).filter(Boolean)
    .sort((a, b) => b.confidence - a.confidence).slice(0, 2)
    .map(f => ({ f, cls: "contradicts" }));

  [...supporting, ...contradicting].forEach(({ f, cls }) => {
    const div = document.createElement("div");
    div.className = "dossier-finding " + cls;
    div.innerHTML = `<div class="df-summary">[${f.agent}] ${f.summary}</div>
      <div class="df-meta">confidence ${f.confidence.toFixed(2)} · ${cls === "supports" ? "supports" : "contradicts"} ${scenario.scenario_id}</div>`;
    container.appendChild(div);
  });

  if (scenario.rule_firings && scenario.rule_firings.length) {
    const rule = scenario.rule_firings[0];
    const div = document.createElement("div");
    div.className = "dossier-finding";
    div.style.borderLeftColor = "var(--accent-amber)";
    div.innerHTML = `<div class="df-summary">⚖ ${rule.rule_name}: ${rule.explanation}</div>
      <div class="df-meta">symbolic rule · score adjustment ${rule.score_delta >= 0 ? "+" : ""}${rule.score_delta.toFixed(2)}</div>`;
    container.appendChild(div);
  }
}

loadLiveOverview();

// ---------------- Re-run full case analysis ----------------
const rerunCaseBtn = document.getElementById("rerunCaseBtn");
rerunCaseBtn.addEventListener("click", async () => {
  rerunCaseBtn.disabled = true;
  setText("rerunCaseStatus", "Running full pipeline live…");
  try {
    const report = await fetchJSON("/api/case/rerun", { method: "POST" });
    const findingsById = {};
    report.findings.forEach(f => { findingsById[f.finding_id] = f; });
    renderDossier(report.reasoning_layer.ranking[0], findingsById);
    setText("rerunCaseStatus", `Recomputed live in ${report._meta.elapsed_ms}ms — ${report.total_findings} findings, top scenario ${report.reasoning_layer.top_scenario}.`);
  } catch (e) {
    setText("rerunCaseStatus", "Backend unreachable — start it with: uvicorn webapp.backend.main:app --port 8420");
  } finally {
    rerunCaseBtn.disabled = false;
  }
});

// ---------------- Re-run quantum-inspired optimizer ----------------
const rerunOptBtn = document.getElementById("rerunOptBtn");
const optResult = document.getElementById("optResult");
rerunOptBtn.addEventListener("click", async () => {
  rerunOptBtn.disabled = true;
  optResult.innerHTML = `<div class="demo-placeholder">Running simulated annealing on the backend…</div>`;
  try {
    const r = await fetchJSON("/api/optimization/rerun", { method: "POST" });
    const bfv = r.bruteforce_verification;
    const deg = r.degeneracy;
    optResult.innerHTML = `
      <div class="demo-result-grid">
        <div class="demo-stat"><div class="dk">Seed used</div><div class="dv">${r.seed}</div></div>
        <div class="demo-stat"><div class="dk">Selected scenario</div><div class="dv">${r.selected_scenario}</div></div>
        <div class="demo-stat"><div class="dk">Annealer energy</div><div class="dv">${r.energy}</div></div>
        <div class="demo-stat"><div class="dk">Brute-force match</div><div class="dv ${bfv.matches_annealer ? 'badge-match' : 'badge-mismatch'}">${bfv.matches_annealer ? 'MATCH ✓' : 'MISMATCH ✗'}</div></div>
      </div>
      <p class="demo-note">Computed live in ${r._meta.elapsed_ms}ms.
      ${deg && deg.is_degenerate ? `This landscape has ${deg.num_optimal_solutions} equally-optimal solutions spanning scenarios {${deg.scenarios_at_optimum.join(', ')}} — different seeds may legitimately select different ones, always at the same true-optimal energy (${deg.optimal_energy}).` : ''}</p>
    `;
  } catch (e) {
    optResult.innerHTML = `<div class="demo-placeholder">Backend unreachable — start it with: uvicorn webapp.backend.main:app --port 8420</div>`;
  } finally {
    rerunOptBtn.disabled = false;
  }
});

// ---------------- Re-run federated learning ----------------
const fedRoundsInput = document.getElementById("fedRounds");
const fedRoundsVal = document.getElementById("fedRoundsVal");
fedRoundsInput.addEventListener("input", () => { fedRoundsVal.textContent = fedRoundsInput.value; });

const rerunFedBtn = document.getElementById("rerunFedBtn");
const fedResult = document.getElementById("fedResult");
rerunFedBtn.addEventListener("click", async () => {
  rerunFedBtn.disabled = true;
  const rounds = fedRoundsInput.value;
  fedResult.innerHTML = `<div class="demo-placeholder">Retraining FedAvg across 4 simulated agencies for ${rounds} rounds…</div>`;
  try {
    const r = await fetchJSON(`/api/federated/rerun?rounds=${rounds}`, { method: "POST" });
    fedResult.innerHTML = `
      <div class="demo-result-grid">
        <div class="demo-stat"><div class="dk">Local-only mean</div><div class="dv">${(r.mean_local_only * 100).toFixed(1)}%</div></div>
        <div class="demo-stat"><div class="dk">Federated mean</div><div class="dv" style="color:var(--accent-quantum)">${(r.mean_federated * 100).toFixed(1)}%</div></div>
        <div class="demo-stat"><div class="dk">Centralized ceiling</div><div class="dv">${(r.mean_centralized * 100).toFixed(1)}%</div></div>
        <div class="demo-stat"><div class="dk">Rounds run</div><div class="dv">${r._meta.rounds}</div></div>
      </div>
      <p class="demo-note">Computed live in ${r._meta.elapsed_ms}ms across ${r.agencies.length} simulated agencies. No agency's raw case data was pooled — only model parameters were averaged, each round.</p>
    `;
  } catch (e) {
    fedResult.innerHTML = `<div class="demo-placeholder">Backend unreachable — start it with: uvicorn webapp.backend.main:app --port 8420</div>`;
  } finally {
    rerunFedBtn.disabled = false;
  }
});

