"""
kg/graph_tools.py — permission-aware graph retrieval functions.

A GraphToolkit is bound to ONE person at construction time. Every query
filters through that identity server-side; the model never supplies (and
can never override) who is asking. That is the security story of the POC:
permissions live in the retrieval layer, not in the prompt.
"""

from kg.config import get_driver

# A person can read a document directly or through team membership.
_ACCESS_PREDICATE = """
    EXISTS { MATCH (:Person {id: $person_id})-[:CAN_READ]->(d) }
    OR EXISTS { MATCH (:Person {id: $person_id})-[:MEMBER_OF]->(:Team)-[:CAN_READ]->(d) }
"""


class PersonNotFound(Exception):
    pass


class GraphToolkit:
    def __init__(self, driver, person_name: str):
        self.driver = driver
        rec = self._run(
            """
            MATCH (p:Person)-[:MEMBER_OF]->(t:Team)
            WHERE toLower(p.name) = toLower($name)
            RETURN p.id AS id, p.name AS name, p.role AS role, p.email AS email,
                   t.id AS team_id, t.name AS team_name
            """,
            name=person_name,
        )
        if not rec:
            raise PersonNotFound(f"No person named {person_name!r} in the graph.")
        self.person = rec[0]

    def _run(self, cypher: str, **params) -> list[dict]:
        with self.driver.session() as session:
            return [dict(r) for r in session.run(cypher, **params)]

    def _doc_access_fields(self) -> str:
        """Common RETURN fragment: doc metadata + accessibility + owner contact."""
        return f"""
            d.id AS id, d.title AS title, d.type AS type,
            d.classification AS classification,
            owner.name AS owner_team,
            ({_ACCESS_PREDICATE}) AS accessible,
            head.name AS owner_contact
        """

    # ── Tools ─────────────────────────────────────────────────────────────

    def whoami(self) -> dict:
        team_id = self.person["team_id"]
        processes = self._run(
            """
            MATCH (:Team {id: $team_id})-[:OWNS]->(p:Process)
            RETURN p.name AS name, p.sla_hours AS sla_hours
            ORDER BY p.name
            """,
            team_id=team_id,
        )
        handoffs = self._run(
            """
            MATCH (t:Team {id: $team_id})
            OPTIONAL MATCH (t)-[out:HANDOFF_TO]->(to:Team)
            OPTIONAL MATCH (from:Team)-[inc:HANDOFF_TO]->(t)
            RETURN collect(DISTINCT {direction: 'outgoing', to_team: to.name,
                                     process: out.process, trigger: out.trigger}) +
                   collect(DISTINCT {direction: 'incoming', from_team: from.name,
                                     process: inc.process, trigger: inc.trigger}) AS handoffs
            """,
            team_id=team_id,
        )[0]["handoffs"]
        return {
            "person": self.person["name"],
            "role": self.person["role"],
            "team": self.person["team_name"],
            "team_owns_processes": processes,
            "team_handoffs": [h for h in handoffs if h.get("process")],
        }

    def search_documents(self, query: str) -> dict:
        """Keyword match over all documents. Inaccessible docs are listed
        (title/metadata only) with the person to contact for access."""
        terms = [t for t in query.lower().split() if len(t) > 2]
        if not terms:
            return {"results": [], "note": "Query too short."}
        rows = self._run(
            f"""
            MATCH (owner:Team)-[:OWNS]->(d:Document)
            WHERE any(term IN $terms WHERE
                  toLower(d.title) CONTAINS term OR toLower(d.content) CONTAINS term)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(owner)
            WHERE head.role STARTS WITH 'Head'
            RETURN {self._doc_access_fields()},
                   size([term IN $terms WHERE toLower(d.title) CONTAINS term
                         OR toLower(d.content) CONTAINS term]) AS hits
            ORDER BY hits DESC, d.title
            """,
            terms=terms, person_id=self.person["id"],
        )
        results = []
        for r in rows:
            entry = {k: r[k] for k in
                     ("id", "title", "type", "classification", "owner_team", "accessible")}
            if not r["accessible"]:
                entry["note"] = (
                    f"You do not have access. Contact {r['owner_contact']} "
                    f"({r['owner_team']} team) to request it."
                )
            results.append(entry)
        return {"results": results}

    def read_document(self, doc_id: str) -> dict:
        """Full content — only if this person is permitted to read it."""
        rows = self._run(
            f"""
            MATCH (owner:Team)-[:OWNS]->(d:Document)
            WHERE d.id = $doc_id OR toLower(d.title) = toLower($doc_id)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(owner)
            WHERE head.role STARTS WITH 'Head'
            RETURN {self._doc_access_fields()}, d.content AS content
            """,
            doc_id=doc_id, person_id=self.person["id"],
        )
        if not rows:
            return {"error": f"No document with id or title {doc_id!r}."}
        r = rows[0]
        if not r["accessible"]:
            return {
                "id": r["id"], "title": r["title"],
                "access": "DENIED",
                "reason": f"Classification is {r['classification']} and you have no read grant.",
                "contact": f"{r['owner_contact']} ({r['owner_team']} team)",
            }
        return {k: r[k] for k in ("id", "title", "type", "classification",
                                  "owner_team", "content")}

    def explore_process(self, process_name: str) -> dict:
        """Everything the graph knows about a process: owner, systems,
        regulations, referencing documents, and cross-team handoffs."""
        rows = self._run(
            f"""
            MATCH (t:Team)-[:OWNS]->(p:Process)
            WHERE toLower(p.name) CONTAINS toLower($name)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(t)
            WHERE head.role STARTS WITH 'Head'
            OPTIONAL MATCH (p)-[:RUNS_ON]->(s:System)
            OPTIONAL MATCH (p)-[:GOVERNED_BY]->(reg:Regulation)
            OPTIONAL MATCH (from:Team)-[h:HANDOFF_TO]->(to:Team)
            WHERE h.process = p.name
            RETURN p.name AS process, p.sla_hours AS sla_hours,
                   p.regulatory_flag AS regulatory,
                   t.name AS owning_team, head.name AS team_head,
                   collect(DISTINCT s.name) AS systems,
                   collect(DISTINCT reg.name) AS regulations,
                   collect(DISTINCT {{from: from.name, to: to.name,
                                      trigger: h.trigger}}) AS handoffs
            """,
            name=process_name,
        )
        if not rows:
            return {"error": f"No process matching {process_name!r}."}
        result = rows[0]
        result["handoffs"] = [h for h in result["handoffs"] if h.get("from")]
        docs = self._run(
            f"""
            MATCH (d:Document)-[:REFERENCES]->(p:Process)
            WHERE toLower(p.name) CONTAINS toLower($name)
            MATCH (owner:Team)-[:OWNS]->(d)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(owner)
            WHERE head.role STARTS WITH 'Head'
            RETURN {self._doc_access_fields()}
            ORDER BY d.title
            """,
            name=process_name, person_id=self.person["id"],
        )
        result["documents"] = [
            {k: d[k] for k in ("id", "title", "classification", "owner_team", "accessible")}
            for d in docs
        ]
        return result

    def documents_owned_by_team(self, team_name: str) -> dict:
        """Documents a team OWNS (ownership, not keyword mention)."""
        rows = self._run(
            f"""
            MATCH (owner:Team)-[:OWNS]->(d:Document)
            WHERE toLower(owner.name) CONTAINS toLower($team)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(owner)
            WHERE head.role STARTS WITH 'Head'
            RETURN {self._doc_access_fields()}
            ORDER BY d.title
            """,
            team=team_name, person_id=self.person["id"],
        )
        if not rows:
            return {"error": f"No team matching {team_name!r}."}
        return {
            "team": rows[0]["owner_team"],
            "documents": [
                {k: r[k] for k in ("id", "title", "type", "classification", "accessible")}
                for r in rows
            ],
        }

    def regulation_impact(self, regulation_name: str) -> dict:
        """Blast radius of a regulation: governed processes, their owning
        teams, and every document tied to those processes."""
        rows = self._run(
            f"""
            MATCH (p:Process)-[:GOVERNED_BY]->(reg:Regulation)
            WHERE toLower(reg.name) CONTAINS toLower($name)
            MATCH (t:Team)-[:OWNS]->(p)
            OPTIONAL MATCH (d:Document)-[:REFERENCES]->(p)
            OPTIONAL MATCH (owner:Team)-[:OWNS]->(d)
            OPTIONAL MATCH (head:Person)-[:MEMBER_OF]->(owner)
            WHERE head.role STARTS WITH 'Head'
            RETURN reg.name AS regulation, reg.summary AS summary,
                   p.name AS process, t.name AS process_owner,
                   collect(DISTINCT CASE WHEN d IS NULL THEN NULL ELSE {{
                       id: d.id, title: d.title, owner_team: owner.name,
                       accessible: ({_ACCESS_PREDICATE})
                   }} END) AS documents
            ORDER BY p.name
            """,
            name=regulation_name, person_id=self.person["id"],
        )
        if not rows:
            return {"error": f"No regulation matching {regulation_name!r}."}
        return {
            "regulation": rows[0]["regulation"],
            "summary": rows[0]["summary"],
            "impacted_processes": [
                {
                    "process": r["process"],
                    "owned_by": r["process_owner"],
                    "documents": [d for d in r["documents"] if d],
                }
                for r in rows
            ],
        }


def build_toolkit(person_name: str, driver=None) -> GraphToolkit:
    return GraphToolkit(driver or get_driver(), person_name)
