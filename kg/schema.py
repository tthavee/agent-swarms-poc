"""
kg/schema.py — uniqueness constraints and lookup indexes.
Safe to re-run — uses IF NOT EXISTS throughout.
"""

SCHEMA_STATEMENTS = [
    # ── Uniqueness constraints ─────────────────────────────────────────────
    "CREATE CONSTRAINT person_id     IF NOT EXISTS FOR (n:Person)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT team_id       IF NOT EXISTS FOR (n:Team)       REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT document_id   IF NOT EXISTS FOR (n:Document)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT process_id    IF NOT EXISTS FOR (n:Process)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT system_id     IF NOT EXISTS FOR (n:System)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT regulation_id IF NOT EXISTS FOR (n:Regulation) REQUIRE n.id IS UNIQUE",

    # ── Lookup indexes ─────────────────────────────────────────────────────
    "CREATE INDEX person_name     IF NOT EXISTS FOR (n:Person)     ON (n.name)",
    "CREATE INDEX team_name       IF NOT EXISTS FOR (n:Team)       ON (n.name)",
    "CREATE INDEX document_type   IF NOT EXISTS FOR (n:Document)   ON (n.type)",
    "CREATE INDEX process_name    IF NOT EXISTS FOR (n:Process)    ON (n.name)",
    "CREATE INDEX system_name     IF NOT EXISTS FOR (n:System)     ON (n.name)",
    "CREATE INDEX system_tier     IF NOT EXISTS FOR (n:System)     ON (n.tier)",
    "CREATE INDEX regulation_name IF NOT EXISTS FOR (n:Regulation) ON (n.name)",
]


def setup_schema(driver):
    with driver.session() as session:
        for stmt in SCHEMA_STATEMENTS:
            session.run(stmt)
    print(f"  ✓  {len(SCHEMA_STATEMENTS)} constraints/indexes ensured")
