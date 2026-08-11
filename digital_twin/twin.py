"""
QSFIN — Digital Twin module.

Wraps a crime-scene case file (see data/case_*.json) into a queryable
"digital twin": a persistent structured model of the scene that downstream
agents and the reasoning layer can interrogate, instead of a one-time
photograph set that degrades in usefulness the moment the physical scene
is released.

In a production system this would be populated from LiDAR point clouds,
photogrammetry meshes, and IoT/sensor feeds. Here it's populated from a
structured JSON case file (rooms, evidence markers, trajectories) which is
the same shape that real capture pipelines would ultimately produce after
processing raw scan data — so this module is the layer everything else
plugs into regardless of how the geometry was captured.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class EvidenceMarker:
    evidence_id: str
    type: str
    room: str
    position: list
    description: str
    collected_by: str
    chain_of_custody: list


@dataclass
class Room:
    room_id: str
    dimensions_m: list
    origin: list


@dataclass
class Trajectory:
    trajectory_id: str
    from_evidence: str
    to_evidence: str
    type: str
    estimated_origin: list
    estimated_angle_deg: float
    note: str


class DigitalTwin:
    """A queryable digital twin of one crime scene."""

    def __init__(self, case_data: dict):
        self.case_id = case_data["case_id"]
        self.title = case_data.get("title", "")
        scene = case_data["scene"]
        self.scene_id = scene["scene_id"]
        self.capture_method = scene.get("capture_method", [])
        self.rooms = {r["room_id"]: Room(**r) for r in scene["rooms"]}
        self.evidence = {e["evidence_id"]: EvidenceMarker(**e) for e in scene["evidence_markers"]}
        self.trajectories = [Trajectory(**t) for t in scene.get("trajectories", [])]
        self.people = {p["person_id"]: p for p in case_data.get("people", [])}
        self.call_records = case_data.get("call_and_location_records", [])
        self.witness_statements = case_data.get("witness_statements", [])
        self.candidate_scenarios = case_data.get("candidate_scenarios", [])
        self._raw = case_data

    @classmethod
    def from_file(cls, path: str) -> "DigitalTwin":
        with open(path) as f:
            return cls(json.load(f))

    # ---- Query API -------------------------------------------------

    def evidence_in_room(self, room_id: str) -> list[EvidenceMarker]:
        return [e for e in self.evidence.values() if e.room == room_id]

    def evidence_by_type(self, evidence_type: str) -> list[EvidenceMarker]:
        return [e for e in self.evidence.values() if e.type == evidence_type]

    def distance(self, evidence_id_a: str, evidence_id_b: str) -> float:
        a = self.evidence[evidence_id_a].position
        b = self.evidence[evidence_id_b].position
        return math.dist(a, b)

    def chain_of_custody_intact(self, evidence_id: str) -> bool:
        """Very simplified integrity check: at least 2 custody handoffs recorded
        with monotonically-labelled timestamps present. A production version
        would verify cryptographic hashes / signed timestamps per handoff."""
        marker = self.evidence[evidence_id]
        return len(marker.chain_of_custody) >= 2

    def trajectory_for(self, evidence_id: str) -> Optional[Trajectory]:
        for t in self.trajectories:
            if evidence_id in (t.from_evidence, t.to_evidence):
                return t
        return None

    def person_location_events(self, person_id: str) -> list[dict]:
        return [r for r in self.call_records if r.get("person_id") == person_id]

    def summary(self) -> dict:
        return {
            "case_id": self.case_id,
            "scene_id": self.scene_id,
            "n_rooms": len(self.rooms),
            "n_evidence": len(self.evidence),
            "n_trajectories": len(self.trajectories),
            "n_people": len(self.people),
            "capture_method": self.capture_method,
            "evidence_types": sorted({e.type for e in self.evidence.values()}),
        }

    # ---- Export for visualization -----------------------------------

    def to_render_json(self) -> dict:
        """Produce a render-ready scene description consumed by the
        three.js digital-twin viewer (digital_twin/scene_viewer.html)."""
        color_map = {
            "blood_spatter": "#c0392b",
            "shell_casing": "#f1c40f",
            "bullet_impact": "#e67e22",
            "footwear_impression": "#2980b9",
            "mobile_device": "#8e44ad",
            "fingerprint": "#16a085",
        }
        return {
            "case_id": self.case_id,
            "title": self.title,
            "rooms": [
                {"room_id": r.room_id, "dimensions_m": r.dimensions_m, "origin": r.origin}
                for r in self.rooms.values()
            ],
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "type": e.type,
                    "room": e.room,
                    "position": e.position,
                    "description": e.description,
                    "color": color_map.get(e.type, "#95a5a6"),
                    "chain_of_custody": e.chain_of_custody,
                }
                for e in self.evidence.values()
            ],
            "trajectories": [
                {
                    "trajectory_id": t.trajectory_id,
                    "from": self.evidence[t.from_evidence].position,
                    "to": self.evidence[t.to_evidence].position,
                    "estimated_origin": t.estimated_origin,
                    "angle_deg": t.estimated_angle_deg,
                    "note": t.note,
                }
                for t in self.trajectories
            ],
        }

    def export_render_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_render_json(), f, indent=2)


if __name__ == "__main__":
    case_path = Path(__file__).parent.parent / "data" / "case_QSFIN_2026_0417.json"
    twin = DigitalTwin.from_file(str(case_path))
    print(json.dumps(twin.summary(), indent=2))
    out_path = Path(__file__).parent / "scene_render.json"
    twin.export_render_json(str(out_path))
    print(f"\nExported render JSON -> {out_path}")
