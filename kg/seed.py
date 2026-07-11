"""
kg/seed.py — idempotent graph loader.
Uses MERGE throughout, so re-running never duplicates data.
reset_graph() wipes everything first for a clean rebuild.
"""

from kg.data import DOCUMENTS, HANDOFFS, PEOPLE, PROCESSES, REGULATIONS, SYSTEMS, TEAMS


def reset_graph(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("  ✓  Graph wiped")


def load_teams(session):
    for t in TEAMS:
        session.run(
            "MERGE (t:Team {id: $id}) SET t.name = $name, t.department = $department",
            **t,
        )
    print(f"  ✓  Teams: {len(TEAMS)}")


def load_people(session):
    for p in PEOPLE:
        session.run(
            """
            MERGE (p:Person {id: $id})
            SET p.name = $name, p.email = $email, p.role = $role
            WITH p
            MATCH (t:Team {id: $team_id})
            MERGE (p)-[:MEMBER_OF]->(t)
            """,
            **p,
        )
    print(f"  ✓  People: {len(PEOPLE)}")


def load_systems(session):
    for s in SYSTEMS:
        session.run(
            """
            MERGE (sys:System {id: $id})
            SET sys.name = $name, sys.vendor = $vendor,
                sys.tier = $tier, sys.criticality = $criticality
            """,
            id=s["id"], name=s["name"], vendor=s["vendor"],
            tier=s["tier"], criticality=s["criticality"],
        )
        for team_id in s["team_ids"]:
            session.run(
                """
                MATCH (t:Team {id: $team_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (t)-[:USES]->(sys)
                """,
                team_id=team_id, sys_id=s["id"],
            )
    print(f"  ✓  Systems: {len(SYSTEMS)}")


def load_processes(session):
    for p in PROCESSES:
        session.run(
            """
            MERGE (pr:Process {id: $id})
            SET pr.name = $name, pr.sla_hours = $sla_hours,
                pr.regulatory_flag = $regulatory_flag
            WITH pr
            MATCH (t:Team {id: $team_id})
            MERGE (t)-[:OWNS]->(pr)
            """,
            id=p["id"], name=p["name"], sla_hours=p["sla_hours"],
            regulatory_flag=p["regulatory_flag"], team_id=p["team_id"],
        )
        for sys_id in p.get("system_ids", []):
            session.run(
                """
                MATCH (pr:Process {id: $proc_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (pr)-[:RUNS_ON]->(sys)
                """,
                proc_id=p["id"], sys_id=sys_id,
            )
    print(f"  ✓  Processes: {len(PROCESSES)}")


def load_regulations(session):
    for r in REGULATIONS:
        session.run(
            """
            MERGE (reg:Regulation {id: $id})
            SET reg.name = $name, reg.jurisdiction = $jurisdiction,
                reg.summary = $summary
            """,
            id=r["id"], name=r["name"], jurisdiction=r["jurisdiction"],
            summary=r["summary"],
        )
        for proc_id in r["process_ids"]:
            session.run(
                """
                MATCH (pr:Process {id: $proc_id})
                MATCH (reg:Regulation {id: $reg_id})
                MERGE (pr)-[:GOVERNED_BY]->(reg)
                """,
                proc_id=proc_id, reg_id=r["id"],
            )
    print(f"  ✓  Regulations: {len(REGULATIONS)}")


def load_documents(session):
    for d in DOCUMENTS:
        session.run(
            """
            MERGE (doc:Document {id: $id})
            SET doc.title = $title, doc.type = $type,
                doc.classification = $classification, doc.content = $content
            WITH doc
            MATCH (t:Team {id: $team_id})
            MERGE (t)-[:OWNS]->(doc)
            """,
            id=d["id"], title=d["title"], type=d["type"],
            classification=d["classification"], content=d["content"],
            team_id=d["team_id"],
        )
        for proc_id in d.get("process_ids", []):
            session.run(
                """
                MATCH (doc:Document {id: $doc_id})
                MATCH (pr:Process {id: $proc_id})
                MERGE (doc)-[:REFERENCES]->(pr)
                """,
                doc_id=d["id"], proc_id=proc_id,
            )
        for sys_id in d.get("system_ids", []):
            session.run(
                """
                MATCH (doc:Document {id: $doc_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (doc)-[:REFERENCES]->(sys)
                """,
                doc_id=d["id"], sys_id=sys_id,
            )
        for team_id in d.get("can_read_teams", []):
            session.run(
                """
                MATCH (t:Team {id: $team_id})
                MATCH (doc:Document {id: $doc_id})
                MERGE (t)-[:CAN_READ]->(doc)
                """,
                team_id=team_id, doc_id=d["id"],
            )
        for person_id in d.get("can_read_people", []):
            session.run(
                """
                MATCH (p:Person {id: $person_id})
                MATCH (doc:Document {id: $doc_id})
                MERGE (p)-[:CAN_READ]->(doc)
                """,
                person_id=person_id, doc_id=d["id"],
            )
    print(f"  ✓  Documents: {len(DOCUMENTS)}")


def load_handoffs(session):
    for h in HANDOFFS:
        session.run(
            """
            MATCH (from:Team {id: $from_id})
            MATCH (to:Team   {id: $to_id})
            MERGE (from)-[r:HANDOFF_TO]->(to)
            SET r.process = $process, r.trigger = $trigger
            """,
            from_id=h["from_team_id"], to_id=h["to_team_id"],
            process=h["process"], trigger=h["trigger"],
        )
    print(f"  ✓  Handoffs: {len(HANDOFFS)}")


def load_all(session):
    load_teams(session)
    load_people(session)
    load_systems(session)
    load_processes(session)
    load_regulations(session)
    load_documents(session)
    load_handoffs(session)


def print_summary(session):
    counts = session.run("""
        RETURN
          count { MATCH (n:Team)       RETURN n } AS teams,
          count { MATCH (n:Person)     RETURN n } AS people,
          count { MATCH (n:System)     RETURN n } AS systems,
          count { MATCH (n:Process)    RETURN n } AS processes,
          count { MATCH (n:Regulation) RETURN n } AS regulations,
          count { MATCH (n:Document)   RETURN n } AS documents,
          count { MATCH ()-[r]->()     RETURN r } AS relationships
    """).single()
    print(f"""
  Graph totals
  ─────────────────────
  Teams         {counts['teams']}
  People        {counts['people']}
  Systems       {counts['systems']}
  Processes     {counts['processes']}
  Regulations   {counts['regulations']}
  Documents     {counts['documents']}
  Relationships {counts['relationships']}""")
