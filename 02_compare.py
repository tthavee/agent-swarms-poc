"""
02_compare.py — THE DEMO.

For each proof question, show side by side:
  LEFT  — what plain BM25 keyword search returns (no ownership, no permissions)
  RIGHT — what the permission-scoped graph agent answers

Question 2 runs twice — as Marcus Webb (Sales) and Sophie Müller (Head of
Operations) — to show the same question producing different permitted answers.

Requires: local Neo4j running, seeded via 01_setup.py, ANTHROPIC_API_KEY in .env.
"""

from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from kg.agent import GraphAgent
from kg.baseline import BaselineSearch
from kg.config import get_driver
from kg.data import DOCUMENTS, PEOPLE
from kg.graph_tools import GraphToolkit

console = Console()

CASES = [
    {
        "title": "1 · Ownership traversal",
        "question": "Which documents does the team responsible for trade settlement own?",
        "askers": ["Marcus Webb"],
        "why": "Search returns docs that MENTION settlement (including Sales docs that "
               "say it in passing) and misses settlement-process docs that never use "
               "the word. The graph follows Team-[:OWNS]->Process and Team-[:OWNS]->Document.",
    },
    {
        "title": "2 · Permission-filtered retrieval",
        "question": "What can I read about the KYC process?",
        "askers": ["Marcus Webb", "Sophie Müller"],
        "why": "Search has no access model — it returns restricted EDD and Compliance "
               "docs to everyone. The graph filters through CAN_READ edges, so the "
               "answer depends on who is asking.",
    },
    {
        "title": "3 · Cross-team handoff",
        "question": "Who takes over after Sales completes client onboarding, and what do they need from us?",
        "askers": ["Priya Sharma"],
        "why": "A structural question about the HANDOFF_TO edge and downstream "
               "ownership — content similarity cannot answer it.",
    },
    {
        "title": "4 · Regulation impact",
        "question": "If the AML Directive changes, which processes and documents are impacted?",
        "askers": ["Elena Vasquez"],
        "why": "Impact = Regulation<-[:GOVERNED_BY]-Process<-[:REFERENCES]-Document, "
               "across three teams. Keyword search only finds docs that literally "
               "say 'AML'.",
    },
]

_PEOPLE_BY_NAME = {p["name"]: p for p in PEOPLE}
_DOCS_BY_ID = {d["id"]: d for d in DOCUMENTS}


def can_read(person_name: str, doc_id: str) -> bool:
    person = _PEOPLE_BY_NAME[person_name]
    doc = _DOCS_BY_ID[doc_id]
    return (person["team_id"] in doc["can_read_teams"]
            or person["id"] in doc["can_read_people"])


def baseline_panel(results: list[dict], asker: str) -> Panel:
    body = Text()
    if not results:
        body.append("(no matches)", style="dim")
    for r in results:
        readable = can_read(asker, r["id"])
        lock = "" if readable else "  🔒 no access"
        body.append(f"{r['score']:>5}  ", style="dim")
        body.append(r["title"], style="white" if readable else "red")
        body.append(f"\n       {r['owner_team_id'].removeprefix('team-')} · "
                    f"{r['classification']}{lock}\n", style="dim")
    body.append("\nNo ownership. No permissions. No relationships.", style="italic dim")
    return Panel(body, title="[bold red]BM25 keyword search[/]",
                 subtitle="what a document search tool sees", border_style="red")


def agent_panel(answer: str, tool_calls: list[dict], asker: str) -> Panel:
    tools_line = " → ".join(
        f"{c['tool']}({', '.join(repr(v) for v in c['input'].values())})"
        for c in tool_calls
    )
    body = Markdown(answer or "(no answer)")
    return Panel.fit(
        Columns([body], expand=True),
        title=f"[bold green]Graph agent — asking as {asker}[/]",
        subtitle=f"[dim]{tools_line}[/]" if tools_line else None,
        border_style="green",
    )


def run_case(case: dict, baseline: BaselineSearch, driver):
    console.print(Rule(f"[bold]{case['title']}[/]"))
    console.print(f"[bold cyan]Q:[/] {case['question']}")
    console.print(f"[dim]{case['why']}[/]\n")

    results = baseline.search(case["question"], top_k=5)

    for asker in case["askers"]:
        toolkit = GraphToolkit(driver, asker)
        agent = GraphAgent(toolkit)
        with console.status(f"[green]agent thinking as {asker}…[/]"):
            result = agent.ask(
                case["question"],
                on_tool=lambda name, inp: console.log(f"[dim]tool: {name}({inp})[/]"),
            )
        console.print(Columns(
            [baseline_panel(results, asker), agent_panel(result.answer, result.tool_calls, asker)],
            equal=True, expand=True,
        ))
        console.print()


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold]Banking Knowledge Graph POC[/]\n"
        "Keyword search vs a permission-scoped graph agent — same corpus, same questions.",
        border_style="cyan",
    ))
    baseline = BaselineSearch()
    driver = get_driver()
    try:
        for case in CASES:
            run_case(case, baseline, driver)
    finally:
        driver.close()
    console.print(Rule("[bold]The delta between the two columns is the POC[/]"))
