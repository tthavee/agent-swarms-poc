"""
02_seed_data.py
Loads the MVP banking knowledge graph into Neo4j.

Nodes created  : 2 Teams, 8 People, 6 Systems, 6 Processes, 20 Documents
Relationships  : MEMBER_OF, OWNS, USES, REFERENCES, HANDOFF_TO, CAN_READ
"""

from connect import get_driver

# ── 1. TEAMS ──────────────────────────────────────────────────────────────────

TEAMS = [
    {"id": "team-sales", "name": "Sales",      "department": "Commercial Banking"},
    {"id": "team-ops",   "name": "Operations", "department": "Operations & Settlement"},
]

# ── 2. PEOPLE ─────────────────────────────────────────────────────────────────

PEOPLE = [
    # Sales team
    {"id": "p01", "name": "Alexandra Chen",    "email": "a.chen@bank.com",    "role": "Head of Sales",           "team_id": "team-sales"},
    {"id": "p02", "name": "Marcus Webb",       "email": "m.webb@bank.com",    "role": "Relationship Manager",    "team_id": "team-sales"},
    {"id": "p03", "name": "Priya Sharma",      "email": "p.sharma@bank.com",  "role": "Relationship Manager",    "team_id": "team-sales"},
    {"id": "p04", "name": "Daniel Okafor",     "email": "d.okafor@bank.com",  "role": "KYC Analyst",             "team_id": "team-sales"},
    # Operations team
    {"id": "p05", "name": "Sophie Müller",     "email": "s.muller@bank.com",  "role": "Head of Operations",      "team_id": "team-ops"},
    {"id": "p06", "name": "James Thornton",    "email": "j.thornton@bank.com","role": "Settlement Analyst",      "team_id": "team-ops"},
    {"id": "p07", "name": "Aisha Rahman",      "email": "a.rahman@bank.com",  "role": "Trade Operations",        "team_id": "team-ops"},
    {"id": "p08", "name": "Carlos Mendes",     "email": "c.mendes@bank.com",  "role": "Reconciliation Analyst",  "team_id": "team-ops"},
]

# ── 3. SYSTEMS ────────────────────────────────────────────────────────────────

SYSTEMS = [
    {"id": "sys-crm",   "name": "CRM Platform",          "vendor": "Salesforce", "tier": "business",  "criticality": "medium", "team_ids": ["team-sales"]},
    {"id": "sys-kyc",   "name": "KYC Screening Platform", "vendor": "Refinitiv",  "tier": "regulated", "criticality": "high",   "team_ids": ["team-sales"]},
    {"id": "sys-cbs",   "name": "Core Banking System",    "vendor": "Temenos",    "tier": "critical",  "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-oms",   "name": "Order Management System","vendor": "Charles River","tier": "critical", "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-sett",  "name": "Settlement Platform",    "vendor": "DTCC",       "tier": "critical",  "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-recon", "name": "Reconciliation Engine",  "vendor": "SmartStream","tier": "business",  "criticality": "medium", "team_ids": ["team-ops"]},
]

# ── 4. PROCESSES ──────────────────────────────────────────────────────────────

PROCESSES = [
    # Sales owns these
    {"id": "proc-onboard", "name": "Client Onboarding",        "sla_hours": 72,  "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-crm", "sys-kyc"]},
    {"id": "proc-kyc",     "name": "KYC Screening",            "sla_hours": 48,  "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-kyc"]},
    {"id": "proc-suit",    "name": "Product Suitability Check", "sla_hours": 24,  "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-crm"]},
    # Operations owns these
    {"id": "proc-acct",    "name": "Account Setup",            "sla_hours": 24,  "regulatory_flag": False, "team_id": "team-ops",   "system_ids": ["sys-cbs"]},
    {"id": "proc-trade",   "name": "Trade Execution",          "sla_hours": 1,   "regulatory_flag": True,  "team_id": "team-ops",   "system_ids": ["sys-oms", "sys-cbs"]},
    {"id": "proc-settle",  "name": "Trade Settlement",         "sla_hours": 48,  "regulatory_flag": True,  "team_id": "team-ops",   "system_ids": ["sys-sett", "sys-recon"]},
]

# ── 5. DOCUMENTS ──────────────────────────────────────────────────────────────
# classification: internal | confidential | restricted
# can_read_teams: teams with read access; can_read_people: individuals with read access

DOCUMENTS = [
    # ── Sales documents ──
    {
        "id": "doc-001", "title": "Client Onboarding Handbook",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-002", "title": "KYC Due Diligence Checklist",
        "type": "Checklist", "classification": "confidential",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": ["p05"],
    },
    {
        "id": "doc-003", "title": "AML Red Flag Indicators Reference",
        "type": "Policy", "classification": "confidential",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
    },
    {
        "id": "doc-004", "title": "Product Suitability Assessment Guide",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-suit"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
    },
    {
        "id": "doc-005", "title": "MiFID II Product Governance Policy",
        "type": "Policy", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-suit", "proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-006", "title": "CRM User Guide — Onboarding Module",
        "type": "Guide", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "system_ids": ["sys-crm"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
    },
    {
        "id": "doc-007", "title": "Enhanced Due Diligence Procedures — PEP & High Risk",
        "type": "Procedure", "classification": "restricted",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": [], "can_read_people": ["p01", "p04"],
    },
    {
        "id": "doc-008", "title": "Client Onboarding SLA and Escalation Matrix",
        "type": "Policy", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-009", "title": "KYC Screening Platform — Quick Start Guide",
        "type": "Guide", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "system_ids": ["sys-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
    },
    {
        "id": "doc-010", "title": "Onboarding Handoff Checklist — Sales to Operations",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard", "proc-acct"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
    },

    # ── Operations documents ──
    {
        "id": "doc-011", "title": "Account Setup Runbook",
        "type": "Runbook", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-acct"],
        "system_ids": ["sys-cbs"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-012", "title": "Trade Execution Standard Operating Procedure",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-trade"],
        "system_ids": ["sys-oms"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-013", "title": "T+2 Settlement Obligations — Desk Reference",
        "type": "Policy", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-014", "title": "Settlement Fail Management Runbook",
        "type": "Runbook", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": ["p05"],
    },
    {
        "id": "doc-015", "title": "Daily Reconciliation Checklist",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-recon"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-016", "title": "Core Banking System — Operations Guide",
        "type": "Guide", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-acct", "proc-trade"],
        "system_ids": ["sys-cbs"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-017", "title": "Trade Operations Maker-Checker Policy",
        "type": "Policy", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-trade"],
        "can_read_teams": ["team-ops", "team-sales"], "can_read_people": [],
    },
    {
        "id": "doc-018", "title": "Settlement Exception Escalation Procedure",
        "type": "Procedure", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": ["p05", "p06"],
    },
    {
        "id": "doc-019", "title": "DTCC / CLS Connectivity Runbook",
        "type": "Runbook", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
    {
        "id": "doc-020", "title": "End-of-Day Processing Checklist",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle", "proc-trade"],
        "system_ids": ["sys-recon", "sys-cbs"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },
]

# ── 6. HANDOFF ────────────────────────────────────────────────────────────────

HANDOFFS = [
    {
        "from_team_id": "team-sales",
        "to_team_id":   "team-ops",
        "process":      "Client Onboarding",
        "trigger":      "KYC approved and product suitability confirmed",
    },
]


# ── LOAD FUNCTIONS ─────────────────────────────────────────────────────────────

def load_teams(session):
    for t in TEAMS:
        session.run(
            "MERGE (t:Team {id: $id}) SET t.name = $name, t.department = $department",
            **t
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
            id=p["id"], name=p["name"], email=p["email"],
            role=p["role"], team_id=p["team_id"]
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
            tier=s["tier"], criticality=s["criticality"]
        )
        for team_id in s["team_ids"]:
            session.run(
                """
                MATCH (t:Team {id: $team_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (t)-[:USES]->(sys)
                """,
                team_id=team_id, sys_id=s["id"]
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
            regulatory_flag=p["regulatory_flag"], team_id=p["team_id"]
        )
        for sys_id in p.get("system_ids", []):
            session.run(
                """
                MATCH (pr:Process {id: $proc_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (pr)-[:RUNS_ON]->(sys)
                """,
                proc_id=p["id"], sys_id=sys_id
            )
    print(f"  ✓  Processes: {len(PROCESSES)}")


def load_documents(session):
    for d in DOCUMENTS:
        session.run(
            """
            MERGE (doc:Document {id: $id})
            SET doc.title = $title, doc.type = $type,
                doc.classification = $classification
            WITH doc
            MATCH (t:Team {id: $team_id})
            MERGE (t)-[:OWNS]->(doc)
            """,
            id=d["id"], title=d["title"], type=d["type"],
            classification=d["classification"], team_id=d["team_id"]
        )
        # REFERENCES → Processes
        for proc_id in d.get("process_ids", []):
            session.run(
                """
                MATCH (doc:Document {id: $doc_id})
                MATCH (pr:Process {id: $proc_id})
                MERGE (doc)-[:REFERENCES]->(pr)
                """,
                doc_id=d["id"], proc_id=proc_id
            )
        # REFERENCES → Systems
        for sys_id in d.get("system_ids", []):
            session.run(
                """
                MATCH (doc:Document {id: $doc_id})
                MATCH (sys:System {id: $sys_id})
                MERGE (doc)-[:REFERENCES]->(sys)
                """,
                doc_id=d["id"], sys_id=sys_id
            )
        # CAN_READ → Teams
        for team_id in d.get("can_read_teams", []):
            session.run(
                """
                MATCH (t:Team {id: $team_id})
                MATCH (doc:Document {id: $doc_id})
                MERGE (t)-[:CAN_READ]->(doc)
                """,
                team_id=team_id, doc_id=d["id"]
            )
        # CAN_READ → People
        for person_id in d.get("can_read_people", []):
            session.run(
                """
                MATCH (p:Person {id: $person_id})
                MATCH (doc:Document {id: $doc_id})
                MERGE (p)-[:CAN_READ]->(doc)
                """,
                person_id=person_id, doc_id=d["id"]
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
            process=h["process"], trigger=h["trigger"]
        )
    print(f"  ✓  Handoffs: {len(HANDOFFS)}")


def print_summary(session):
    counts = session.run("""
        RETURN
          count { MATCH (n:Team)     RETURN n } AS teams,
          count { MATCH (n:Person)   RETURN n } AS people,
          count { MATCH (n:System)   RETURN n } AS systems,
          count { MATCH (n:Process)  RETURN n } AS processes,
          count { MATCH (n:Document) RETURN n } AS documents,
          count { MATCH ()-[r]->()   RETURN r } AS relationships
    """).single()
    print(f"""
  Graph totals
  ─────────────────────
  Teams         {counts['teams']}
  People        {counts['people']}
  Systems       {counts['systems']}
  Processes     {counts['processes']}
  Documents     {counts['documents']}
  Relationships {counts['relationships']}
    """)


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n── Banking KG MVP: Loading seed data ──\n")
    driver = get_driver()
    try:
        with driver.session() as session:
            load_teams(session)
            load_people(session)
            load_systems(session)
            load_processes(session)
            load_documents(session)
            load_handoffs(session)
            print_summary(session)
        print("Seed data loaded. Run 03_proof_queries.py next.\n")
    finally:
        driver.close()
