"""
QSFIN — Neuro-symbolic explainable reasoning layer.

This is the module that makes the whole system's output usable in a legal
context rather than just an investigative dashboard. It deliberately keeps
two things separate and both visible in the output:

  1. THE "NEURAL" PART — a statistical aggregation of agent Finding
     confidences into a raw numeric score per scenario. This is the part
     that behaves like a typical ML system: continuous, weighted,
     approximate.

  2. THE "SYMBOLIC" PART — a small set of explicit, named, human-readable
     rules that adjust and constrain that raw score (e.g. "don't let a
     scenario score highly if it has zero directly supporting findings",
     "discount evidence whose chain of custody is broken"). Each rule
     firing is logged, in plain language, as part of the explanation.

The reason to keep these separate rather than training one opaque model
end-to-end: a court, a defense lawyer, or a review board can be shown
exactly which numeric evidence contributed how much AND which explicit
logical rule shaped the final ranking — "explainable by construction"
rather than "explainable by post-hoc approximation" (which is what most
XAI techniques applied to black-box neural nets have to settle for).
"""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RuleFiring:
    rule_name: str
    scenario_id: str
    explanation: str
    score_delta: float


@dataclass
class ScenarioAssessment:
    scenario_id: str
    summary: str
    raw_score: float          # neural/statistical aggregation, pre-rules
    adjusted_score: float     # after symbolic rules applied
    supporting_findings: list
    contradicting_findings: list
    rule_firings: list
    explanation_chain: list   # ordered plain-language reasoning steps

    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "summary": self.summary,
            "raw_score": round(self.raw_score, 3),
            "adjusted_score": round(self.adjusted_score, 3),
            "supporting_findings": [f.finding_id for f in self.supporting_findings],
            "contradicting_findings": [f.finding_id for f in self.contradicting_findings],
            "rule_firings": [vars(r) for r in self.rule_firings],
            "explanation_chain": self.explanation_chain,
        }


# --------------------------------------------------------------------
# Step 1 (neural / statistical): raw aggregation of Finding confidences
# --------------------------------------------------------------------

def _raw_aggregate(blackboard, scenario_id: str):
    supporting = blackboard.supporting(scenario_id)
    contradicting = blackboard.contradicting(scenario_id)
    support_sum = sum(f.confidence for f in supporting)
    contradict_sum = sum(f.confidence for f in contradicting)
    return support_sum - contradict_sum, supporting, contradicting


# --------------------------------------------------------------------
# Step 2 (symbolic): explicit named rules that adjust the raw score
# --------------------------------------------------------------------

def rule_no_direct_support_caps_score(scenario_id, supporting, contradicting, score):
    """A scenario with zero directly supporting findings cannot be ranked
    above one with actual support, regardless of low contradiction — an
    absence of evidence against something is not evidence for it."""
    if len(supporting) == 0 and score > 0.3:
        capped = 0.3
        return RuleFiring(
            rule_name="no_direct_support_caps_score",
            scenario_id=scenario_id,
            explanation=("This scenario has zero findings that directly support it. Absence of "
                         "contradicting evidence is not the same as positive evidence, so its score "
                         "is capped rather than allowed to rank on low contradiction alone."),
            score_delta=capped - score,
        ), capped
    return None, score


def rule_broken_custody_discounts_support(scenario_id, supporting, contradicting, score, twin):
    """If a supporting finding references evidence whose chain of custody
    is broken, discount that finding's contribution — because it would
    likely be challenged or excluded in court."""
    discount = 0.0
    broken_refs = []
    for f in supporting:
        for ref in f.evidence_refs:
            if ref in twin.evidence and not twin.chain_of_custody_intact(ref):
                discount += f.confidence * 0.5
                broken_refs.append((f.finding_id, ref))
    if discount > 0:
        new_score = score - discount
        return RuleFiring(
            rule_name="broken_custody_discounts_support",
            scenario_id=scenario_id,
            explanation=(f"Supporting finding(s) {', '.join(fid for fid, _ in broken_refs)} rely on "
                         f"evidence with an incomplete chain of custody; their contribution is "
                         f"discounted by 50% since this evidence would likely face admissibility "
                         f"challenges."),
            score_delta=new_score - score,
        ), new_score
    return None, score


def rule_low_confidence_findings_reduced_weight(scenario_id, supporting, contradicting, score):
    """Individually weak findings (confidence < 0.4) should not be allowed
    to swing a conclusion as much as strong ones — already true in the raw
    sum since we use confidence as weight, but we make this explicit and
    flag it in the explanation for transparency."""
    weak = [f for f in supporting + contradicting if f.confidence < 0.4]
    if weak:
        return RuleFiring(
            rule_name="low_confidence_findings_flagged",
            scenario_id=scenario_id,
            explanation=(f"{len(weak)} finding(s) below 0.4 confidence contributed to this score "
                         f"({', '.join(f.finding_id for f in weak)}); they are weighted low but "
                         f"are flagged here so a reviewer can decide whether to exclude them entirely."),
            score_delta=0.0,
        ), score
    return None, score


SYMBOLIC_RULES_SIMPLE = [rule_no_direct_support_caps_score, rule_low_confidence_findings_reduced_weight]


# --------------------------------------------------------------------
# Step 3: plain-language explanation chain construction
# --------------------------------------------------------------------

def _build_explanation_chain(scenario, supporting, contradicting, rule_firings):
    chain = [f"Candidate scenario: {scenario['summary']}"]
    if supporting:
        chain.append(f"{len(supporting)} finding(s) support this scenario:")
        for f in sorted(supporting, key=lambda x: -x.confidence):
            chain.append(f"  • [{f.agent}] {f.summary} (confidence {f.confidence:.2f}) — {f.reasoning}")
    else:
        chain.append("No findings directly support this scenario.")
    if contradicting:
        chain.append(f"{len(contradicting)} finding(s) contradict this scenario:")
        for f in sorted(contradicting, key=lambda x: -x.confidence):
            chain.append(f"  • [{f.agent}] {f.summary} (confidence {f.confidence:.2f}) — {f.reasoning}")
    if rule_firings:
        chain.append("Symbolic adjustments applied:")
        for r in rule_firings:
            chain.append(f"  ⚖ {r.rule_name}: {r.explanation} (Δ{r.score_delta:+.2f})")
    return chain


def assess_scenarios(blackboard, twin, case_data: dict) -> list[ScenarioAssessment]:
    assessments = []
    for scenario in case_data.get("candidate_scenarios", []):
        sid = scenario["scenario_id"]
        raw_score, supporting, contradicting = _raw_aggregate(blackboard, sid)

        score = raw_score
        rule_firings = []

        firing, score = rule_broken_custody_discounts_support(sid, supporting, contradicting, score, twin)
        if firing:
            rule_firings.append(firing)
        for rule_fn in SYMBOLIC_RULES_SIMPLE:
            firing, score = rule_fn(sid, supporting, contradicting, score)
            if firing:
                rule_firings.append(firing)

        chain = _build_explanation_chain(scenario, supporting, contradicting, rule_firings)

        assessments.append(ScenarioAssessment(
            scenario_id=sid,
            summary=scenario["summary"],
            raw_score=raw_score,
            adjusted_score=score,
            supporting_findings=supporting,
            contradicting_findings=contradicting,
            rule_firings=rule_firings,
            explanation_chain=chain,
        ))

    assessments.sort(key=lambda a: a.adjusted_score, reverse=True)
    return assessments


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
    assessments = assess_scenarios(bb, twin, case_data)

    print("=== Scenario ranking (neuro-symbolic reasoning layer) ===\n")
    for a in assessments:
        print(f"[{a.scenario_id}] raw={a.raw_score:+.2f} adjusted={a.adjusted_score:+.2f}  {a.summary}")
    print()
    for a in assessments:
        print(f"\n--- Explanation for {a.scenario_id} ---")
        for line in a.explanation_chain:
            print(line)

    out_path = Path(__file__).parent / "scenario_assessments.json"
    with open(out_path, "w") as f:
        json.dump([a.to_dict() for a in assessments], f, indent=2)
    print(f"\nExported -> {out_path}")
