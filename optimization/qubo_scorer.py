"""
QSFIN — Quantum-inspired scenario/evidence optimization.

HONEST FRAMING FIRST: this module does not run on a quantum computer.
It formulates the "which scenario best fits the evidence, and which
contested evidence should be trusted" problem as a QUBO (Quadratic
Unconstrained Binary Optimization) — the standard mathematical form used
by real quantum annealers (e.g. D-Wave) and QAOA-style gate-model quantum
algorithms — and solves it with simulated annealing, a classical
metaphor/stand-in for quantum annealing that searches the same energy
landscape. Swapping the solve_* function at the bottom of this file for a
call to a real quantum annealer's API (or a QAOA circuit) is a drop-in
replacement; nothing about the QUBO formulation above it would need to
change. That is the honest and currently-correct way to describe "quantum
optimization" in this project: quantum-ready, classically validated today.

WHY FORMULATE IT THIS WAY AT ALL, GIVEN 3 SCENARIOS IS TRIVIAL TO BRUTE
FORCE: because the real target isn't 3 scenarios, it's joint reasoning
over a scenario AND every piece of contested evidence simultaneously —
that combined search space grows exponentially with case complexity
(more scenarios, more evidence items, more suspects in a network), which
is exactly the regime where classical brute force stops being tractable
and annealing-style / quantum approaches start to matter. This module is
built at small scale so its correctness can be checked against an exact
brute-force solution (see verify_against_bruteforce below), while being
structured so it scales the same way a real deployment's QUBO would.
"""
import itertools
import json
import random
from pathlib import Path

import numpy as np


def build_qubo(scenarios: list[dict], findings: list, one_hot_penalty: float = 6.0,
               evidence_prior: float = 0.15):
    """
    Variables:
      x_s  (one per scenario)  = 1 if this scenario is selected as the
                                  working hypothesis
      z_e  (one per evidence id referenced by any finding) = 1 if this
                                  piece of evidence is trusted

    Objective (to MINIMIZE, i.e. energy):
      - reward selecting a scenario whose trusted, supporting evidence is
        strong -> negative energy contribution
      + penalize selecting a scenario while trusting evidence that
        contradicts it -> positive energy contribution
      + one-hot constraint: exactly one scenario selected
      + small prior cost for distrusting evidence (default-trust bias, so
        the optimizer doesn't trivially distrust everything to dodge
        contradiction penalties)

    Returns (var_names, Q) where Q is a symmetric numpy matrix such that
    energy(x) = x^T Q x for binary vector x indexed by var_names.
    """
    scenario_ids = [s["scenario_id"] for s in scenarios]
    evidence_ids = sorted({ref for f in findings for ref in f.evidence_refs if ref.startswith("E-")})

    var_names = [f"x_{s}" for s in scenario_ids] + [f"z_{e}" for e in evidence_ids]
    idx = {v: i for i, v in enumerate(var_names)}
    n = len(var_names)
    Q = np.zeros((n, n))

    # --- one-hot constraint on scenario selection: penalty * (sum x_s - 1)^2 ---
    # expand: penalty * (sum x_s^2 + 2*sum_{i<j} x_i x_j - 2*sum x_s + 1)
    # x_s^2 == x_s for binary vars
    for s in scenario_ids:
        i = idx[f"x_{s}"]
        Q[i, i] += one_hot_penalty * (1 - 2)  # x_s^2 coefficient contribution minus linear -2*x_s term folded in
    for s1, s2 in itertools.combinations(scenario_ids, 2):
        i, j = idx[f"x_{s1}"], idx[f"x_{s2}"]
        Q[i, j] += one_hot_penalty * 2
        Q[j, i] += one_hot_penalty * 2
    # constant term (+penalty) is irrelevant to argmin, omitted

    # --- evidence trust prior: small cost for z_e = 0, i.e. reward z_e = 1 slightly ---
    for e in evidence_ids:
        i = idx[f"z_{e}"]
        Q[i, i] -= evidence_prior

    # --- support / contradiction interaction terms between x_s and z_e ---
    for f in findings:
        refs = [r for r in f.evidence_refs if r.startswith("E-")]
        if not refs:
            continue
        for s in f.supports:
            if s not in scenario_ids:
                continue
            xi = idx[f"x_{s}"]
            for e in refs:
                zi = idx[f"z_{e}"]
                # reward (negative energy) for selecting scenario s while trusting supporting evidence e
                Q[xi, zi] -= f.confidence
                Q[zi, xi] -= f.confidence
        for s in f.contradicts:
            if s not in scenario_ids:
                continue
            xi = idx[f"x_{s}"]
            for e in refs:
                zi = idx[f"z_{e}"]
                # penalize (positive energy) for selecting scenario s while trusting contradicting evidence e
                Q[xi, zi] += f.confidence
                Q[zi, xi] += f.confidence

    return var_names, Q


def energy(bits: np.ndarray, Q: np.ndarray) -> float:
    return float(bits @ Q @ bits)


def solve_simulated_annealing(var_names, Q, n_sweeps=2000, n_restarts=25, seed=7):
    """Classical simulated annealing over the QUBO energy landscape — the
    stand-in for a quantum annealer described in the module docstring."""
    rng = random.Random(seed)
    n = len(var_names)
    best_bits, best_e = None, float("inf")

    for restart in range(n_restarts):
        bits = np.array([rng.randint(0, 1) for _ in range(n)], dtype=float)
        e = energy(bits, Q)
        T0, T1 = 3.0, 0.02
        for step in range(n_sweeps):
            T = T0 * (T1 / T0) ** (step / n_sweeps)
            i = rng.randrange(n)
            trial = bits.copy()
            trial[i] = 1 - trial[i]
            e_trial = energy(trial, Q)
            d = e_trial - e
            if d <= 0 or rng.random() < np.exp(-d / max(T, 1e-9)):
                bits, e = trial, e_trial
        if e < best_e:
            best_bits, best_e = bits.copy(), e

    return best_bits, best_e


def analyze_degeneracy(var_names, Q, tol=1e-6):
    """Enumerate every binary assignment (only tractable at this small
    scale — see solve_bruteforce) and report whether the minimum energy is
    achieved by more than one assignment, and if so which scenarios appear
    among those tied optima. This is not a hedge — it's a real property of
    this case's evidence-trust landscape worth surfacing honestly: running
    the annealer from different random seeds can legitimately select
    different, EQUALLY optimal scenarios, and that tie is itself
    information (it means the physical/ballistics evidence subset this
    layer reasons over cannot by itself distinguish those scenarios — the
    reasoning layer's broader evidence base is what breaks the tie)."""
    n = len(var_names)
    best_e = float("inf")
    optimal_assignments = []
    for combo in itertools.product([0, 1], repeat=n):
        bits = np.array(combo, dtype=float)
        e = energy(bits, Q)
        if e < best_e - tol:
            best_e, optimal_assignments = e, [combo]
        elif abs(e - best_e) <= tol:
            optimal_assignments.append(combo)

    scenarios_at_optimum = set()
    for combo in optimal_assignments:
        for v, b in zip(var_names, combo):
            if v.startswith("x_") and b == 1:
                scenarios_at_optimum.add(v[2:])

    return {
        "num_optimal_solutions": len(optimal_assignments),
        "is_degenerate": len(optimal_assignments) > 1,
        "scenarios_at_optimum": sorted(scenarios_at_optimum),
        "optimal_energy": round(best_e, 4),
    }


def solve_bruteforce(var_names, Q):
    """Exact solution by trying every binary assignment — only tractable
    at small scale, used here purely to VERIFY the annealer found the true
    optimum. A real deployment would drop this at scale."""
    n = len(var_names)
    best_bits, best_e = None, float("inf")
    for combo in itertools.product([0, 1], repeat=n):
        bits = np.array(combo, dtype=float)
        e = energy(bits, Q)
        if e < best_e:
            best_bits, best_e = bits, e
    return best_bits, best_e


def decode(var_names, bits) -> dict:
    return {v: int(b) for v, b in zip(var_names, bits)}


def run(scenarios, findings, verify=True, seed=7):
    """seed is exposed so a live caller (e.g. the web backend's "re-run
    optimizer" button) can trigger a genuinely fresh annealing run each
    time — different random restarts, same QUBO — and show that it keeps
    converging to the same brute-force-verified optimum regardless of
    seed. That reproducibility-under-randomness is itself the point being
    demonstrated, not just a UI gimmick."""
    var_names, Q = build_qubo(scenarios, findings)
    sa_bits, sa_energy = solve_simulated_annealing(var_names, Q, seed=seed)
    result = {
        "variables": var_names,
        "assignment": decode(var_names, sa_bits),
        "energy": round(sa_energy, 4),
        "seed": seed,
        "method": "simulated_annealing (quantum-inspired; drop-in replaceable with real quantum annealer / QAOA)",
    }
    if verify:
        bf_bits, bf_energy = solve_bruteforce(var_names, Q)
        result["bruteforce_verification"] = {
            "assignment": decode(var_names, bf_bits),
            "energy": round(bf_energy, 4),
            "matches_annealer": bool(abs(bf_energy - sa_energy) < 1e-6),
        }
        result["degeneracy"] = analyze_degeneracy(var_names, Q)
    selected_scenario = next((v[2:] for v, b in zip(var_names, sa_bits) if v.startswith("x_") and b == 1), None)
    result["selected_scenario"] = selected_scenario
    result["trusted_evidence"] = [v[2:] for v, b in zip(var_names, sa_bits) if v.startswith("z_") and b == 1]
    result["distrusted_evidence"] = [v[2:] for v, b in zip(var_names, sa_bits) if v.startswith("z_") and b == 0]
    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from digital_twin.twin import DigitalTwin
    from agents.coordinator import run_agents

    case_path = Path(__file__).parent.parent / "data" / "case_QSFIN_2026_0417.json"
    with open(case_path) as f:
        case_data = json.load(f)
    twin = DigitalTwin(case_data)
    bb = run_agents(twin, case_data)

    result = run(case_data["candidate_scenarios"], bb.findings)

    print("=== Quantum-inspired QUBO scenario/evidence optimization ===\n")
    print(f"Variables ({len(result['variables'])}): {result['variables']}\n")
    print(f"Annealer energy: {result['energy']}")
    if "bruteforce_verification" in result:
        bfv = result["bruteforce_verification"]
        print(f"Brute-force optimum energy: {bfv['energy']}  "
              f"(annealer matches exact optimum: {bfv['matches_annealer']})")
    print(f"\nSelected scenario: {result['selected_scenario']}")
    print(f"Trusted evidence: {result['trusted_evidence']}")
    print(f"Flagged/distrusted evidence: {result['distrusted_evidence']}")

    out_path = Path(__file__).parent / "optimization_result.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nExported -> {out_path}")
