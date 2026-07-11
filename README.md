# Banking Knowledge Graph — Permission-Aware Graph Agent POC

A Neo4j knowledge graph as the **enterprise context layer for AI agents**.

The claim this POC proves, live: **document search cannot answer questions
about ownership, permissions, handoffs, or regulatory impact — graph
traversal can, and an agent scoped to the asker's identity does it safely.**

Every demo prints two columns over the *same corpus*:

| | BM25 keyword search | Graph agent |
|---|---|---|
| Ownership | docs that *mention* "settlement" | docs *owned by* the team that owns the settlement process |
| Permissions | returns restricted docs to everyone | filtered through `CAN_READ` — Marcus and Sophie get different answers |
| Handoffs | no idea | follows `HANDOFF_TO` edges with triggers |
| Regulation change | docs that literally say "AML" | `Regulation ← GOVERNED_BY ← Process ← REFERENCES ← Document`, across teams |

The agent's identity is bound **server-side** in the tool layer — the model
never passes "who is asking" and cannot be prompt-injected into reading
restricted content. Denied access returns the document title and who to
contact, never the content.

---

## Data model

**Nodes**: `Team` (Sales, Operations, Compliance) · `Person` (10) ·
`System` (6) · `Process` (7) · `Regulation` (AML Directive, MiFID II, CSDR) ·
`Document` (24, each with content + classification)

**Edges**: `MEMBER_OF` · `OWNS` · `USES` · `RUNS_ON` · `REFERENCES` ·
`GOVERNED_BY` · `HANDOFF_TO` (with process + trigger) · `CAN_READ` (team- and
person-level grants)

The document content is deliberately adversarial to keyword search: Sales
docs mention "settlement" in passing (false positives), settlement-process
runbooks never say the word (false negatives), and the best KYC content sits
in restricted docs most people can't read.

## Setup

1. **Neo4j Desktop** running locally (Bolt `7687`), or point `.env` at Aura.
2. ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # set NEO4J_PASSWORD and ANTHROPIC_API_KEY
   ```

## Run

```bash
python 01_setup.py --reset   # schema + seed (idempotent; --reset wipes first)
python 02_compare.py         # THE DEMO: search vs agent, side by side
python 03_chat.py --as "Marcus Webb"   # free-form chat as any identity
```

Try the same question as different people in `03_chat.py`:

```
python 03_chat.py --as "Marcus Webb"     # Sales RM — limited view
python 03_chat.py --as "Sophie Müller"   # Head of Ops — sees ops runbooks
python 03_chat.py --as "Elena Vasquez"   # Head of Compliance
you> what can I read about the KYC process?
```

## Layout

```
kg/
├── config.py        # env + Neo4j driver
├── schema.py        # constraints + indexes
├── data.py          # seed data (docs include content)
├── seed.py          # idempotent loader
├── baseline.py      # BM25 keyword search — the strawman
├── graph_tools.py   # permission-aware retrieval, identity bound server-side
└── agent.py         # Claude agent (tool runner, claude-opus-4-8)
01_setup.py          # schema + seed
02_compare.py        # side-by-side demo
03_chat.py           # identity-scoped REPL
sync_to_aura.py      # mirror local graph → Neo4j Aura
```

## How permissions work

`kg/graph_tools.py` builds a `GraphToolkit` bound to one `Person` at
construction. Every Cypher query embeds:

```cypher
EXISTS { (:Person {id: $person_id})-[:CAN_READ]->(d) }
OR EXISTS { (:Person {id: $person_id})-[:MEMBER_OF]->(:Team)-[:CAN_READ]->(d) }
```

`search_documents` returns inaccessible matches as metadata-only with a
contact ("ask Sophie Müller"); `read_document` refuses outright. The LLM
only ever sees what the person may see.

## Cloud sync

`python sync_to_aura.py` mirrors the local graph into Neo4j Aura
(MERGE-based, safe to re-run). Set the `NEO4J_AURA_*` vars in `.env`.
