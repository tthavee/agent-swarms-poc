"""
01_setup_schema.py
Creates uniqueness constraints and indexes for all 5 MVP node types.
Run once before loading any data.
Safe to re-run — uses IF NOT EXISTS throughout.
"""

from connect import get_driver

SCHEMA_STATEMENTS = [
    # ── Uniqueness constraints ─────────────────────────────────────────────
    "CREATE CONSTRAINT person_id   IF NOT EXISTS FOR (n:Person)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT team_id     IF NOT EXISTS FOR (n:Team)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT process_id  IF NOT EXISTS FOR (n:Process)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT system_id   IF NOT EXISTS FOR (n:System)   REQUIRE n.id IS UNIQUE",

    # ── Lookup indexes ─────────────────────────────────────────────────────
    # Name lookups used heavily in proof queries
    "CREATE INDEX person_name   IF NOT EXISTS FOR (n:Person)   ON (n.name)",
    "CREATE INDEX team_name     IF NOT EXISTS FOR (n:Team)     ON (n.name)",
    "CREATE INDEX document_type IF NOT EXISTS FOR (n:Document) ON (n.type)",
    "CREATE INDEX process_name  IF NOT EXISTS FOR (n:Process)  ON (n.name)",
    "CREATE INDEX system_name   IF NOT EXISTS FOR (n:System)   ON (n.name)",
    "CREATE INDEX system_tier   IF NOT EXISTS FOR (n:System)   ON (n.tier)",
]


def setup_schema(driver):
    with driver.session() as session:
        for stmt in SCHEMA_STATEMENTS:
            session.run(stmt)
            label = stmt.split("FOR")[1].split("REQUIRE")[0].strip() if "FOR" in stmt else stmt
            print(f"  ✓  {label.strip()}")


if __name__ == "__main__":
    print("\n── Banking KG MVP: Schema setup ──\n")
    driver = get_driver()
    try:
        setup_schema(driver)
        print("\nSchema ready. Run 02_seed_data.py next.\n")
    finally:
        driver.close()
