"""
connect.py — shared Neo4j driver helper.
All scripts import get_driver() from here.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def get_driver():
    uri      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
    user     = os.getenv("NEO4J_USER",     "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise EnvironmentError(
            "NEO4J_PASSWORD not set. Copy .env.example to .env and add your password."
        )

    return GraphDatabase.driver(uri, auth=(user, password))


def verify():
    """Quick connection smoke-test — run this file directly to check."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j connected ✓' AS msg")
        print(result.single()["msg"])
    driver.close()


if __name__ == "__main__":
    verify()
