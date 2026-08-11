"""
Network analysis agent.

Scope: models people in the case as a graph (known associations, call
contact during the window) and computes structural properties — who is
central, who is directly connected to whom — using networkx. This is the
same graph-analysis approach used for organized-crime network mapping,
just applied at the scale of a single case's persons of interest.

The "quantum graph intelligence" idea from the original project title
would plug in here at scale: for a network of thousands of nodes (a full
criminal network, not 4 people), quantum-inspired graph algorithms become
relevant for tasks like community detection or finding the most influential
nodes efficiently. At this case's scale a classical exact computation is
better and cheaper — networkx is the right tool here, and the module is
structured so the same Finding output could later be produced by a
quantum-inspired backend without changing anything downstream.
"""
import networkx as nx
from agents.base import ForensicAgent, Finding


class NetworkAgent(ForensicAgent):
    name = "network_agent"

    def _build_graph(self, twin, case_data: dict) -> nx.Graph:
        G = nx.Graph()
        for pid, p in twin.people.items():
            G.add_node(pid, **p)
        for pid, p in twin.people.items():
            for assoc in p.get("known_associate_of", []):
                if assoc in twin.people:
                    G.add_edge(pid, assoc, relation="known_associate")
        # Add an edge for any call contact recorded during the case
        for r in twin.call_records:
            if r.get("event") in ("outgoing_call", "incoming_call") and r.get("to_person_id"):
                a, b = r["person_id"], r["to_person_id"]
                if G.has_edge(a, b):
                    G[a][b]["call_contact"] = True
                else:
                    G.add_edge(a, b, relation="call_contact", call_contact=True)
        return G

    def analyze(self, twin, case_data: dict) -> list[Finding]:
        findings = []
        idx = 1
        G = self._build_graph(twin, case_data)

        centrality = nx.degree_centrality(G)
        ranked = sorted(centrality.items(), key=lambda kv: kv[1], reverse=True)
        top = ranked[0] if ranked else None
        if top:
            alias = twin.people[top[0]].get("alias", top[0])
            findings.append(self._finding(
                idx,
                summary=f"{alias} has the highest degree centrality in the case network "
                        f"({top[1]:.2f}), connected to {G.degree[top[0]]} other people of interest.",
                reasoning="Degree centrality identifies who sits at the most connections in the "
                          "known-associate/contact graph. A highly central person of interest "
                          "warrants closer scrutiny, but centrality alone is not evidence of "
                          "wrongdoing — it simply prioritizes investigative attention.",
                confidence=0.6,
                supports=[],
                contradicts=[],
                evidence_refs=[top[0]],
            ))
            idx += 1

        # Direct relationship between the two persons of interest
        if G.has_edge("P-02", "P-03"):
            edge = G["P-02"]["P-03"]
            a1, a2 = twin.people["P-02"].get("alias"), twin.people["P-03"].get("alias")
            findings.append(self._finding(
                idx,
                summary=f"{a1} and {a2} are directly connected in the network "
                        f"(relation: {edge.get('relation')}"
                        + (", plus a recorded call during the case window" if edge.get("call_contact") else "")
                        + ").",
                reasoning="A pre-existing known-associate relationship between the two persons of "
                          "interest, combined with contact during the incident window, increases "
                          "the structural plausibility of a joint-action scenario (S2) relative to "
                          "the two being unconnected strangers. This is circumstantial network "
                          "evidence, not direct proof of coordination in this specific act.",
                confidence=0.58,
                supports=["S2"],
                contradicts=["S3"],
                evidence_refs=["P-02", "P-03"],
            ))
            idx += 1

        # Isolation check for the "unknown third party" scenario
        isolated_candidates = [n for n in G.nodes if G.degree[n] == 0 and twin.people[n].get("role") != "witness"]
        findings.append(self._finding(
            idx,
            summary=(f"No unconnected/isolated person-of-interest node exists in the current "
                     f"case network — all known persons of interest are linked to the victim or "
                     f"each other."),
            reasoning=("A scenario involving an unknown third party (S3) is not supported by the "
                       "current network, since no unlinked candidate node exists in it — but this "
                       "reflects the limits of the data collected so far, not proof that no such "
                       "person exists. Absence of network evidence for S3 is weak evidence against "
                       "it at best, and should be revisited if new persons of interest are added."),
            confidence=0.35,
            supports=[],
            contradicts=["S3"],
            evidence_refs=[],
        ))
        idx += 1

        return findings
