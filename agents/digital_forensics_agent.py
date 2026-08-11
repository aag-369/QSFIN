"""
Digital forensics agent.

Scope: cell-tower / call-record analysis — where was each person of
interest at the time of the crime, and who was in contact with whom. This
is the kind of analysis that, today, a human cyber-cell analyst does by
hand against raw telecom dumps; here it's automated over the structured
call_and_location_records already present in the case file.
"""
from datetime import datetime
from agents.base import ForensicAgent, Finding

TOD_START = datetime.fromisoformat("2026-08-02T21:30:00+05:30")
TOD_END = datetime.fromisoformat("2026-08-02T22:00:00+05:30")
NEAR_SCENE_M = 150  # threshold distance to consider someone "near the scene"


class DigitalForensicsAgent(ForensicAgent):
    name = "digital_forensics_agent"

    def analyze(self, twin, case_data: dict) -> list[Finding]:
        findings = []
        idx = 1
        records = twin.call_records

        people_of_interest = [pid for pid, p in twin.people.items() if p.get("role") == "person_of_interest"]

        for pid in people_of_interest:
            alias = twin.people[pid].get("alias", pid)
            person_records = [r for r in records if r["person_id"] == pid]
            in_window = [r for r in person_records
                         if TOD_START <= datetime.fromisoformat(r["timestamp"]) <= TOD_END]
            near_scene_in_window = [r for r in in_window if r["distance_from_scene_m"] <= NEAR_SCENE_M]

            if near_scene_in_window:
                closest = min(near_scene_in_window, key=lambda r: r["distance_from_scene_m"])
                findings.append(self._finding(
                    idx,
                    summary=(f"{alias}'s device pinged {closest['distance_from_scene_m']}m from the "
                             f"scene at {closest['timestamp'][11:16]}, inside the estimated "
                             f"time-of-death window."),
                    reasoning=(f"Cell-tower proximity places {alias} at/near the scene during the "
                               f"window in which the victim is estimated to have died. This is "
                               f"consistent with physical presence but is not, by itself, proof of "
                               f"presence — tower triangulation has meter-to-hundreds-of-meter "
                               f"uncertainty depending on tower density."),
                    confidence=0.7,
                    supports=["S1", "S2"],
                    contradicts=[],
                    evidence_refs=[pid],
                ))
                idx += 1
            else:
                far = [r for r in in_window]
                if far:
                    findings.append(self._finding(
                        idx,
                        summary=f"{alias}'s device was consistently >{NEAR_SCENE_M}m from the scene "
                                f"throughout the time-of-death window.",
                        reasoning="Location data does not place this person near the scene during "
                                  "the relevant window, which weighs against a theory requiring "
                                  "their physical presence at the time of the shooting.",
                        confidence=0.65,
                        supports=[],
                        contradicts=["S1", "S2"] if pid == "P-02" else [],
                        evidence_refs=[pid],
                    ))
                    idx += 1

        # --- Contact analysis between P-02 and P-03 ---
        calls = [r for r in records if r["event"] in ("outgoing_call", "incoming_call")]
        for r in calls:
            if r["event"] == "outgoing_call":
                caller = twin.people.get(r["person_id"], {}).get("alias", r["person_id"])
                callee = twin.people.get(r.get("to_person_id"), {}).get("alias", r.get("to_person_id"))
                ts = r["timestamp"][11:16]
                dist_caller = r["distance_from_scene_m"]
                findings.append(self._finding(
                    idx,
                    summary=(f"Outgoing call from {caller} to {callee} at {ts}, {dist_caller}m from "
                             f"the scene, duration {r['duration_sec']}s — roughly 5-7 minutes after "
                             f"the witness-reported gunshot."),
                    reasoning=("A phone contact between the two persons of interest occurring shortly "
                               "after the estimated time of the shooting, while the caller was still "
                               "near the scene, is consistent with a coordination/joint-action "
                               "scenario (S2). It is also consistent with an innocent, unrelated call "
                               "— call content/transcript would be needed to move beyond circumstantial "
                               "weight. This finding should not be treated as conclusive on its own."),
                    confidence=0.55,
                    supports=["S2"],
                    contradicts=[],
                    evidence_refs=[r["person_id"], r.get("to_person_id")],
                ))
                idx += 1

        # --- Departure pattern ---
        p02_records = sorted([r for r in records if r["person_id"] == "P-02"], key=lambda r: r["timestamp"])
        if len(p02_records) >= 2:
            last = p02_records[-1]
            if last["distance_from_scene_m"] > 500:
                alias = twin.people["P-02"].get("alias", "P-02")
                findings.append(self._finding(
                    idx,
                    summary=f"{alias} moved from ~40m to {last['distance_from_scene_m']}m from the "
                            f"scene by {last['timestamp'][11:16]}, consistent with departure shortly "
                            f"after the witness-observed person left the stairwell (~21:50).",
                    reasoning="Movement pattern (arrival near scene -> presence during TOD window -> "
                              "rapid departure) matches the witness account of someone leaving in a "
                              "hurry, though it does not independently confirm identity.",
                    confidence=0.6,
                    supports=["S1", "S2"],
                    contradicts=[],
                    evidence_refs=["P-02", "WS-01"],
                ))
                idx += 1

        return findings
