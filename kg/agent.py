"""
kg/agent.py — Claude agent over the permission-scoped graph toolkit.

The agent gets six tools, all pre-bound to one person's identity. It cannot
query as anyone else: the toolkit closures carry the person_id server-side.
"""

import json
from dataclasses import dataclass, field

import anthropic
from anthropic import beta_tool

from kg.graph_tools import GraphToolkit

MODEL = "claude-opus-4-8"

SYSTEM_TEMPLATE = """\
You are the enterprise context assistant of a commercial bank, answering on
behalf of {name} ({role}, {team} team).

Rules:
- Answer ONLY from the graph tools. Never invent documents, people, or processes.
- Cite documents by title when you rely on them.
- Access control is enforced by the tools. If a document is inaccessible,
  say so plainly, name it (title only), and tell the user exactly who to
  contact for access — never speculate about restricted content.
- Prefer structural answers (ownership, handoffs, governance) over keyword
  matching: use explore_process, documents_owned_by_team, and
  regulation_impact when the question is about responsibility or impact.
- Be concise: short paragraphs or tight bullet lists.
"""


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[dict] = field(default_factory=list)


class GraphAgent:
    def __init__(self, toolkit: GraphToolkit, client: anthropic.Anthropic | None = None):
        self.toolkit = toolkit
        self.client = client or anthropic.Anthropic()
        self.system = SYSTEM_TEMPLATE.format(
            name=toolkit.person["name"],
            role=toolkit.person["role"],
            team=toolkit.person["team_name"],
        )
        self.tools = self._build_tools()
        self.messages: list[dict] = []  # multi-turn history for the chat REPL

    def _build_tools(self):
        tk = self.toolkit

        @beta_tool
        def whoami() -> str:
            """Get the current user's identity: name, role, team, the processes their team owns, and the team's handoffs to/from other teams."""
            return json.dumps(tk.whoami(), default=str)

        @beta_tool
        def search_documents(query: str) -> str:
            """Keyword-search all documents by title and content. Returns every match with its owner team and whether the current user may read it; inaccessible documents include who to contact for access.

            Args:
                query: Search keywords, e.g. "KYC screening".
            """
            return json.dumps(tk.search_documents(query), default=str)

        @beta_tool
        def read_document(doc_id: str) -> str:
            """Read a document's full content. Access is enforced: returns the content only if the current user is permitted, otherwise an access-denied result with the contact person.

            Args:
                doc_id: Document id (e.g. "doc-014") or exact title.
            """
            return json.dumps(tk.read_document(doc_id), default=str)

        @beta_tool
        def explore_process(process_name: str) -> str:
            """Look up a business process: owning team and its head, systems it runs on, governing regulations, cross-team handoffs, and every document that references it (with access flags).

            Args:
                process_name: Process name or fragment, e.g. "settlement".
            """
            return json.dumps(tk.explore_process(process_name), default=str)

        @beta_tool
        def documents_owned_by_team(team_name: str) -> str:
            """List the documents a team OWNS (organisational ownership — not keyword mentions).

            Args:
                team_name: Team name or fragment, e.g. "Operations".
            """
            return json.dumps(tk.documents_owned_by_team(team_name), default=str)

        @beta_tool
        def regulation_impact(regulation_name: str) -> str:
            """Trace a regulation's blast radius: which processes it governs, which teams own them, and every document tied to those processes.

            Args:
                regulation_name: Regulation name or fragment, e.g. "AML".
            """
            return json.dumps(tk.regulation_impact(regulation_name), default=str)

        return [whoami, search_documents, read_document, explore_process,
                documents_owned_by_team, regulation_impact]

    def ask(self, question: str, on_tool=None, remember: bool = False) -> AgentResult:
        """Run one question through the agentic loop.

        on_tool: optional callback (tool_name, tool_input) fired per tool call.
        remember: keep the exchange in self.messages for multi-turn chat.
        """
        messages = self.messages + [{"role": "user", "content": question}]
        runner = self.client.beta.messages.tool_runner(
            model=MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=self.system,
            tools=self.tools,
            messages=messages,
        )

        tool_calls: list[dict] = []
        last_message = None
        for message in runner:
            last_message = message
            for block in message.content:
                if block.type == "tool_use":
                    call = {"tool": block.name, "input": block.input}
                    tool_calls.append(call)
                    if on_tool:
                        on_tool(block.name, block.input)

        answer = ""
        if last_message:
            answer = "\n".join(
                b.text for b in last_message.content if b.type == "text"
            ).strip()

        if remember:
            self.messages.append({"role": "user", "content": question})
            self.messages.append({"role": "assistant", "content": answer or "(no answer)"})

        return AgentResult(answer=answer, tool_calls=tool_calls)
