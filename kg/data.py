"""
kg/data.py — seed data for the banking knowledge graph.

Pure data, no I/O. Loaded by kg/seed.py.

The document `content` fields are deliberately crafted so that keyword/BM25
search mis-fires in ways graph traversal does not:

  * Several Sales-owned docs mention "settlement" in passing (false positives
    for "settlement documents"), while several Operations docs that BELONG to
    the Trade Settlement process never use the word (false negatives).
  * KYC content appears in restricted/confidential docs that most people
    cannot read — keyword search has no access model and returns them anyway.
"""

# ── 1. TEAMS ──────────────────────────────────────────────────────────────────

TEAMS = [
    {"id": "team-sales",      "name": "Sales",      "department": "Commercial Banking"},
    {"id": "team-ops",        "name": "Operations", "department": "Operations & Settlement"},
    {"id": "team-compliance", "name": "Compliance", "department": "Risk & Compliance"},
]

# ── 2. PEOPLE ─────────────────────────────────────────────────────────────────

PEOPLE = [
    # Sales team
    {"id": "p01", "name": "Alexandra Chen", "email": "a.chen@bank.com",     "role": "Head of Sales",           "team_id": "team-sales"},
    {"id": "p02", "name": "Marcus Webb",    "email": "m.webb@bank.com",     "role": "Relationship Manager",    "team_id": "team-sales"},
    {"id": "p03", "name": "Priya Sharma",   "email": "p.sharma@bank.com",   "role": "Relationship Manager",    "team_id": "team-sales"},
    {"id": "p04", "name": "Daniel Okafor",  "email": "d.okafor@bank.com",   "role": "KYC Analyst",             "team_id": "team-sales"},
    # Operations team
    {"id": "p05", "name": "Sophie Müller",  "email": "s.muller@bank.com",   "role": "Head of Operations",      "team_id": "team-ops"},
    {"id": "p06", "name": "James Thornton", "email": "j.thornton@bank.com", "role": "Settlement Analyst",      "team_id": "team-ops"},
    {"id": "p07", "name": "Aisha Rahman",   "email": "a.rahman@bank.com",   "role": "Trade Operations",        "team_id": "team-ops"},
    {"id": "p08", "name": "Carlos Mendes",  "email": "c.mendes@bank.com",   "role": "Reconciliation Analyst",  "team_id": "team-ops"},
    # Compliance team
    {"id": "p09", "name": "Elena Vasquez",  "email": "e.vasquez@bank.com",  "role": "Head of Compliance",      "team_id": "team-compliance"},
    {"id": "p10", "name": "Tom Nakamura",   "email": "t.nakamura@bank.com", "role": "AML Compliance Officer",  "team_id": "team-compliance"},
]

# ── 3. SYSTEMS ────────────────────────────────────────────────────────────────

SYSTEMS = [
    {"id": "sys-crm",   "name": "CRM Platform",           "vendor": "Salesforce",    "tier": "business",  "criticality": "medium", "team_ids": ["team-sales"]},
    {"id": "sys-kyc",   "name": "KYC Screening Platform", "vendor": "Refinitiv",     "tier": "regulated", "criticality": "high",   "team_ids": ["team-sales", "team-compliance"]},
    {"id": "sys-cbs",   "name": "Core Banking System",    "vendor": "Temenos",       "tier": "critical",  "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-oms",   "name": "Order Management System","vendor": "Charles River", "tier": "critical",  "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-sett",  "name": "Settlement Platform",    "vendor": "DTCC",          "tier": "critical",  "criticality": "high",   "team_ids": ["team-ops"]},
    {"id": "sys-recon", "name": "Reconciliation Engine",  "vendor": "SmartStream",   "tier": "business",  "criticality": "medium", "team_ids": ["team-ops"]},
]

# ── 4. PROCESSES ──────────────────────────────────────────────────────────────

PROCESSES = [
    # Sales owns these
    {"id": "proc-onboard", "name": "Client Onboarding",         "sla_hours": 72, "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-crm", "sys-kyc"]},
    {"id": "proc-kyc",     "name": "KYC Screening",             "sla_hours": 48, "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-kyc"]},
    {"id": "proc-suit",    "name": "Product Suitability Check", "sla_hours": 24, "regulatory_flag": True,  "team_id": "team-sales", "system_ids": ["sys-crm"]},
    # Operations owns these
    {"id": "proc-acct",    "name": "Account Setup",             "sla_hours": 24, "regulatory_flag": False, "team_id": "team-ops",   "system_ids": ["sys-cbs"]},
    {"id": "proc-trade",   "name": "Trade Execution",           "sla_hours": 1,  "regulatory_flag": True,  "team_id": "team-ops",   "system_ids": ["sys-oms", "sys-cbs"]},
    {"id": "proc-settle",  "name": "Trade Settlement",          "sla_hours": 48, "regulatory_flag": True,  "team_id": "team-ops",   "system_ids": ["sys-sett", "sys-recon"]},
    # Compliance owns these
    {"id": "proc-monitor", "name": "AML Transaction Monitoring","sla_hours": 24, "regulatory_flag": True,  "team_id": "team-compliance", "system_ids": ["sys-kyc"]},
]

# ── 5. REGULATIONS ────────────────────────────────────────────────────────────
# (Process)-[:GOVERNED_BY]->(Regulation)

REGULATIONS = [
    {
        "id": "reg-aml", "name": "AML Directive",
        "jurisdiction": "EU", "summary": "Anti-money-laundering obligations: customer due diligence, transaction monitoring, and suspicious activity reporting.",
        "process_ids": ["proc-kyc", "proc-onboard", "proc-monitor"],
    },
    {
        "id": "reg-mifid", "name": "MiFID II",
        "jurisdiction": "EU", "summary": "Investor protection and market conduct: product governance, suitability, and best execution.",
        "process_ids": ["proc-suit", "proc-trade"],
    },
    {
        "id": "reg-csdr", "name": "CSDR Settlement Discipline",
        "jurisdiction": "EU", "summary": "Settlement discipline regime: cash penalties for fails and mandatory buy-in provisions.",
        "process_ids": ["proc-settle"],
    },
]

# ── 6. DOCUMENTS ──────────────────────────────────────────────────────────────
# classification: internal | confidential | restricted
# can_read_teams: teams with read access; can_read_people: individuals with read access

DOCUMENTS = [
    # ── Sales documents ──
    {
        "id": "doc-001", "title": "Client Onboarding Handbook",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
        # trap: mentions "settlement" but is NOT a settlement-process doc
        "content": (
            "End-to-end guide for bringing a new client onto the platform: intake, "
            "documentation, and account activation. Includes capturing the client's "
            "standing settlement instructions and expected settlement timelines so "
            "downstream teams are not blocked after go-live."
        ),
    },
    {
        "id": "doc-002", "title": "KYC Due Diligence Checklist",
        "type": "Checklist", "classification": "confidential",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": ["p05"],
        "content": (
            "Mandatory KYC verification steps before onboarding approval: identity "
            "documents, beneficial ownership above 25%, source of funds, and "
            "adverse media screening. Every item requires evidence attached in the "
            "KYC Screening Platform."
        ),
    },
    {
        "id": "doc-003", "title": "AML Red Flag Indicators Reference",
        "type": "Policy", "classification": "confidential",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
        "content": (
            "Reference list of AML red flags relevant to KYC screening: unusual "
            "transaction patterns, reluctance to provide beneficial ownership "
            "information, shell company structures, and high-risk jurisdictions. "
            "Escalate any hit to the KYC Analyst."
        ),
    },
    {
        "id": "doc-004", "title": "Product Suitability Assessment Guide",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-suit"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
        "content": (
            "How to complete the suitability questionnaire: client risk tolerance, "
            "investment horizon, knowledge and experience checks, and target market "
            "matching under MiFID II product governance rules."
        ),
    },
    {
        "id": "doc-005", "title": "MiFID II Product Governance Policy",
        "type": "Policy", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-suit", "proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
        "content": (
            "Bank policy implementing MiFID II product governance: target market "
            "definition, distribution strategy review, and periodic product review "
            "cadence. Applies to all products distributed by the Sales team."
        ),
    },
    {
        "id": "doc-006", "title": "CRM User Guide — Onboarding Module",
        "type": "Guide", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "system_ids": ["sys-crm"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
        "content": (
            "Step-by-step CRM instructions for the onboarding module: creating the "
            "prospect record, attaching intake documents, and triggering the "
            "handoff workflow once approvals are complete."
        ),
    },
    {
        "id": "doc-007", "title": "Enhanced Due Diligence Procedures — PEP & High Risk",
        "type": "Procedure", "classification": "restricted",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "can_read_teams": [], "can_read_people": ["p01", "p04"],
        # trap: top KYC content, but almost nobody can read it
        "content": (
            "Enhanced due diligence for politically exposed persons and high-risk "
            "KYC cases: senior management sign-off, source of wealth corroboration, "
            "enhanced ongoing monitoring frequency, and documentation retention "
            "requirements. Distribution is restricted to named individuals."
        ),
    },
    {
        "id": "doc-008", "title": "Client Onboarding SLA and Escalation Matrix",
        "type": "Policy", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
        "content": (
            "Onboarding service levels: 72-hour end-to-end target, per-stage "
            "checkpoints, and the escalation ladder when a stage breaches. Names "
            "the accountable owner for each stage."
        ),
    },
    {
        "id": "doc-009", "title": "KYC Screening Platform — Quick Start Guide",
        "type": "Guide", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-kyc"],
        "system_ids": ["sys-kyc"],
        "can_read_teams": ["team-sales"], "can_read_people": [],
        "content": (
            "Getting started with the KYC Screening Platform: running a screen, "
            "interpreting match scores, dispositioning false positives, and "
            "exporting the audit trail for the client file."
        ),
    },
    {
        "id": "doc-010", "title": "Onboarding Handoff Checklist — Sales to Operations",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-sales", "process_ids": ["proc-onboard", "proc-acct"],
        "can_read_teams": ["team-sales", "team-ops"], "can_read_people": [],
        # trap: mentions settlement instructions but is a Sales onboarding doc
        "content": (
            "Everything Operations needs before account setup can begin: executed "
            "agreements, verified standing settlement instructions (SSIs), tax "
            "forms, and the completed KYC approval reference. Incomplete handoffs "
            "are returned to the Relationship Manager."
        ),
    },

    # ── Operations documents ──
    {
        "id": "doc-011", "title": "Account Setup Runbook",
        "type": "Runbook", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-acct"],
        "system_ids": ["sys-cbs"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        "content": (
            "Operational steps to open the account in the Core Banking System: "
            "static data entry, account hierarchy, fee schedule assignment, and "
            "four-eyes verification before activation."
        ),
    },
    {
        "id": "doc-012", "title": "Trade Execution Standard Operating Procedure",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-trade"],
        "system_ids": ["sys-oms"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        "content": (
            "Order lifecycle in the Order Management System: order capture, "
            "pre-trade checks, execution, and allocation. Covers best-execution "
            "evidence requirements and the one-hour booking SLA."
        ),
    },
    {
        "id": "doc-013", "title": "T+2 Settlement Obligations — Desk Reference",
        "type": "Policy", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        "content": (
            "Desk reference for T+2 settlement obligations by market: cut-off "
            "times, affirmation deadlines, and CSDR cash penalty exposure for "
            "late matching. Includes the buy-in decision tree."
        ),
    },
    {
        "id": "doc-014", "title": "Settlement Fail Management Runbook",
        "type": "Runbook", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": ["p05"],
        "content": (
            "Playbook for settlement fails: root-cause triage, counterparty "
            "chasing, partial delivery decisions, and CSDR penalty calculation. "
            "Names the counterparties with recurring fail patterns — handle as "
            "confidential."
        ),
    },
    {
        "id": "doc-015", "title": "Daily Reconciliation Checklist",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-recon"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        # trap: belongs to the Trade Settlement process but never says "settlement"
        "content": (
            "Morning checks in the Reconciliation Engine: match ledger entries "
            "against custodian statements, investigate breaks over threshold, and "
            "sign off positions before the market open. Unresolved breaks escalate "
            "to the desk supervisor."
        ),
    },
    {
        "id": "doc-016", "title": "Core Banking System — Operations Guide",
        "type": "Guide", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-acct", "proc-trade"],
        "system_ids": ["sys-cbs"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        "content": (
            "Administration guide for the Core Banking System: user provisioning, "
            "batch schedules, interface monitoring, and the incident severity "
            "matrix for platform outages."
        ),
    },
    {
        "id": "doc-017", "title": "Trade Operations Maker-Checker Policy",
        "type": "Policy", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-trade"],
        "can_read_teams": ["team-ops", "team-sales"], "can_read_people": [],
        "content": (
            "Dual-control policy for trade operations: which actions require a "
            "second approver, segregation-of-duties rules, and the exception "
            "process for out-of-hours amendments."
        ),
    },
    {
        "id": "doc-018", "title": "Settlement Exception Escalation Procedure",
        "type": "Procedure", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": ["p05", "p06"],
        "content": (
            "Escalation path for settlement exceptions that breach the 48-hour "
            "SLA: notification thresholds, client-impact assessment, and when to "
            "engage the Head of Operations directly."
        ),
    },
    {
        "id": "doc-019", "title": "DTCC / CLS Connectivity Runbook",
        "type": "Runbook", "classification": "confidential",
        "team_id": "team-ops", "process_ids": ["proc-settle"],
        "system_ids": ["sys-sett"],
        "can_read_teams": ["team-ops"], "can_read_people": [],
        # trap: settlement-process doc described in clearing/DvP vocabulary
        "content": (
            "Connectivity procedures for the DTCC and CLS gateways: session "
            "restart, message queue drain, and fallback to manual delivery-versus-"
            "payment instruction upload when the primary clearing link is down."
        ),
    },
    {
        "id": "doc-020", "title": "End-of-Day Processing Checklist",
        "type": "Checklist", "classification": "internal",
        "team_id": "team-ops", "process_ids": ["proc-settle", "proc-trade"],
        "system_ids": ["sys-recon", "sys-cbs"],
        # trap: settlement-process doc that never says "settlement"
        "content": (
            "End-of-day sequence: confirm all trades are booked and allocated, "
            "run the ledger roll in the Core Banking System, verify batch "
            "completion in the Reconciliation Engine, and hand over open items to "
            "the follow-the-sun desk."
        ),
        "can_read_teams": ["team-ops"], "can_read_people": [],
    },

    # ── Compliance documents ──
    {
        "id": "doc-021", "title": "AML Transaction Monitoring Standards",
        "type": "Policy", "classification": "restricted",
        "team_id": "team-compliance", "process_ids": ["proc-monitor", "proc-kyc"],
        "system_ids": ["sys-kyc"],
        "can_read_teams": ["team-compliance"], "can_read_people": ["p01"],
        # trap: strong KYC/AML content, restricted to Compliance + Head of Sales
        "content": (
            "Internal standards for AML transaction monitoring: scenario "
            "thresholds, KYC risk-score integration, alert triage timelines, and "
            "suspicious activity report criteria. Contains detection logic — "
            "restricted distribution."
        ),
    },
    {
        "id": "doc-022", "title": "Regulatory Change Management Procedure",
        "type": "Procedure", "classification": "internal",
        "team_id": "team-compliance", "process_ids": ["proc-monitor"],
        "can_read_teams": ["team-sales", "team-ops", "team-compliance"], "can_read_people": [],
        "content": (
            "How regulatory changes are assessed and rolled out: horizon "
            "scanning, impact assessment across affected processes and documents, "
            "and attestation that controls were updated before the effective date."
        ),
    },
    {
        "id": "doc-023", "title": "Sanctions Screening Escalation Playbook",
        "type": "Runbook", "classification": "confidential",
        "team_id": "team-compliance", "process_ids": ["proc-monitor", "proc-kyc"],
        "can_read_teams": ["team-compliance"], "can_read_people": ["p04"],
        "content": (
            "What to do on a potential sanctions match during KYC or ongoing "
            "monitoring: freeze actions, internal notification order, regulator "
            "reporting deadlines, and the do-not-tip-off rule."
        ),
    },
    {
        "id": "doc-024", "title": "MiFID II Compliance Attestation Guide",
        "type": "Guide", "classification": "internal",
        "team_id": "team-compliance", "process_ids": ["proc-suit"],
        "can_read_teams": ["team-sales", "team-compliance"], "can_read_people": [],
        "content": (
            "Annual attestation process for MiFID II obligations: evidence "
            "collection for suitability checks, sampling methodology, and the "
            "sign-off chain from desk head to Head of Compliance."
        ),
    },
]

# ── 7. HANDOFFS ───────────────────────────────────────────────────────────────

HANDOFFS = [
    {
        "from_team_id": "team-sales",
        "to_team_id":   "team-ops",
        "process":      "Client Onboarding",
        "trigger":      "KYC approved and product suitability confirmed",
    },
    {
        "from_team_id": "team-sales",
        "to_team_id":   "team-compliance",
        "process":      "KYC Screening",
        "trigger":      "PEP match, sanctions hit, or high-risk rating",
    },
]
