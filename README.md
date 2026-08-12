# QSFIN Prototype v0.1

Quantum Sentient Forensic Intelligence Network — a working, end-to-end prototype covering the
digital twin, multi-agent forensic analysis, neuro-symbolic explainable reasoning, quantum-inspired
scenario optimization, and federated learning pieces of the original QSFIN project brief.

**Everything here runs on synthetic, fictional data.** No real case, person, or agency is
represented. See `docs/ARCHITECTURE.md` for the full breakdown of what's simulated vs. what a real
deployment would need, and a suggested path from this prototype to an actual thesis/paper.

## Quick start

```bash
pip install -r requirements.txt
python3 data/generate_agency_data.py
python3 digital_twin/twin.py && python3 digital_twin/build_viewer.py
python3 agents/coordinator.py
python3 reasoning/engine.py
python3 optimization/qubo_scorer.py
python3 -m federated.fedavg
python3 -m orchestration.pipeline
python3 dashboard/build_dashboard.py
```

Then open `dashboard/qsfin_dashboard.html` in a browser (works fully offline — no CDN
dependencies) or `digital_twin/scene_viewer.html` for just the 3D crime-scene viewer on its own.

## Full-stack website (live backend + themed frontend)

```bash
pip install fastapi uvicorn   # already in requirements.txt
uvicorn webapp.backend.main:app --port 8420
```

Open **http://127.0.0.1:8420/** — a themed, professionally designed showcase site (forensic-lab /
quantum-lab visual identity) with a real FastAPI backend behind it: several widgets on the page
(scenario optimizer, federated-learning trainer, full case re-analysis) call the backend live and
recompute for real on every click, not just replay static numbers. The original all-in-one
dashboard is still served alongside it at **http://127.0.0.1:8420/dashboard**. Full details,
including exactly which parts of the page are live vs. static, are in `webapp/README.md`.

## Layout

- `data/` — the synthetic demo case + synthetic multi-agency historical datasets
- `digital_twin/` — queryable scene model + 3D web viewer
- `agents/` — ballistics, digital forensics, network, and timeline agents + shared blackboard
- `reasoning/` — neuro-symbolic scenario scoring and plain-language explanations
- `optimization/` — QUBO formulation solved via simulated annealing (quantum-inspired)
- `federated/` — FedAvg simulation across simulated agencies
- `orchestration/` — the single pipeline that runs a case through every module
- `dashboard/` — the all-in-one visual dashboard
- `webapp/` — the full-stack showcase website (FastAPI backend + themed frontend)
- `docs/` — architecture notes, research roadmap, and the website build prompt

## Read this first

`docs/ARCHITECTURE.md` — full module map, honest simulated-vs-real breakdown, and a concrete
roadmap for turning this prototype into a real thesis or research paper.

## License

Copyright (c) 2026 Aayushman Ghatak. All rights reserved. This repository is public for
portfolio and demonstration purposes only — see [`LICENSE`](./LICENSE) for terms. No reuse,
copying, or redistribution is permitted without written permission.
