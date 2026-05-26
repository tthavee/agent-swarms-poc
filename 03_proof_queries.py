"""
03_proof_queries.py
Runs the 3 MVP proof queries and prints results.

Each query demonstrates something graph retrieval can answer
that keyword or vector search cannot.

After running this, ask the same questions against any document
search tool using only the document titles from this corpus.
The comparison is your POC result.
"""

from tabulate import tabulate
from connect import get_driver

DIVIDER = "\n" + "─" * 70 + "\n"


# ── QUERY 1: Ownership traversal ──────────────────────────────────────────────
#
# "Find documents owned by the team responsible for trade settlement"
#
# Vector search returns documents that MENTION settlement.
# Graph traversal returns documents OWNED BY the team that OWNS the process.
# These are often different documents entirely.

QUERY_1 = """
MATCH (t:Team)-[:OWNS]->(p:Process)
WHERE p.name CONTAINS 'Settlement'
MATCH (t)-[:OWNS]->(d:Document)
RETURN t.name AS owning_team,
       d.title AS document,
       d.type  AS doc_type,
       d.classification AS access_level
ORDER BY d.type, d.title
"""

# ── QUERY 2: Permission-filtered retrieval ────────────────────────────────────
#
# "What can Marcus Webb (Sales) access about the KYC process?"
#
# Vector search has no access model — it returns all KYC documents.
# Graph traversal follows CAN_READ edges then REFERENCES edges,
# returning only documents this specific person is permitted to see.

QUERY_2 = """
MATCH (person:Person {name: 'Marcus Webb'})
MATCH (person)-[:MEMBER_OF]->(team:Team)-[:CAN_READ]->(d:Document)
MATCH (d)-[:REFERENCES]->(p:Process)
WHERE p.name CONTAINS 'KYC'
RETURN person.name  AS person,
       d.title      AS document,
       d.classification AS access_level,
       p.name       AS related_process
ORDER BY d.classification, d.title

UNION

MATCH (person:Person {name: 'Marcus Webb'})-[:CAN_READ]->(d:Document)
MATCH (d)-[:REFERENCES]->(p:Process)
WHERE p.name CONTAINS 'KYC'
RETURN person.name  AS person,
       d.title      AS document,
       d.classification AS access_level,
       p.name       AS related_process
ORDER BY d.classification, d.title
"""

# ── QUERY 3: Cross-team handoff traversal ────────────────────────────────────
#
# "Trace the full handoff from Sales — who takes over and what do they own?"
#
# This is a structural relationship query, not a content question.
# Vector search cannot answer it from document similarity alone.

QUERY_3 = """
MATCH (from:Team)-[h:HANDOFF_TO]->(to:Team)
WHERE from.name = 'Sales'
MATCH (to)-[:OWNS]->(p:Process)
OPTIONAL MATCH (to)-[:OWNS]->(d:Document)
RETURN from.name        AS from_team,
       h.process        AS handoff_for,
       h.trigger        AS trigger_condition,
       to.name          AS to_team,
       collect(DISTINCT p.name) AS processes_owned,
       count(DISTINCT d)        AS documents_owned
"""

# ── BONUS: Graph coverage summary ────────────────────────────────────────────
#
# Shows all nodes and relationship types — useful for the Bloom visualiser.

QUERY_SUMMARY = """
MATCH (t:Team)-[r]->(target)
RETURN t.name AS team, type(r) AS relationship,
       labels(target)[0] AS target_type,
       count(*) AS count
ORDER BY t.name, type(r)
"""


def run_query(session, cypher, dedupe_col=None):
    result = session.run(cypher)
    rows = [dict(r) for r in result]
    if dedupe_col:
        seen = set()
        rows = [r for r in rows if not (r[dedupe_col] in seen or seen.add(r[dedupe_col]))]
    return rows


def print_query_block(num, title, why_graph_wins, rows, headers):
    print(DIVIDER)
    print(f"  QUERY {num}  {title}")
    print(f"\n  Why graph wins: {why_graph_wins}\n")
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        print("  (no results — check seed data loaded correctly)")


if __name__ == "__main__":
    print("\n── Banking KG MVP: Proof queries ──")

    driver = get_driver()
    try:
        with driver.session() as session:

            # ── Query 1
            rows = run_query(session, QUERY_1)
            print_query_block(
                1,
                "Ownership traversal — docs owned by the settlement team",
                "Vector search returns docs that mention 'settlement'.\n"
                "  This query returns docs OWNED BY the team that OWNS the settlement\n"
                "  process. Often different documents entirely.",
                rows,
                {"owning_team": "Team", "document": "Document", "doc_type": "Type", "access_level": "Access"},
            )

            # ── Query 2
            rows = run_query(session, QUERY_2, dedupe_col="document")
            print_query_block(
                2,
                "Permission-filtered retrieval — KYC docs Marcus Webb can see",
                "Vector search has no access model — returns all KYC docs.\n"
                "  This query follows CAN_READ edges first, returning only what\n"
                "  this person is actually permitted to read.",
                rows,
                {"person": "Person", "document": "Document", "access_level": "Access", "related_process": "Process"},
            )

            # ── Query 3
            rows = run_query(session, QUERY_3)
            print_query_block(
                3,
                "Cross-team handoff traversal — who receives from Sales and what do they own?",
                "This is a structural question about process ownership, not content.\n"
                "  Vector search cannot answer it. The HANDOFF_TO edge with its\n"
                "  process and trigger properties is the proof of concept.",
                rows,
                {"from_team": "From", "handoff_for": "Handoff For", "trigger_condition": "Trigger",
                 "to_team": "To Team", "processes_owned": "Processes Owned", "documents_owned": "Docs Owned"},
            )

            # ── Summary
            print(DIVIDER)
            print("  GRAPH COVERAGE SUMMARY\n")
            rows = run_query(session, QUERY_SUMMARY)
            print(tabulate(rows,
                headers={"team": "Team", "relationship": "Relationship", "target_type": "Target Type", "count": "Count"},
                tablefmt="rounded_outline"
            ))

        print(DIVIDER)
        print("  Next steps")
        print("  ──────────")
        print("  1. Open Neo4j Browser at http://localhost:7474")
        print("     Run: MATCH (n) RETURN n   to see the full graph visually")
        print("  2. Install Neo4j Bloom from Desktop for a richer visualisation")
        print("  3. Ask the same 3 questions against your document search tool")
        print("     and compare results — that comparison is your POC output")
        print("  4. When ready for Phase 1: add Client Support + Tech Support teams,")
        print("     Regulation/Control nodes, and automated ingestion connectors\n")

    finally:
        driver.close()
