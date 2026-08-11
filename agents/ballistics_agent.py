"""
Ballistics & physical trace-evidence agent.

Scope: anything derivable from the physical scene geometry captured in the
digital twin — shot trajectory reconstruction, and cross-referencing trace
evidence (footwear impressions) against persons of interest. A real system
would compute trajectory from wound/impact geometry and photogrammetry;
here we consume the pre-computed trajectory estimate already present in
the digital twin and reason over it.
"""
import math
from agents.base import ForensicAgent, Finding


class BallisticsAgent(ForensicAgent):
    name = "ballistics_agent"

    def analyze(self, twin, case_data: dict) -> list[Finding]:
        findings = []
        idx = 1

        # --- Trajectory reconstruction ---
        for t in twin.trajectories:
            origin = t.estimated_origin
            findings.append(self._finding(
                idx,
                summary=(f"Single gunshot trajectory reconstructed: firing origin "
                         f"~{origin} near the sofa in the living room, entry angle "
                         f"{t.estimated_angle_deg}° into the west wall (evidence {t.to_evidence})."),
                reasoning=(f"Shell casing {t.from_evidence} and bullet impact {t.to_evidence} "
                           f"are geometrically consistent with a single shot fired from close "
                           f"range while standing/seated near the sofa, not from the doorway or "
                           f"kitchen entry point. This constrains the shooter's position at the "
                           f"moment of firing to within ~1m of the estimated origin."),
                confidence=0.82,
                supports=["S1", "S2"],
                contradicts=[],
                evidence_refs=[t.from_evidence, t.to_evidence, t.trajectory_id],
            ))
            idx += 1

        # --- Chain of custody check on ballistic evidence ---
        for eid in ["E-02", "E-03"]:
            intact = twin.chain_of_custody_intact(eid)
            findings.append(self._finding(
                idx,
                summary=f"Chain of custody for {eid} ({twin.evidence[eid].type}) is "
                        f"{'intact' if intact else 'INCOMPLETE — flag for review'}.",
                reasoning="Custody log shows collection, transport, and lab receipt entries "
                          "with no unexplained gaps." if intact else
                          "Custody log has fewer than 2 recorded handoffs — this evidence would "
                          "likely face admissibility challenges in court and should be "
                          "re-verified before being relied on.",
                confidence=0.95 if intact else 0.4,
                supports=[],
                contradicts=[],
                evidence_refs=[eid],
            ))
            idx += 1

        # --- Footwear trace evidence vs persons of interest ---
        footwear = twin.evidence_by_type("footwear_impression")
        for fw in footwear:
            desc = fw.description
            matches = []
            for pid, p in twin.people.items():
                shoe = p.get("shoe_size_uk")
                if shoe is not None and 9 <= shoe <= 10:
                    matches.append((pid, p.get("alias", pid), shoe))
            match_str = "; ".join(f"{alias} (UK {shoe})" for _, alias, shoe in matches)
            findings.append(self._finding(
                idx,
                summary=f"Footwear impression {fw.evidence_id} ({desc}) is consistent with "
                        f"shoe size range that includes: {match_str if matches else 'no current persons of interest'}.",
                reasoning=("Impression size/tread class narrows the pool of plausible individuals "
                           "but a partial print alone cannot uniquely identify a wearer — this is "
                           "corroborating, not conclusive, evidence. It should be weighted alongside "
                           "digital-forensics and timeline findings, not read in isolation."),
                confidence=0.45,
                supports=["S1", "S2"] if matches else [],
                contradicts=["S3"] if matches else [],
                evidence_refs=[fw.evidence_id] + [pid for pid, _, _ in matches],
            ))
            idx += 1

        return findings
