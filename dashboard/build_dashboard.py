"""
Builds the single self-contained QSFIN dashboard HTML by embedding the
outputs of every module (digital twin scene, agent findings, reasoning
assessments, optimization result, federated learning result) directly
into one page. This is the artifact that demonstrates the whole pipeline
working together, end to end, for a human reviewer.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from digital_twin.build_viewer import render_html as render_twin_html, load_three_js


def load(path):
    with open(path) as f:
        return json.load(f)


def build():
    case_report = load(ROOT / "orchestration" / "case_report.json")
    federated = load(ROOT / "federated" / "federated_result.json")
    scene = load(ROOT / "digital_twin" / "scene_render.json")

    # Render the digital twin viewer to a full standalone HTML document
    # (same renderer as the standalone scene_viewer.html) so it can be
    # dropped straight into the dashboard's iframe via srcdoc — one
    # implementation of the 3D viewer, embedded safely as a JSON string
    # rather than nested inside another layer of JS templating.
    twin_html = render_twin_html(scene, load_three_js())

    bundle = {
        "case_report": case_report,
        "federated": federated,
        "scene": scene,
        "twin_html": twin_html,
    }

    # twin_html is a full HTML document (it has its own <script> tags for
    # the inlined three.js viewer). It's embedded here as a JSON string
    # inside THIS page's own <script> block, so any literal "</script>"
    # inside it would prematurely close the outer block to the HTML
    # parser (which doesn't know or care that it's sitting inside a JS
    # string) and truncate everything after it. Escaping the slash is the
    # standard fix — same reasoning applies to a stray "<!--".
    data_json = json.dumps(bundle)
    data_json = data_json.replace("</script", "<\\/script").replace("<!--", "<\\!--")

    html = TEMPLATE.replace("__DATA_JSON__", data_json)
    out_path = HERE / "qsfin_dashboard.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Built dashboard -> {out_path} ({out_path.stat().st_size/1024:.1f} KB)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QSFIN Prototype Dashboard</title>
<style>
:root {
  color-scheme: dark;
  --surface-1: #1a1a19;
  --page: #0d0d0d;
  --ink-1: #ffffff;
  --ink-2: #c3c2b7;
  --ink-muted: #898781;
  --grid: #2c2c2a;
  --baseline: #383835;
  --border: rgba(255,255,255,0.10);
  --s1: #3987e5; /* blue */
  --s2: #d95926; /* orange */
  --s3: #199e70; /* aqua */
  --s4: #c98500; /* yellow */
  --s5: #d55181; /* magenta */
  --s6: #008300; /* green */
  --s7: #9085e9; /* violet */
  --s8: #e66767; /* red */
  --good: #0ca30c;
  --warning: #fab219;
  --serious: #ec835a;
  --critical: #d03b3b;
}
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background: var(--page); color: var(--ink-1);
  font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
a { color: var(--s1); }

.app { max-width: 1180px; margin: 0 auto; padding: 0 20px 60px; }
header.top { padding: 22px 0 16px; border-bottom: 1px solid var(--border); margin-bottom: 18px; }
header.top .eyebrow { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 6px; }
header.top h1 { font-size: 21px; margin: 0 0 4px; font-weight: 650; }
header.top .meta { font-size: 12.5px; color: var(--ink-2); }
header.top .meta b { color: var(--ink-1); font-weight: 600; }

.banner { display:flex; align-items:center; gap:10px; padding: 10px 14px; border-radius: 10px;
  background: var(--surface-1); border: 1px solid var(--border); font-size: 13px; margin-bottom: 18px; }
.banner .dot { width:9px; height:9px; border-radius:50%; flex:none; }
.banner.agree .dot { background: var(--good); }
.banner.disagree .dot { background: var(--warning); }

nav.tabs { display:flex; gap:4px; flex-wrap:wrap; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
nav.tabs button { background:none; border:none; color: var(--ink-2); font-size: 13px; padding: 10px 14px;
  cursor:pointer; border-bottom: 2px solid transparent; font-family:inherit; }
nav.tabs button:hover { color: var(--ink-1); }
nav.tabs button.active { color: var(--ink-1); border-bottom-color: var(--s1); font-weight:600; }

.panel { display:none; }
.panel.active { display:block; }

.card { background: var(--surface-1); border:1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin-bottom: 16px; }
.card h2 { font-size: 14px; margin: 0 0 12px; font-weight: 650; }
.card h3 { font-size: 12.5px; margin: 14px 0 8px; color: var(--ink-2); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
.grid-2 { display:grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
@media (max-width: 800px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

.stat { background: var(--page); border:1px solid var(--border); border-radius:10px; padding: 12px 14px; }
.stat .v { font-size: 22px; font-weight: 650; font-variant-numeric: tabular-nums; }
.stat .l { font-size: 11.5px; color: var(--ink-muted); margin-top: 2px; }

.hbar-row { display:grid; grid-template-columns: 190px 1fr 70px; align-items:center; gap: 10px; margin: 10px 0; font-size: 12.5px; }
.hbar-row .label { color: var(--ink-2); }
.hbar-track { background: var(--grid); border-radius: 5px; height: 10px; overflow:hidden; }
.hbar-fill { height: 100%; border-radius: 5px 0 0 5px; }
.hbar-val { text-align:right; font-variant-numeric: tabular-nums; color: var(--ink-2); }

.badge { display:inline-block; font-size: 10.5px; padding: 2px 7px; border-radius: 999px; margin: 0 4px 4px 0; font-weight:600; }
.badge.support { background: rgba(12,163,12,.18); color: #6bdc6b; }
.badge.contradict { background: rgba(208,59,59,.18); color: #ef8f8f; }
.badge.agent { background: rgba(57,135,229,.18); color: #86b6ef; }

.finding { border-top: 1px solid var(--border); padding: 12px 0; }
.finding:first-child { border-top: none; }
.finding .summary { font-size: 13px; margin-bottom: 4px; }
.finding .reasoning { font-size: 12px; color: var(--ink-2); line-height:1.55; }
.finding .conf { font-size: 11px; color: var(--ink-muted); margin-top:4px; }

.legend { display:flex; gap:14px; flex-wrap:wrap; font-size:11.5px; color:var(--ink-2); margin-bottom: 10px; }
.legend .sw { display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:5px; vertical-align:middle; }

.chain-line { font-size: 12.5px; line-height: 1.7; color: var(--ink-2); white-space: pre-wrap; }
.chain-line b { color: var(--ink-1); }

table.tbl { width:100%; border-collapse: collapse; font-size: 12.5px; }
table.tbl th { text-align:left; color: var(--ink-muted); font-weight:600; font-size:11px; text-transform:uppercase;
  letter-spacing:.03em; padding: 6px 8px; border-bottom: 1px solid var(--baseline); }
table.tbl td { padding: 7px 8px; border-bottom: 1px solid var(--grid); font-variant-numeric: tabular-nums; }
table.tbl tr:last-child td { border-bottom: none; }

.twin-frame { width:100%; height: 560px; border-radius: 10px; overflow:hidden; border:1px solid var(--border); }
.twin-frame iframe { width:100%; height:100%; border:none; }

.chip-row { display:flex; gap:8px; flex-wrap:wrap; margin: 8px 0; }
.chip { font-size: 11.5px; padding: 4px 10px; border-radius: 999px; border:1px solid var(--border); color: var(--ink-2); }
.chip.trusted { border-color: rgba(12,163,12,.4); color:#6bdc6b; }
.chip.distrusted { border-color: rgba(208,59,59,.4); color:#ef8f8f; }

.note { font-size: 11.5px; color: var(--ink-muted); margin-top: 10px; line-height:1.5; }
footer.foot { margin-top: 30px; padding-top: 16px; border-top:1px solid var(--border); font-size: 11px; color: var(--ink-muted); }
</style>
</head>
<body>
<div class="app">
  <header class="top">
    <div class="eyebrow">QSFIN Prototype · v0.1 · Synthetic demonstration case</div>
    <h1 id="case-title">—</h1>
    <div class="meta" id="case-meta"></div>
  </header>

  <div class="banner" id="agree-banner"><div class="dot"></div><div id="agree-text"></div></div>

  <nav class="tabs">
    <button data-tab="overview" class="active">Overview</button>
    <button data-tab="twin">Digital Twin</button>
    <button data-tab="agents">Agent Findings</button>
    <button data-tab="reasoning">Reasoning &amp; Explanation</button>
    <button data-tab="optimization">Quantum-Inspired Optimization</button>
    <button data-tab="federated">Federated Learning</button>
  </nav>

  <div class="panel active" id="panel-overview"></div>
  <div class="panel" id="panel-twin"></div>
  <div class="panel" id="panel-agents"></div>
  <div class="panel" id="panel-reasoning"></div>
  <div class="panel" id="panel-optimization"></div>
  <div class="panel" id="panel-federated"></div>

  <footer class="foot">
    QSFIN — Quantum Sentient Forensic Intelligence Network. This is a research prototype running on
    fully synthetic data. Nothing in this dashboard is derived from a real case, and nothing in it
    constitutes a legal conclusion. Every score shown is traceable to a named agent finding and a
    named reasoning rule — see the Reasoning tab.
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;
const report = DATA.case_report;
const fed = DATA.federated;
const scene = DATA.scene;
const SCOLORS = {S1: 'var(--s1)', S2: 'var(--s2)', S3: 'var(--s3)'};
const SCOLORS_HEX = {S1: '#3987e5', S2: '#d95926', S3: '#199e70'};

function el(html) { const d = document.createElement('div'); d.innerHTML = html; return d.firstElementChild; }

// ---------- Header ----------
document.getElementById('case-title').textContent = report.title;
document.getElementById('case-meta').innerHTML =
  `Case <b>${report.case_id}</b> &nbsp;·&nbsp; ${report.total_findings} findings from <b>${report.agents_run.length}</b> agents ` +
  `&nbsp;·&nbsp; generated ${new Date(report.generated_at).toUTCString()}`;

const agreeBanner = document.getElementById('agree-banner');
const agree = report.cross_check.agree;
agreeBanner.classList.add(agree ? 'agree' : 'disagree');
document.getElementById('agree-text').innerHTML = agree
  ? `<b>Reasoning layer and optimization layer agree</b> on the leading scenario (${report.cross_check.reasoning_layer_top_scenario}).`
  : `<b>Reasoning layer and optimization layer disagree</b> — reasoning favors ${report.cross_check.reasoning_layer_top_scenario}, optimization favors ${report.cross_check.optimization_layer_selected_scenario}. ${report.cross_check.note}`;

// ---------- Tabs ----------
document.querySelectorAll('nav.tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
  });
});

// ---------- Overview panel ----------
(function renderOverview(){
  const p = document.getElementById('panel-overview');
  const ranking = report.reasoning_layer.ranking;
  const maxScore = Math.max(...ranking.map(r => Math.abs(r.adjusted_score)), 1);

  let bars = '';
  ranking.forEach(r => {
    const pct = Math.max(4, Math.abs(r.adjusted_score) / maxScore * 100);
    const color = SCOLORS[r.scenario_id] || 'var(--s1)';
    bars += `<div class="hbar-row">
      <div class="label">${r.scenario_id}</div>
      <div class="hbar-track"><div class="hbar-fill" style="width:${pct}%; background:${color}"></div></div>
      <div class="hbar-val">${r.adjusted_score >= 0 ? '+' : ''}${r.adjusted_score.toFixed(2)}</div>
    </div>`;
  });

  const stats = `<div class="grid-3">
    <div class="stat"><div class="v">${report.digital_twin_summary.n_evidence}</div><div class="l">Evidence markers</div></div>
    <div class="stat"><div class="v">${report.digital_twin_summary.n_people}</div><div class="l">People of interest</div></div>
    <div class="stat"><div class="v">${report.total_findings}</div><div class="l">Agent findings</div></div>
  </div>`;

  p.innerHTML = `
    <div class="card">
      <h2>Scenario ranking — neuro-symbolic reasoning layer</h2>
      ${bars}
      <div class="note">Score = weighted sum of supporting-finding confidence minus contradicting-finding confidence, adjusted by explicit symbolic rules (chain-of-custody discounting, no-direct-support cap). See the Reasoning tab for the full chain per scenario.</div>
    </div>
    <div class="card">
      <h2>Case digital twin at a glance</h2>
      ${stats}
    </div>
    <div class="card">
      <h2>Plain-language summary</h2>
      <div class="chain-line">${report.human_readable_summary}</div>
    </div>
  `;
})();

// ---------- Digital twin panel (embedded three.js scene) ----------
(function renderTwin(){
  const p = document.getElementById('panel-twin');
  p.innerHTML = `<div class="card">
    <h2>Interactive 3D digital twin — ${scene.title}</h2>
    <div class="note" style="margin-top:-6px; margin-bottom:10px;">Drag to orbit, scroll to zoom, click a marker for evidence detail and chain of custody.</div>
    <div class="twin-frame"><iframe id="twin-iframe"></iframe></div>
  </div>`;
  const iframe = document.getElementById('twin-iframe');
  // srcdoc (not doc.write of a hand-built string) so the embedded three.js
  // payload — which itself contains template-literal/backtick shader code —
  // never has to survive being re-quoted inside another JS template string.
  // DATA.twin_html was produced by the same Python renderer that builds the
  // standalone scene_viewer.html, so there is one implementation to trust.
  iframe.srcdoc = DATA.twin_html;
})();

// ---------- Agent findings panel ----------
(function renderAgents(){
  const p = document.getElementById('panel-agents');
  const byAgent = {};
  report.findings.forEach(f => { (byAgent[f.agent] = byAgent[f.agent] || []).push(f); });

  let html = '';
  Object.entries(byAgent).forEach(([agent, findings]) => {
    let rows = '';
    findings.forEach(f => {
      const sup = f.supports.map(s => `<span class="badge support">supports ${s}</span>`).join('');
      const con = f.contradicts.map(s => `<span class="badge contradict">contradicts ${s}</span>`).join('');
      rows += `<div class="finding">
        <div class="summary">${f.summary}</div>
        <div class="reasoning">${f.reasoning}</div>
        <div class="conf">confidence ${f.confidence.toFixed(2)} &nbsp; ${sup}${con}</div>
      </div>`;
    });
    html += `<div class="card"><h2>${agent.replace(/_/g,' ')} <span style="color:var(--ink-muted); font-weight:400;">(${findings.length} findings)</span></h2>${rows}</div>`;
  });
  p.innerHTML = html;
})();

// ---------- Reasoning panel ----------
(function renderReasoning(){
  const p = document.getElementById('panel-reasoning');
  let html = `<div class="card"><h2>Method</h2><div class="note" style="font-size:12.5px; color:var(--ink-2);">
    ${report.reasoning_layer.method}. The "neural" part is a statistical aggregation of every agent finding's confidence.
    The "symbolic" part is a small set of explicit, named rules (visible below as ⚖ lines) that adjust that raw score
    and are logged in plain language — so every ranking is explainable by construction, not by after-the-fact approximation.
  </div></div>`;

  report.reasoning_layer.ranking.forEach(r => {
    const lines = r.explanation_chain.map(l => {
      if (l.startsWith('  ⚖')) return `<div class="chain-line" style="color:var(--warning)">${l}</div>`;
      if (l.startsWith('  •')) return `<div class="chain-line">${l}</div>`;
      return `<div class="chain-line"><b>${l}</b></div>`;
    }).join('');
    html += `<div class="card"><h2>${r.scenario_id} — raw ${r.raw_score.toFixed(2)} → adjusted <span style="color:${SCOLORS_HEX[r.scenario_id]}">${r.adjusted_score.toFixed(2)}</span></h2>${lines}</div>`;
  });
  p.innerHTML = html;
})();

// ---------- Optimization panel ----------
(function renderOptimization(){
  const p = document.getElementById('panel-optimization');
  const opt = report.optimization_layer.result;
  const bfv = opt.bruteforce_verification;
  const trusted = opt.trusted_evidence.map(e => `<span class="chip trusted">${e} trusted</span>`).join('');
  const distrusted = opt.distrusted_evidence.map(e => `<span class="chip distrusted">${e} flagged</span>`).join('');

  p.innerHTML = `
  <div class="card">
    <h2>Quantum-inspired joint scenario/evidence optimization</h2>
    <div class="note" style="color:var(--ink-2); font-size:12.5px; margin-bottom:10px;">
      ${report.optimization_layer.method}<br><br>
      This layer does NOT run on quantum hardware — it formulates scenario selection and evidence-trust as a QUBO
      (the standard mathematical form used by real quantum annealers and QAOA), and solves it with simulated annealing,
      the classical stand-in. The solver here is verified against an exact brute-force optimum at this small scale;
      at real-world scale (many more scenarios and evidence items), brute force stops being tractable and this is
      exactly the regime annealing / quantum approaches are for.
    </div>
    <div class="grid-3">
      <div class="stat"><div class="v">${opt.selected_scenario}</div><div class="l">Selected scenario</div></div>
      <div class="stat"><div class="v">${opt.energy}</div><div class="l">Annealer energy</div></div>
      <div class="stat"><div class="v">${bfv ? (bfv.matches_annealer ? 'Matches ✓' : 'Mismatch ✗') : '—'}</div><div class="l">Brute-force verification</div></div>
    </div>
    <h3>Evidence trust assignment</h3>
    <div class="chip-row">${trusted}${distrusted || '<span class="note">No evidence flagged for distrust in this run.</span>'}</div>
  </div>`;
})();

// ---------- Federated learning panel ----------
(function renderFederated(){
  const p = document.getElementById('panel-federated');
  const agencies = Object.keys(fed.local_only_accuracy);
  const cols = [
    {k: fed.local_only_accuracy, label: 'Local-only', color: 'var(--s1)'},
    {k: fed.federated_accuracy_final_round, label: 'Federated (FedAvg)', color: 'var(--s2)'},
    {k: fed.centralized_pooled_accuracy, label: 'Centralized (pooled, ceiling)', color: 'var(--s3)'},
  ];

  let legend = cols.map(c => `<span><span class="sw" style="background:${c.color}"></span>${c.label}</span>`).join('');
  let rows = '';
  agencies.forEach(a => {
    rows += `<div style="margin:14px 0;">
      <div style="font-size:12.5px; color:var(--ink-2); margin-bottom:6px;">${a}</div>`;
    cols.forEach(c => {
      const v = c.k[a];
      const pct = (v * 100).toFixed(1);
      rows += `<div class="hbar-row" style="grid-template-columns:130px 1fr 50px;">
        <div class="label" style="font-size:11px;">${c.label}</div>
        <div class="hbar-track"><div class="hbar-fill" style="width:${pct}%; background:${c.color}"></div></div>
        <div class="hbar-val">${pct}%</div>
      </div>`;
    });
    rows += `</div>`;
  });

  let roundRows = '';
  fed.federated_training_history.forEach(h => {
    roundRows += `<tr><td>${h.round}</td><td>${(h.mean_accuracy*100).toFixed(1)}%</td></tr>`;
  });

  p.innerHTML = `
  <div class="card">
    <h2>Federated learning across simulated agencies</h2>
    <div class="note" style="color:var(--ink-2); font-size:12.5px; margin-bottom:10px;">
      Each agency trains locally on its own synthetic case data; only model parameters (never raw case
      records) are shared and averaged (FedAvg) into a global triage model, each communication round.
    </div>
    <div class="legend">${legend}</div>
    ${rows}
    <div class="grid-3" style="margin-top:14px;">
      <div class="stat"><div class="v">${(fed.mean_local_only*100).toFixed(1)}%</div><div class="l">Mean local-only</div></div>
      <div class="stat"><div class="v">${(fed.mean_federated*100).toFixed(1)}%</div><div class="l">Mean federated</div></div>
      <div class="stat"><div class="v">${(fed.mean_centralized*100).toFixed(1)}%</div><div class="l">Mean centralized (ceiling)</div></div>
    </div>
  </div>
  <div class="card">
    <h2>Federated accuracy by communication round</h2>
    <table class="tbl"><thead><tr><th>Round</th><th>Mean accuracy across agencies</th></tr></thead>
    <tbody>${roundRows}</tbody></table>
  </div>`;
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
