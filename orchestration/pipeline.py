"""
QSFIN — end-to-end orchestration pipeline.

Takes a case file all the way through: digital twin construction -> multi-
agent analysis -> neuro-symbolic reasoning -> quantum-inspired scenario/
evidence optimization -> one structured case report. This is the single
entry point a real "run QSFIN on this case" command would call; every
module built so far (digital_twin/, agents/, reasoning/, optimization/)
is a library this script composes rather than duplicates.

Federated learning (federated/) is intentionally NOT part of this
per-case pipeline: it's a background, cross-case capability (agencies
periodically improve a shared triage model together) rather than a step
in analyzing one specific case, so it's run/reported separately.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.twin import DigitalTwin
from agents.coordinator import run_agents, AGENTS
from reasoning.engine import assess_scenarios
from optimization.qubo_scorer import run as run_qubo


def analyze_case(case_data: dict) -> dict:
    twin = DigitalTwin(case_data)

    blackboard = run_agents(twin, case_data)
    assessments = assess_scenarios(blackboard, twin, case_data)
    qubo_result = run_qubo(case_data["candidate_scenarios"], blackboard.findings)

    reasoning_top = assessments[0]
    qubo_scenario = qubo_result["selected_scenario"]

    agreement = (reasoning_top.scenario_id == qubo_scenario)

    report = {
        "case_id": case_data["case_id"],
        "title": case_data["title"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "QSFIN-prototype-0.1",
        "digital_twin_summary": twin.summary(),
        "agents_run": [a.name for a in AGENTS],
        "total_findings": len(blackboard.findings),
        "findings": blackboard.to_dict(),
        "reasoning_layer": {
            "method": "neuro-symbolic (statistical aggregation + explicit named rules)",
            "ranking": [a.to_dict() for a in assessments],
            "top_scenario": reasoning_top.scenario_id,
        },
        "optimization_layer": {
            "method": qubo_result["method"],
            "result": qubo_result,
            "selected_scenario": qubo_scenario,
        },
        "cross_check": {
            "reasoning_layer_top_scenario": reasoning_top.scenario_id,
            "optimization_layer_selected_scenario": qubo_scenario,
            "agree": agreement,
            "note": (
                "The two layers agree on the leading scenario."
                if agreement else
                "The two layers disagree. This is expected and useful, not a bug: the "
                "reasoning layer aggregates ALL agent findings (ballistics, digital "
                "forensics, network, timeline), while the optimization layer jointly "
                "reasons only over scenario selection AND physical-evidence trust "
                "(ballistics-derived evidence). A disagreement flags that the case's "
                "physical evidence alone points one way while the fuller picture "
                "(including phone/network circumstantial evidence) points another way — "
                "exactly the kind of tension a human investigator/prosecutor needs "
                "surfaced explicitly, not resolved silently by an opaque system."
            ),
        },
        "human_readable_summary": _build_summary(case_data, assessments, qubo_result, agreement, len(blackboard.findings)),
    }
    return report


def _build_summary(case_data, assessments, qubo_result, agreement, n_findings) -> str:
    top = assessments[0]
    lines = [
        f"Case {case_data['case_id']}: {len(assessments)} candidate scenarios evaluated "
        f"against {n_findings} findings from {len(AGENTS)} specialized agents.",
        f"Neuro-symbolic reasoning layer ranks '{top.scenario_id}' highest "
        f"(adjusted score {top.adjusted_score:+.2f}): {top.summary}",
        f"Quantum-inspired joint scenario/evidence optimizer selects '{qubo_result['selected_scenario']}', "
        f"trusting evidence {qubo_result['trusted_evidence']}"
        + (f" and flagging {qubo_result['distrusted_evidence']} for review." if qubo_result['distrusted_evidence'] else "."),
        "The two layers AGREE on the leading scenario." if agreement else
        "The two layers DISAGREE — see cross_check note for why, and treat this as a "
        "flag for human review rather than a system failure.",
        "This output is a decision-SUPPORT artifact: every number above is traceable to "
        "a specific, named agent finding and a specific, named symbolic rule. Nothing here "
        "is a verdict, and none of it should be treated as one.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    case_path = Path(__file__).parent.parent / "data" / "case_QSFIN_2026_0417.json"
    with open(case_path) as f:
        case_data = json.load(f)

    report = analyze_case(case_data)

    print(report["human_readable_summary"])
    print()

    out_path = Path(__file__).parent / "case_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull structured report -> {out_path}")
