# Banking Knowledge Graph — MVP POC

Graph-based enterprise context layer. Sales + Operations teams.
Proves relationship-based retrieval across team ownership, permissions, and process handoffs.

---

## Prerequisites

- [Neo4j Desktop](https://neo4j.com/download/) — free, runs locally
- Python 3.10+
- VS Code with extensions listed below

---

## VS Code Extensions (install these first)

| Extension | Publisher | Why |
|---|---|---|
| Neo4j for VS Code | Neo4j | Cypher syntax highlighting + run queries directly |
| Python | Microsoft | Core Python support |
| Pylance | Microsoft | Type checking and autocomplete |
| Python Debugger | Microsoft | Step through scripts |
| DotENV | mikestead | .env file highlighting |

---

## Neo4j Desktop Setup

1. Download and install Neo4j Desktop from https://neo4j.com/download/
2. Open Neo4j Desktop → New Project → Add → Local DBMS
3. Name it `banking-kg-mvp`, set a password (remember it)
4. Click **Start** — wait for the green dot
5. Leave default ports: Bolt `7687`, HTTP `7474`

---

## Python Setup

```bash
# Clone / open this folder in VS Code, then in the terminal:

python -m venv .venv

# Mac / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## Configure credentials

```bash
cp .env.example .env
# Edit .env and set NEO4J_PASSWORD to whatever you chose in Neo4j Desktop
```

---

## Run in order

```bash
python 01_setup_schema.py     # Creates constraints and indexes
python 02_seed_data.py        # Loads teams, people, systems, processes, documents
python 03_proof_queries.py    # Runs the 3 MVP proof queries + prints results
```

---

## What success looks like

`03_proof_queries.py` prints a results table for each of the 3 proof queries.
These are questions that pure keyword or vector search cannot answer correctly
because they require traversing ownership, permission, and handoff relationships.

Run the same natural-language questions through any document search tool
against the same document titles — compare the results. That delta is the POC.

---

## Project structure

```
banking-kg-mvp/
├── .env.example          # Credential template
├── .env                  # Your local credentials (gitignored)
├── README.md
├── requirements.txt
├── connect.py            # Shared Neo4j driver helper
├── 01_setup_schema.py    # Constraints + indexes
├── 02_seed_data.py       # Sample banking graph data
└── 03_proof_queries.py   # 3 proof queries with formatted output
```
