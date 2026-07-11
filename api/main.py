"""
api/main.py — FastAPI skin over the kg/ package.

    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET  /people                 persona list for the identity switcher
    GET  /graph?person=p02       full graph, docs annotated with access for that person
    POST /chat                   SSE stream: text deltas, tool calls, citations
"""

import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from kg.agent import GraphAgent
from kg.config import get_driver
from kg.graph_tools import GraphToolkit, PersonNotFound

driver = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver
    driver = get_driver()
    yield
    driver.close()


app = FastAPI(title="Banking KG API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One agent per (session, persona) so chat history survives across turns
# but never leaks between personas or browser tabs.
_agents: dict[tuple[str, str], GraphAgent] = {}
_agents_lock = threading.Lock()


def _run(cypher: str, **params) -> list[dict]:
    with driver.session() as session:
        return [dict(r) for r in session.run(cypher, **params)]


@app.get("/people")
def people():
    return _run(
        """
        MATCH (p:Person)-[:MEMBER_OF]->(t:Team)
        RETURN p.id AS id, p.name AS name, p.role AS role, t.name AS team
        ORDER BY t.name, p.name
        """
    )


@app.get("/graph")
def graph(person: str):
    nodes = _run(
        """
        MATCH (n) WHERE n.id IS NOT NULL
        RETURN n.id AS id, labels(n)[0] AS label,
               coalesce(n.name, n.title) AS caption,
               n.classification AS classification,
               properties(n) AS props,
               CASE WHEN n:Document THEN
                 EXISTS { MATCH (:Person {id: $person_id})-[:CAN_READ]->(n) }
                 OR EXISTS { MATCH (:Person {id: $person_id})-[:MEMBER_OF]->(:Team)-[:CAN_READ]->(n) }
               ELSE null END AS accessible
        """,
        person_id=person,
    )
    # Popups show doc content via /document (permission-checked) — never here.
    for n in nodes:
        n["props"].pop("content", None)
        n["props"].pop("id", None)
    rels = _run(
        """
        MATCH (a)-[r]->(b)
        WHERE a.id IS NOT NULL AND b.id IS NOT NULL
        RETURN a.id AS source, b.id AS target, type(r) AS type,
               properties(r) AS props,
               a.id + '|' + type(r) + '|' + b.id AS id
        """
    )
    return {"nodes": nodes, "relationships": rels}


@app.get("/document/{doc_id}")
def document(doc_id: str, person: str):
    """Permission-checked document read for the details popup."""
    try:
        toolkit = GraphToolkit(driver, person)
    except PersonNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return toolkit.read_document(doc_id)


class ChatRequest(BaseModel):
    session_id: str
    person_id: str
    message: str


def _get_agent(session_id: str, person_id: str) -> GraphAgent:
    key = (session_id, person_id)
    with _agents_lock:
        if key not in _agents:
            toolkit = GraphToolkit(driver, person_id)
            _agents[key] = GraphAgent(toolkit)
        return _agents[key]


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        agent = _get_agent(req.session_id, req.person_id)
    except PersonNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    def sse():
        try:
            for event in agent.ask_stream(req.message):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:  # surface agent/API failures to the client
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
