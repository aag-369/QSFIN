"""
QSFIN — Multi-agent forensic analysis framework, shared base classes.

Design principle: instead of one large model trying to reason about an
entire case, each agent is narrow and auditable — it looks at one slice of
the evidence, and produces structured Findings with an explicit reasoning
trail. This mirrors how a real investigative team is organized (a
ballistics expert doesn't also do cell-tower analysis), and it means any
single agent's logic can be inspected, tested, and challenged in isolation
— which matters a great deal if this is ever used to support a legal
proceeding.

Findings, not verdicts: agents never output "guilty" — they output
evidence-grounded observations that support or contradict specific
candidate scenarios, with a confidence and a plain-language reason. The
reasoning layer (see reasoning/) is what combines many agents' findings
into an overall picture.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    agent: str
    finding_id: str
    summary: str
    reasoning: str
    confidence: float  # 0.0-1.0, this agent's own confidence in the finding
    supports: list = field(default_factory=list)     # scenario_ids this finding supports
    contradicts: list = field(default_factory=list)  # scenario_ids this finding contradicts
    evidence_refs: list = field(default_factory=list)  # evidence_id / person_id references

    def to_dict(self):
        return {
            "agent": self.agent,
            "finding_id": self.finding_id,
            "summary": self.summary,
            "reasoning": self.reasoning,
            "confidence": round(self.confidence, 3),
            "supports": self.supports,
            "contradicts": self.contradicts,
            "evidence_refs": self.evidence_refs,
        }


class ForensicAgent:
    """Base class every specialized agent implements."""
    name = "base_agent"

    def analyze(self, twin, case_data: dict) -> list[Finding]:
        raise NotImplementedError

    def _finding(self, idx: int, **kwargs) -> Finding:
        return Finding(agent=self.name, finding_id=f"{self.name}-{idx:02d}", **kwargs)
