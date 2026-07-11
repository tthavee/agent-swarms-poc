"""
sync_to_aura.py
Merges all data from local Neo4j Desktop into Neo4j Aura.
Safe to run repeatedly — uses MERGE throughout, so no duplicates are created.

Usage:
    python sync_to_aura.py
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

from kg.schema import SCHEMA_STATEMENTS

load_dotenv()

NODE_LABELS = ["Team", "Person", "System", "Process", "Regulation", "Document"]


def _local_driver():
    uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pw   = os.getenv("NEO4J_PASSWORD")
    if not pw:
        raise EnvironmentError("NEO4J_PASSWORD not set in .env")
    return GraphDatabase.driver(uri, auth=(user, pw))


def _aura_driver():
    uri  = os.getenv("NEO4J_AURA_URI")
    user = os.getenv("NEO4J_AURA_USERNAME")
    pw   = os.getenv("NEO4J_AURA_PASSWORD")
    if not all([uri, user, pw]):
        raise EnvironmentError("NEO4J_AURA_URI / USERNAME / PASSWORD not set in .env")
    # macOS TLS on port 7687 fails cert verification against the Aura cert chain;
    # swap to +ssc (TLS on, cert verification off) so the Bolt handshake succeeds.
    uri = uri.replace("neo4j+s://", "neo4j+ssc://").replace("bolt+s://", "bolt+ssc://")
    return GraphDatabase.driver(uri, auth=(user, pw))


def _aura_db():
    return os.getenv("NEO4J_AURA_DATABASE")


def _graph_counts(session):
    return dict(session.run("""
        RETURN
          count { MATCH (n:Team)     RETURN n } AS teams,
          count { MATCH (n:Person)   RETURN n } AS people,
          count { MATCH (n:System)   RETURN n } AS systems,
          count { MATCH (n:Process)  RETURN n } AS processes,
          count { MATCH (n:Regulation) RETURN n } AS regulations,
          count { MATCH (n:Document) RETURN n } AS documents,
          count { MATCH ()-[r]->()   RETURN r } AS relationships
    """).single())


def _print_counts(header, counts):
    print(f"""
  {header}
  {'─' * 28}
  Teams         {counts['teams']}
  People        {counts['people']}
  Systems       {counts['systems']}
  Processes     {counts['processes']}
  Regulations   {counts['regulations']}
  Documents     {counts['documents']}
  Relationships {counts['relationships']}""")


def setup_schema(aura_session):
    print("\n[1/3] Setting up schema on Aura ...")
    for stmt in SCHEMA_STATEMENTS:
        aura_session.run(stmt)
    print("  ✓  Schema ready")


def sync_nodes(local_session, aura_session):
    print("\n[2/3] Syncing nodes ...")
    total = 0
    for label in NODE_LABELS:
        records = local_session.run(f"MATCH (n:{label}) RETURN n").data()
        for rec in records:
            props = dict(rec["n"])
            node_id = props.get("id")
            if node_id is None:
                continue
            aura_session.run(
                f"MERGE (n:{label} {{id: $id}}) SET n = $props",
                id=node_id,
                props=props,
            )
        print(f"  ✓  {label}: {len(records)}")
        total += len(records)
    print(f"  Nodes synced: {total}")


def sync_relationships(local_session, aura_session):
    print("\n[3/3] Syncing relationships ...")
    records = local_session.run("""
        MATCH (a)-[r]->(b)
        WHERE a.id IS NOT NULL AND b.id IS NOT NULL
        RETURN
          labels(a)[0]  AS src_label,
          a.id           AS src_id,
          type(r)        AS rel_type,
          properties(r)  AS rel_props,
          labels(b)[0]  AS dst_label,
          b.id           AS dst_id
    """).data()

    counts: dict[str, int] = {}
    for rec in records:
        rel_type = rec["rel_type"]
        aura_session.run(
            f"""
            MATCH (a:{rec['src_label']} {{id: $src_id}})
            MATCH (b:{rec['dst_label']} {{id: $dst_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += $props
            """,
            src_id=rec["src_id"],
            dst_id=rec["dst_id"],
            props=rec["rel_props"],
        )
        counts[rel_type] = counts.get(rel_type, 0) + 1

    for rel_type, n in sorted(counts.items()):
        print(f"  ✓  {rel_type}: {n}")
    print(f"  Relationships synced: {sum(counts.values())}")


def main():
    print("\n── Neo4j Sync: Local → Aura ──")

    local = _local_driver()
    aura  = _aura_driver()
    db    = _aura_db()

    try:
        # Show before state
        with local.session() as s:
            _print_counts("Local (source)", _graph_counts(s))
        with aura.session(database=db) as s:
            _print_counts("Aura before sync", _graph_counts(s))

        # Schema
        with aura.session(database=db) as s:
            setup_schema(s)

        # Nodes + relationships (single read session, single write session)
        with local.session() as src, aura.session(database=db) as dst:
            sync_nodes(src, dst)
            sync_relationships(src, dst)

        # Show after state
        with aura.session(database=db) as s:
            _print_counts("Aura after sync", _graph_counts(s))

        print("\n✓  Sync complete.\n")

    finally:
        local.close()
        aura.close()


if __name__ == "__main__":
    main()
