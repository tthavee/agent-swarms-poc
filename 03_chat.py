"""
03_chat.py — interactive REPL over the graph agent, as a chosen identity.

    python 03_chat.py --as "Marcus Webb"
    python 03_chat.py                      # lists people, prompts for one

Ask anything: "what does my team own?", "who do I hand off to?",
"can I read the settlement fail runbook?", "what changes if MiFID II changes?"
"""

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from kg.agent import GraphAgent
from kg.config import get_driver
from kg.data import PEOPLE
from kg.graph_tools import GraphToolkit, PersonNotFound

console = Console()


def pick_person() -> str:
    console.print("[bold]Who is asking?[/]")
    for p in PEOPLE:
        console.print(f"  • {p['name']}  [dim]({p['role']}, {p['team_id'].removeprefix('team-')})[/]")
    return console.input("\n[bold cyan]name>[/] ").strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--as", dest="person", help='Identity to ask as, e.g. "Marcus Webb"')
    args = parser.parse_args()

    person = args.person or pick_person()
    driver = get_driver()
    try:
        try:
            toolkit = GraphToolkit(driver, person)
        except PersonNotFound as e:
            console.print(f"[red]{e}[/]")
            raise SystemExit(1)

        agent = GraphAgent(toolkit)
        console.print(Panel.fit(
            f"Chatting as [bold]{toolkit.person['name']}[/] "
            f"({toolkit.person['role']}, {toolkit.person['team_name']} team)\n"
            "[dim]Permissions are enforced in the tools — the agent only sees what "
            "this person may see. Ctrl-C or 'exit' to quit.[/]",
            border_style="cyan",
        ))

        while True:
            try:
                question = console.input("\n[bold cyan]you>[/] ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not question or question.lower() in {"exit", "quit"}:
                break
            with console.status("[green]thinking…[/]"):
                result = agent.ask(
                    question,
                    on_tool=lambda name, inp: console.log(f"[dim]tool: {name}({inp})[/]"),
                    remember=True,
                )
            console.print(Markdown(result.answer or "(no answer)"))
    finally:
        driver.close()
    console.print("\n[dim]bye[/]")
