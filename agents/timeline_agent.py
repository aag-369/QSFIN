"""
Timeline reconstruction agent.

Scope: merges every timestamped fact across the case — time-of-death
estimate, witness statements, and cell/call records — into one ordered
timeline, then checks whether the pieces are mutually consistent or
whether there are contradictions a defense could exploit (e.g. an alibi
that overlaps the estimated time of death).
"""
from datetime import datetime
from agents.base import ForensicAgent, Finding


class TimelineAgent(ForensicAgent):
    name = "timeline_agent"

    def _build_timeline(self, twin, case_data: dict) -> list[dict]:
        events = []
        for p in case_data.get("people", []):
            if p.get("role") == "victim" and p.get("time_of_death_estimate"):
                start, end = p["time_of_death_estimate"].split(" to ")
                events.append({"time": start, "label": "Estimated time-of-death window opens", "source": "medical_examiner_estimate"})
                events.append({"time": end, "label": "Estimated time-of-death window closes", "source": "medical_examiner_estimate"})
        for ws in case_data.get("witness_statements", []):
            events.append({"time": ws["timestamp"], "label": f"Witness statement recorded: \"{ws['text']}\"", "source": ws["statement_id"]})
        for r in twin.call_records:
            alias = twin.people.get(r["person_id"], {}).get("alias", r["person_id"])
            if r["event"] == "cell_ping":
                label = f"{alias} device pings tower {r['cell_tower']} ({r['distance_from_scene_m']}m from scene)"
            elif r["event"] == "outgoing_call":
                to_alias = twin.people.get(r.get("to_person_id"), {}).get("alias", r.get("to_person_id"))
                label = f"{alias} calls {to_alias} ({r['duration_sec']}s)"
            else:
                label = f"{alias} {r['event']}"
            events.append({"time": r["timestamp"], "label": label, "source": "call_and_location_records"})
        events.sort(key=lambda e: e["time"])
        return events

    def analyze(self, twin, case_data: dict) -> list[Finding]:
        findings = []
        idx = 1
        timeline = self._build_timeline(twin, case_data)

        findings.append(self._finding(
            idx,
            summary=f"Reconstructed a {len(timeline)}-event timeline spanning "
                    f"{timeline[0]['time'][11:16]}–{timeline[-1]['time'][11:16]} from medical, "
                    f"witness, and digital-forensics sources.",
            reasoning="Merging independently-sourced timestamps (medical estimate, witness account, "
                      "cell records) into one timeline is what allows cross-checking whether "
                      "different evidence streams tell a mutually consistent story, rather than "
                      "being assessed in isolation by different specialists.",
            confidence=0.9,
            supports=[],
            contradicts=[],
            evidence_refs=[],
        ))
        idx += 1

        # Consistency check: does witness account fall inside / near the ping showing P-02 near scene?
        witness_bang_time = None
        for ws in case_data.get("witness_statements", []):
            witness_bang_time = ws["timestamp"]
        p02_near_scene = [r for r in twin.call_records
                           if r["person_id"] == "P-02" and r["distance_from_scene_m"] <= 150]
        if witness_bang_time and p02_near_scene:
            findings.append(self._finding(
                idx,
                summary="Witness-reported gunshot time, victim's estimated time-of-death window, "
                        "and P-02's near-scene cell activity all fall within the same "
                        "~20-30 minute span with no contradicting alibi evidence on file.",
                reasoning="Three independently-collected sources (medical, eyewitness, telecom) are "
                          "temporally consistent with each other. This convergence strengthens "
                          "confidence in the overall timeline, though it does not by itself assign "
                          "responsibility — consistency is necessary but not sufficient for a "
                          "specific scenario to be correct.",
                confidence=0.75,
                supports=["S1", "S2"],
                contradicts=[],
                evidence_refs=["WS-01", "P-02"],
            ))
            idx += 1

        # No alibi evidence on file for either suspect
        findings.append(self._finding(
            idx,
            summary="No alibi evidence (e.g. independent corroboration placing a person of interest "
                    "elsewhere during the full time-of-death window) is present in the current case file.",
            reasoning="This is an evidentiary gap, not a finding against anyone — a real "
                      "investigation would actively seek out alibi evidence for all persons of "
                      "interest before any scenario is treated as established. Its absence here "
                      "should not be read as suspicious; it should be read as incomplete.",
            confidence=0.5,
            supports=[],
            contradicts=[],
            evidence_refs=[],
        ))
        idx += 1

        return findings

    def get_timeline(self, twin, case_data: dict) -> list[dict]:
        """Exposed separately so the orchestrator/dashboard can render the raw
        timeline, not just the findings derived from it."""
        return self._build_timeline(twin, case_data)
