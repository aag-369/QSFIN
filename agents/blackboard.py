"""
Shared blackboard: the common workspace all agents write their Findings
to, and that the reasoning layer reads from. Using a shared blackboard
(a classic multi-agent-systems pattern) rather than direct agent-to-agent
calls keeps agents decoupled — each one only needs to know how to read the
case/digital-twin and write Findings, not what any other agent is doing.
"""
from agents.base import Finding


class Blackboard:
    def __init__(self):
        self.findings: list[Finding] = []

    def post(self, findings: list[Finding]):
        self.findings.extend(findings)

    def by_agent(self, agent_name: str) -> list[Finding]:
        return [f for f in self.findings if f.agent == agent_name]

    def supporting(self, scenario_id: str) -> list[Finding]:
        return [f for f in self.findings if scenario_id in f.supports]

    def contradicting(self, scenario_id: str) -> list[Finding]:
        return [f for f in self.findings if scenario_id in f.contradicts]

    def to_dict(self) -> list[dict]:
        return [f.to_dict() for f in self.findings]
