"""
QSFIN — Federated learning simulation across agencies.

The scenario: 4 simulated agencies each hold their own historical case
records (data/agencies/*.json) and want a shared model that predicts case
resolution likelihood from case features — useful for triaging which
pending cases most need forensic-resource priority. No agency is willing
(or, in India, often legally/institutionally able) to hand its raw case
data to the others or to a central server.

Federated averaging (FedAvg) solves this: each agency trains locally on
its own data for a few epochs, sends only the resulting model *parameters*
(a handful of numbers) to a coordinator, the coordinator averages them
(weighted by how much data each agency has) into a new global model, and
sends that back out for another round of local training. Raw case data
never leaves its agency.

This script proves the concept end-to-end on synthetic data and reports:
  - each agency's local-only model accuracy (what they'd get alone)
  - the federated global model's accuracy on each agency's local test data
  - a fully-centralized model trained on all pooled data, as the
    theoretical ceiling federated learning is trying to approach without
    actually pooling data
"""
import json
import zlib
from pathlib import Path

import numpy as np

from federated.model import LogisticRegression


def _stable_seed(text: str) -> int:
    """A deterministic string->int seed. Python's built-in hash() is
    randomized per-process (PYTHONHASHSEED) for security reasons, which
    silently made the train/test split — and therefore every reported
    accuracy number — different on every server restart. That's a real
    reproducibility bug for a research prototype: results should depend on
    the data, not on when the process happened to start. zlib.crc32 is
    stable across processes, platforms, and Python versions."""
    return zlib.crc32(text.encode("utf-8")) % 1000

FEATURES = ["num_suspects", "evidence_strength", "days_to_forensic_report",
            "has_digital_evidence", "has_witness", "prior_offender_link"]


def load_agency(path: Path):
    with open(path) as f:
        data = json.load(f)
    cases = data["cases"]
    X = np.array([[c[f] for f in FEATURES] for c in cases], dtype=float)
    y = np.array([c["resolved"] for c in cases], dtype=float)
    return data["agency_id"], data["agency_name"], X, y


def normalize(X, mean=None, std=None):
    if mean is None:
        mean, std = X.mean(axis=0), X.std(axis=0)
        std[std == 0] = 1.0
    return (X - mean) / std, mean, std


def train_test_split(X, y, test_frac=0.25, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    n_test = int(len(X) * test_frac)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], y[train_idx], X[test_idx], y[test_idx]


def run_federated_simulation(rounds=15, local_epochs=5, lr=0.3):
    agency_dir = Path(__file__).parent.parent / "data" / "agencies"
    agency_files = sorted(agency_dir.glob("AG-*_local_cases.json"))

    agencies = []
    all_X, all_y = [], []
    for path in agency_files:
        agency_id, name, X, y = load_agency(path)
        agencies.append({"agency_id": agency_id, "name": name, "X": X, "y": y})
        all_X.append(X)
        all_y.append(y)

    # Normalize using GLOBAL feature statistics computed once and shared as
    # part of the protocol setup (this is standard practice; it's not raw
    # case data, just feature-scale metadata) so all agencies' models speak
    # the same coordinate system.
    all_X_concat = np.vstack(all_X)
    _, mean, std = normalize(all_X_concat)

    for a in agencies:
        Xn, _, _ = normalize(a["X"], mean, std)
        Xtr, ytr, Xte, yte = train_test_split(Xn, a["y"], seed=_stable_seed(a["agency_id"]))
        a.update({"Xtr": Xtr, "ytr": ytr, "Xte": Xte, "yte": yte})

    n_features = len(FEATURES)

    # ---- 1. Local-only baselines (what each agency gets training alone) ----
    local_only_results = {}
    for a in agencies:
        m = LogisticRegression(n_features, seed=1)
        m.train_epochs(a["Xtr"], a["ytr"], epochs=200, lr=lr)
        local_only_results[a["agency_id"]] = round(m.accuracy(a["Xte"], a["yte"]), 4)

    # ---- 2. Fully centralized baseline (pooled raw data — the thing we're trying to avoid needing) ----
    Xtr_all = np.vstack([a["Xtr"] for a in agencies])
    ytr_all = np.concatenate([a["ytr"] for a in agencies])
    central_model = LogisticRegression(n_features, seed=1)
    central_model.train_epochs(Xtr_all, ytr_all, epochs=200, lr=lr)
    centralized_results = {a["agency_id"]: round(central_model.accuracy(a["Xte"], a["yte"]), 4) for a in agencies}

    # ---- 3. Federated averaging over communication rounds ----
    global_model = LogisticRegression(n_features, seed=1)
    total_n = sum(len(a["Xtr"]) for a in agencies)
    history = []

    for r in range(rounds):
        local_params = []
        weights = []
        for a in agencies:
            local_model = LogisticRegression(n_features, seed=1)
            local_model.set_params(global_model.get_params())
            local_model.train_epochs(a["Xtr"], a["ytr"], epochs=local_epochs, lr=lr)
            local_params.append(local_model.get_params())
            weights.append(len(a["Xtr"]) / total_n)

        # FedAvg: weighted average of parameter vectors. This one line is
        # the entire "federated" part of federated learning — everything
        # else is bookkeeping. No agency's raw X, y ever appears here.
        new_params = np.average(np.stack(local_params), axis=0, weights=weights)
        global_model.set_params(new_params)

        round_acc = {a["agency_id"]: round(global_model.accuracy(a["Xte"], a["yte"]), 4) for a in agencies}
        avg_acc = round(np.mean(list(round_acc.values())), 4)
        history.append({"round": r + 1, "per_agency_accuracy": round_acc, "mean_accuracy": avg_acc})

    federated_final = history[-1]["per_agency_accuracy"]

    result = {
        "features_used": FEATURES,
        "agencies": [{"agency_id": a["agency_id"], "name": a["name"],
                      "n_train": len(a["Xtr"]), "n_test": len(a["Xte"])} for a in agencies],
        "local_only_accuracy": local_only_results,
        "centralized_pooled_accuracy": centralized_results,
        "federated_accuracy_final_round": federated_final,
        "federated_training_history": history,
        "mean_local_only": round(float(np.mean(list(local_only_results.values()))), 4),
        "mean_centralized": round(float(np.mean(list(centralized_results.values()))), 4),
        "mean_federated": round(float(np.mean(list(federated_final.values()))), 4),
    }
    return result


if __name__ == "__main__":
    result = run_federated_simulation()

    print("=== Federated learning simulation across simulated agencies ===\n")
    print(f"{'Agency':<10} {'Local-only':>12} {'Federated':>12} {'Centralized':>13}")
    for aid in result["local_only_accuracy"]:
        print(f"{aid:<10} {result['local_only_accuracy'][aid]:>12.3f} "
              f"{result['federated_accuracy_final_round'][aid]:>12.3f} "
              f"{result['centralized_pooled_accuracy'][aid]:>13.3f}")
    print(f"\n{'MEAN':<10} {result['mean_local_only']:>12.3f} "
          f"{result['mean_federated']:>12.3f} {result['mean_centralized']:>13.3f}")
    print("\nInterpretation: federated accuracy should sit close to the centralized-pooled\n"
          "ceiling and above each agency's local-only baseline, WITHOUT any agency's raw\n"
          "case records ever having been shared — only model parameters were exchanged,\n"
          "each round, in the FedAvg loop above.")

    out_path = Path(__file__).parent / "federated_result.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nExported -> {out_path}")
