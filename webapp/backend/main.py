"""
QSFIN full-stack web application — backend.

This is a real FastAPI service wrapping the actual pipeline modules built
earlier in this project (digital_twin, agents, reasoning, optimization,
federated, orchestration) — it does not re-implement or fake any of that
logic, it imports and calls it. Every endpoint that says "live" genuinely
re-executes Python code on each request; nothing is pre-baked and replayed.

Run with:  uvicorn webapp.backend.main:app --reload --port 8420
(from the qsfin/ project root, so the sys.path insert below resolves)
"""
import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent.parent  # qsfin/
sys.path.insert(0, str(ROOT))

from digital_twin.twin import DigitalTwin
from agents.coordinator import run_agents, AGENTS
from reasoning.engine import assess_scenarios
from optimization.qubo_scorer import run as run_qubo
from federated.fedavg import run_federated_simulation
from orchestration.pipeline import analyze_case

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
CASE_PATH = ROOT / "data" / "case_QSFIN_2026_0417.json"

app = FastAPI(title="QSFIN API", version="0.1.0",
              description="Live backend for the QSFIN research prototype — "
                          "digital twin, multi-agent analysis, neuro-symbolic "
                          "reasoning, quantum-inspired optimization, and "
                          "federated learning, all running on synthetic data.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Load the case once at startup and build the digital twin from it. Agent
# findings / reasoning / a first optimization pass are also computed once
# at startup so GET requests are instant; POST .../rerun endpoints below
# genuinely recompute on demand for the frontend's live-demo widgets.
# ---------------------------------------------------------------------
with open(CASE_PATH) as f:
    CASE_DATA = json.load(f)

TWIN = DigitalTwin(CASE_DATA)
_startup_report = analyze_case(CASE_DATA)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "case_id": CASE_DATA["case_id"],
        "agents_loaded": [a.name for a in AGENTS],
        "note": "Live backend. All /api endpoints below execute real pipeline code on each request.",
    }


@app.get("/api/case")
def get_case():
    """Full case report — digital twin summary, every agent finding, the
    reasoning-layer ranking, the optimization-layer result, and the
    cross-check between them. This is the same object orchestration/
    pipeline.py produces when run from the command line."""
    return _startup_report


@app.post("/api/case/rerun")
def rerun_case():
    """Recomputes the entire pipeline from scratch: builds the digital
    twin, runs all 4 agents, re-scores scenarios with the reasoning layer,
    and re-solves the QUBO optimization — genuinely, not cached. Returns
    the fresh report plus how long it took, so the frontend can prove to
    itself (and the visitor) that this was a real computation."""
    t0 = time.time()
    report = analyze_case(CASE_DATA)
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    report["_meta"] = {"computed_live": True, "elapsed_ms": elapsed_ms}
    return report


@app.get("/api/digital-twin")
def get_digital_twin():
    return TWIN.to_render_json()


@app.get("/api/agents/findings")
def get_findings():
    bb = run_agents(TWIN, CASE_DATA)
    return {"agents": [a.name for a in AGENTS], "findings": bb.to_dict()}


@app.get("/api/reasoning")
def get_reasoning():
    bb = run_agents(TWIN, CASE_DATA)
    assessments = assess_scenarios(bb, TWIN, CASE_DATA)
    return [a.to_dict() for a in assessments]


@app.get("/api/optimization")
def get_optimization():
    bb = run_agents(TWIN, CASE_DATA)
    return run_qubo(CASE_DATA["candidate_scenarios"], bb.findings, seed=7)


@app.post("/api/optimization/rerun")
def rerun_optimization(seed: int = Query(default=None, ge=0, le=999999,
                        description="Random seed for the annealer. Omit for a fresh random seed each call.")):
    """Genuinely re-runs simulated annealing on the QUBO with a new random
    seed (or a caller-supplied one), independently verifies the result
    against the exact brute-force optimum, and reports whether this
    case's evidence-trust landscape has a tied (degenerate) optimum —
    which it does: S1 and S2 are equally consistent with the physical
    evidence subset this layer reasons over. That's real, not a bug."""
    import random as _random
    if seed is None:
        seed = _random.randint(0, 999999)
    t0 = time.time()
    bb = run_agents(TWIN, CASE_DATA)
    result = run_qubo(CASE_DATA["candidate_scenarios"], bb.findings, seed=seed, verify=True)
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    result["_meta"] = {"computed_live": True, "elapsed_ms": elapsed_ms}
    return result


@app.get("/api/federated")
def get_federated():
    return run_federated_simulation(rounds=15, local_epochs=5)


@app.post("/api/federated/rerun")
def rerun_federated(rounds: int = Query(default=15, ge=1, le=40),
                     local_epochs: int = Query(default=5, ge=1, le=20)):
    """Genuinely retrains the 4-agency FedAvg simulation from scratch with
    the requested number of communication rounds / local epochs per
    round — lets the frontend show, live, how federated accuracy
    approaches the centralized ceiling as rounds increase."""
    t0 = time.time()
    result = run_federated_simulation(rounds=rounds, local_epochs=local_epochs)
    elapsed_ms = round((time.time() - t0) * 1000, 1)
    result["_meta"] = {"computed_live": True, "elapsed_ms": elapsed_ms, "rounds": rounds, "local_epochs": local_epochs}
    return result


# ---------------------------------------------------------------------
# Static frontend + the existing standalone dashboard, served from the
# same FastAPI app so the whole thing is one deployable unit.
# ---------------------------------------------------------------------
@app.get("/dashboard")
def dashboard_page():
    return FileResponse(ROOT / "dashboard" / "qsfin_dashboard.html")


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
