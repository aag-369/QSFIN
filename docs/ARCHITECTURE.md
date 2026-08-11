# QSFIN Prototype — Architecture & Research Roadmap

Version: 0.1 (first working end-to-end prototype)
Status: runs entirely on synthetic, fictional case data. Not connected to any real case system.

## 1. What this prototype actually is

This is a working, runnable implementation of the QSFIN pipeline described in the original
project brief, built at demonstration scale on one synthetic case (`QSFIN-2026-0417`, a fictional
residential-homicide case) and one synthetic multi-agency dataset (four fictional agencies,
1,500 fictional historical cases total). Every module below is real, runnable code — nothing is
mocked out as a stub — but every module is also honestly scoped to what's achievable as a single
build, with clear notes on what would need to change to go from "prototype" to "production."

Run the whole thing yourself:

```
cd qsfin
python3 data/generate_agency_data.py        # regenerate synthetic multi-agency data
python3 digital_twin/twin.py                # build the digital twin + export render JSON
python3 digital_twin/build_viewer.py        # build the standalone 3D scene viewer
python3 agents/coordinator.py               # run all 4 forensic agents
python3 reasoning/engine.py                 # neuro-symbolic scenario ranking
python3 optimization/qubo_scorer.py         # quantum-inspired scenario/evidence optimization
python3 -m federated.fedavg                 # federated learning simulation
python3 -m orchestration.pipeline           # the full pipeline, one case in, one report out
python3 dashboard/build_dashboard.py        # build the all-in-one dashboard HTML
```

Open `dashboard/qsfin_dashboard.html` in any browser — it's fully self-contained (three.js is
inlined, not loaded from a CDN, so it works offline).

## 2. Module map

```
data/               synthetic case file + synthetic multi-agency historical datasets
digital_twin/        DigitalTwin class (queryable scene model) + three.js 3D viewer builder
agents/               4 specialized forensic agents + shared blackboard + coordinator
reasoning/            neuro-symbolic scenario scoring + plain-language explanation chains
optimization/         QUBO formulation + simulated-annealing solver (quantum-inspired)
federated/            FedAvg simulation across simulated agencies
orchestration/        ties digital_twin + agents + reasoning + optimization into one pipeline
dashboard/             single-file HTML dashboard embedding every module's output
```

Data flow for one case: `data/case_*.json` → `DigitalTwin` → 4 agents write `Finding`s to a
shared `Blackboard` → the reasoning layer scores each candidate scenario against those findings
→ the optimization layer independently scores scenario + evidence-trust jointly → the
orchestration pipeline combines both into one case report → the dashboard renders it.

Federated learning is a separate, parallel capability (cross-case triage modeling across
agencies), not a step in analyzing any single case — that's intentional, mirroring how a real
deployment would separate "analyze this case" from "improve our shared models over time."

## 3. How each module maps to the five publishable sub-projects

From the original project breakdown, this prototype gives each of the five a working seed:

1. **Digital twin crime-scene reconstruction** → `digital_twin/`. Currently driven by structured
   JSON rather than raw LiDAR/photogrammetry data — the natural next step is a real capture
   pipeline (see §5) feeding the same `DigitalTwin` interface.
2. **Multi-agent forensic reasoning framework** → `agents/` + `agents/blackboard.py`. The
   agent/blackboard pattern here is a legitimate, citable multi-agent-systems architecture on its
   own; each agent's logic is currently rule-based/deterministic rather than learned, which is a
   *feature* for a first version (auditable, no training data needed) and a place to add ML later.
3. **Explainable AI layer for legal reasoning** → `reasoning/engine.py`. This is the strongest
   candidate for a standalone thesis chapter or paper: the explicit separation of statistical
   aggregation from named symbolic rules, with every rule firing logged in plain language, is
   directly aligned with current legal-AI/XAI research on argumentation-based explainability.
4. **Federated learning across agencies** → `federated/`. Currently simulated with synthetic data
   and a from-scratch logistic regression; the FedAvg mechanism itself (weighted parameter
   averaging across communication rounds) is the real, standard algorithm, not a simplification.
5. **Quantum-inspired graph/optimization for scenario scoring** → `optimization/qubo_scorer.py`.
   Honestly labeled throughout as quantum-*inspired* (simulated annealing over a QUBO
   formulation), verified against exact brute-force at this scale, structured so the solver can be
   swapped for a real quantum annealer or QAOA circuit without touching the QUBO formulation.

## 4. What's simulated vs. what would be real in production

Being explicit about this is what keeps the project credible in front of an advisor, reviewer, or
funding body:

| Component | In this prototype | In a real deployment |
|---|---|---|
| Scene capture | Structured JSON authored by hand | LiDAR + photogrammetry + IoT sensor fusion pipeline |
| Agent "intelligence" | Deterministic rules over structured fields | Rules + trained models (CV for trajectory/blood-spatter analysis, NLP for witness statements) |
| Evidence data | Fictional, hand-written | Real forensic lab outputs, telecom CDRs (with legal authorization), CCTV |
| Quantum optimization | Simulated annealing on a classical CPU | Same QUBO, solvable on D-Wave-style annealers or via QAOA on gate-model hardware once viable at the needed scale |
| Federated learning | 4 simulated agencies, synthetic data, single machine | Real agencies, real infrastructure, secure aggregation protocols, legal MOUs between departments |
| "Explainability" | Rule-firing log + confidence-weighted aggregation | Same approach, but validated against real legal-admissibility standards (BNSS/Evidence Act requirements) with actual legal domain experts |
| Scale | 1 case, 6 evidence items, 4 people | Real caseloads: thousands of cases, evidence items in the hundreds, networks with hundreds/thousands of nodes — this is where the "quantum" framing starts to earn its keep over brute force |

## 5. Extension roadmap (in likely order of effort)

1. **Swap synthetic case data for a real (or realistic, IRB/ethics-cleared) dataset.** Every
   module was written against the case-file JSON schema in `data/case_*.json` — as long as a new
   dataset is transformed into that schema, nothing downstream needs to change.
2. **Add a real 3D capture pipeline.** Replace hand-authored room/evidence coordinates with
   photogrammetry output (e.g. COLMAP or a commercial LiDAR scanner export) feeding the same
   `DigitalTwin.from_file()` interface.
3. **Replace rule-based agent logic with trained models where it adds real value** — e.g. a CV
   model for blood-spatter angle estimation, an NLP model for extracting structured facts from
   free-text witness statements — while keeping the Finding/confidence/reasoning output contract
   unchanged so the reasoning layer doesn't need to change.
4. **Validate the explainability output against real legal standards.** Work with someone with
   Indian evidence-law expertise to check whether the rule-firing explanations in `reasoning/`
   would actually satisfy admissibility requirements under the Bharatiya Sakshya Adhiniyam / BNSS
   — this is likely the single highest-value, most citable piece of follow-up work.
5. **Scale the optimization layer and benchmark real quantum hardware.** Once case/evidence graphs
   are large enough that brute force is genuinely intractable, benchmark the QUBO on a real
   annealer (D-Wave Leap has a free tier for research) or a QAOA circuit (Qiskit) against the
   classical simulated-annealing baseline already in this repo — this produces a very clean,
   honest "quantum vs. classical" comparison chapter.
6. **Move federated learning from simulation to a real multi-party protocol**, including secure
   aggregation (so even the averaged parameters can't leak information about any one agency's
   data) — this is a systems/security contribution in its own right.

## 6. Suggested path to an actual thesis/paper

Given the five sub-projects above, the recommended real deliverable is **one of them, built out
properly, with the rest as the introduction's vision/future-work framing** — exactly as flagged in
the original project overview. Based on what exists in literature already and what's achievable
solo:

- **Fastest path to a strong, citable result:** extend `reasoning/engine.py` into a full
  neuro-symbolic explainable-AI-for-legal-reasoning paper. The core idea (explicit statistical +
  symbolic separation, rule-firing logs as the explanation artifact) is novel enough to stand on
  its own and directly engages active XAI-and-law literature.
- **Most visually compelling / best demo value:** extend `digital_twin/` into a real
  photogrammetry-driven crime-scene reconstruction system — this is the piece most likely to
  impress a non-technical audience (a review committee, a funding panel, law-enforcement
  stakeholders) and has a clear evaluation methodology (reconstruction accuracy vs. ground truth).
- **Most technically novel:** benchmark `optimization/qubo_scorer.py` against real quantum
  hardware at increasing problem scale — a clean quantitative "where does quantum start to win"
  result is rare and publishable on its own.

Whichever is chosen, this repository's other modules stay as working supporting infrastructure
and as the "bigger picture" narrative for the introduction — they don't need to be thrown away,
just clearly labeled as scaffolding/vision rather than the thesis's core contribution.
