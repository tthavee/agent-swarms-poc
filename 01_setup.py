"""
01_setup.py — create schema and load seed data in one shot.

    python 01_setup.py            # idempotent MERGE load
    python 01_setup.py --reset    # wipe the graph first (recommended after data changes)
"""

import sys

from kg.config import get_driver
from kg.schema import setup_schema
from kg.seed import load_all, print_summary, reset_graph

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    print("\n── Banking KG: setup ──\n")
    driver = get_driver()
    try:
        with driver.session() as session:
            if reset:
                reset_graph(session)
        setup_schema(driver)
        with driver.session() as session:
            load_all(session)
            print_summary(session)
        print("\nGraph ready. Run 02_compare.py for the demo.\n")
    finally:
        driver.close()
