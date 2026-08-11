"""
Multi-agent coordinator: runs every specialized agent against the case's
digital twin, posts their Findings to the shared blackboard, and returns
it for the reasoning layer to consume.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.twin import DigitalTwin
from agents.ballistics_agent import BallisticsAgent
from agents.digital_forensics_agent import DigitalForensicsAgent
from agents.network_agent import NetworkAgent
from agents.timeline_agent import TimelineAgent
from agents.blackboard import Blackboard

AGENTS = [BallisticsAgent(), DigitalForensicsAgent(), NetworkAgent(), TimelineAgent()]


def run_agents(twin: DigitalTwin, case_data: dict) -> Blackboard:
    bb = Blackboard()
    for agent in AGENTS:
        findings = agent.analyze(twin, case_data)
        bb.post(findings)
    return bb


if __name__ == "__main__":
    case_path = Path(__file__).parent.parent / "data" / "case_QSFIN_2026_0417.json"
    with open(case_path) as f:
        case_data = json.load(f)
    twin = DigitalTwin(case_data)
    bb = run_agents(twin, case_data)

    print(f"Ran {len(AGENTS)} agents, {len(bb.findings)} findings total.\n")
    for agent in AGENTS:
        agent_findings = bb.by_agent(agent.name)
        print(f"--- {agent.name} ({len(agent_findings)} findings) ---")
        for f in agent_findings:
            print(f"  [{f.finding_id}] conf={f.confidence:.2f} supports={f.supports} contradicts={f.contradicts}")
            print(f"    {f.summary}")
        print()

    out_path = Path(__file__).parent / "findings.json"
    with open(out_path, "w") as f:
        json.dump(bb.to_dict(), f, indent=2)
    print(f"Exported findings -> {out_path}")
