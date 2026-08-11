"""
QSFIN — Synthetic multi-agency case dataset generator.

Generates historical case records for N simulated forensic/police agencies,
each with its OWN local dataset (never shared directly with the others).
This is the raw material for the federated learning demo: each agency
trains a local model on its own cases, and only model updates (not raw
case data) are combined centrally.

All data is synthetic. Feature meanings are simplified stand-ins for what
a real system would compute from case files (e.g. evidence_strength would
come from real forensic examination results, not a random number).
"""

import json
import random
from pathlib import Path

random.seed(42)

AGENCIES = [
    {"agency_id": "AG-DL", "name": "Simulated Metro Police Dept. (Delhi-style)", "n_cases": 400, "bias": 0.02},
    {"agency_id": "AG-MH", "name": "Simulated State Police Dept. (Maharashtra-style)", "n_cases": 550, "bias": -0.03},
    {"agency_id": "AG-KA", "name": "Simulated State Police Dept. (Karnataka-style)", "n_cases": 300, "bias": 0.05},
    {"agency_id": "AG-CFSL", "name": "Simulated Central Forensic Science Lab", "n_cases": 250, "bias": 0.0},
]

CRIME_TYPES = ["burglary", "assault", "homicide", "robbery", "cyber_fraud", "vehicle_theft"]


def make_case(i, agency_bias):
    crime_type = random.choice(CRIME_TYPES)
    num_suspects = random.choice([0, 1, 1, 2, 2, 3])
    evidence_strength = round(min(1.0, max(0.0, random.gauss(0.5 + agency_bias, 0.2))), 3)
    days_to_forensic_report = max(1, int(random.gauss(45, 20)))  # reflects real backlog delays
    has_digital_evidence = random.random() < 0.55
    has_witness = random.random() < 0.6
    prior_offender_link = random.random() < 0.3

    # Simplified synthetic "ground truth" generating process for case resolution,
    # loosely weighted so evidence_strength / witness / digital evidence matter —
    # NOT a claim about how real case outcomes are determined.
    score = (
        0.45 * evidence_strength
        + 0.15 * has_witness
        + 0.15 * has_digital_evidence
        + 0.1 * prior_offender_link
        - 0.10 * (days_to_forensic_report / 120)
        + random.gauss(0, 0.08)
    )
    resolved = 1 if score > 0.45 else 0

    return {
        "case_id": f"{i:05d}",
        "crime_type": crime_type,
        "num_suspects": num_suspects,
        "evidence_strength": evidence_strength,
        "days_to_forensic_report": days_to_forensic_report,
        "has_digital_evidence": int(has_digital_evidence),
        "has_witness": int(has_witness),
        "prior_offender_link": int(prior_offender_link),
        "resolved": resolved,
    }


def main():
    out_dir = Path(__file__).parent / "agencies"
    out_dir.mkdir(exist_ok=True)

    manifest = []
    for agency in AGENCIES:
        cases = [make_case(i, agency["bias"]) for i in range(agency["n_cases"])]
        path = out_dir / f"{agency['agency_id']}_local_cases.json"
        with open(path, "w") as f:
            json.dump({
                "agency_id": agency["agency_id"],
                "agency_name": agency["name"],
                "synthetic": True,
                "note": "Synthetic data for QSFIN federated learning prototype. Not real case records.",
                "cases": cases,
            }, f, indent=2)
        resolved_rate = sum(c["resolved"] for c in cases) / len(cases)
        manifest.append({"agency_id": agency["agency_id"], "n_cases": len(cases),
                          "resolved_rate": round(resolved_rate, 3), "path": str(path)})
        print(f"{agency['agency_id']}: {len(cases)} cases, resolved_rate={resolved_rate:.3f} -> {path}")

    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
