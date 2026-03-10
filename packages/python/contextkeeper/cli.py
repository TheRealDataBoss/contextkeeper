"""CLI entry point for contextkeeper — thin wrapper over ContextKeeperClient."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from contextkeeper.client import ContextKeeperClient
from contextkeeper.exceptions import ContextKeeperError

app = typer.Typer(
    name="contextkeeper",
    help="Zero model drift between AI agents.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


def _get_client() -> ContextKeeperClient:
    return ContextKeeperClient(project_dir=Path("."))


def _handle_error(exc: Exception) -> None:
    err_console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(code=1)


@app.command()
def init(
    name: str = typer.Option(..., "--name", "-n", help="Project name"),
    coordination: str = typer.Option(
        "sequential",
        "--coordination",
        "-c",
        help="Coordination mode: sequential, lock, or merge",
    ),
    backend: str = typer.Option(
        "file",
        "--backend",
        "-b",
        help="Backend: file or sqlite",
    ),
) -> None:
    """Initialize a new contextkeeper project in the current directory."""
    try:
        client = _get_client()
        config = client.init(name=name, coordination=coordination, backend_type=backend)
        console.print(Panel(
            f"[green]Initialized project[/green] [bold]{config.name}[/bold]\n"
            f"  ID:           {config.project_id}\n"
            f"  Backend:      {config.backend}\n"
            f"  Coordination: {config.coordination}\n"
            f"  Schema:       {config.schema_version}",
            title="contextkeeper init",
            border_style="green",
        ))
    except ContextKeeperError as exc:
        _handle_error(exc)


def _parse_task(raw: str) -> dict:
    """Parse a task string in format 'TASK-XXXX:title' or 'TASK-XXXX:title:status'."""
    parts = raw.split(":", 2)
    if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
        err_console.print(
            f"[red]Error:[/red] Malformed --task: '{raw}'\n"
            "  Expected format: TASK-XXXX:title or TASK-XXXX:title:status"
        )
        raise typer.Exit(code=1)
    result: dict = {"id": parts[0].strip(), "title": parts[1].strip()}
    if len(parts) == 3 and parts[2].strip():
        result["status"] = parts[2].strip()
    return result


@app.command()
def sync(
    notes: str = typer.Option("", "--notes", help="Free-form notes for this handoff"),
    agent: str = typer.Option("custom", "--agent", help="Agent type: claude, gpt, gemini, custom"),
    agent_version: str = typer.Option("", "--agent-version", help="Agent version string"),
    next_step: Optional[list[str]] = typer.Option(None, "--next-step", help="Add a next step (repeatable)"),
    question: Optional[list[str]] = typer.Option(None, "--question", help="Add an open question (repeatable)"),
    task: Optional[list[str]] = typer.Option(None, "--task", help="Add a task as TASK-XXXX:title[:status] (repeatable)"),
) -> None:
    """Sync current state — creates a versioned handoff."""
    try:
        tasks_parsed = [_parse_task(t) for t in (task or [])]
        client = _get_client()
        handoff = client.sync(
            notes=notes,
            agent=agent,
            agent_version=agent_version,
            next_steps=next_step or None,
            open_questions=question or None,
            tasks=tasks_parsed or None,
        )
        console.print(Panel(
            f"[green]Handoff synced[/green]\n"
            f"  Session: {handoff.session_id}\n"
            f"  Version: {handoff.version}\n"
            f"  Agent:   {handoff.agent.value}\n"
            f"  Tasks:   {len(handoff.tasks)}\n"
            f"  Steps:   {len(handoff.next_steps)}\n"
            f"  Q's:     {len(handoff.open_questions)}",
            title="contextkeeper sync",
            border_style="green",
        ))
    except ContextKeeperError as exc:
        _handle_error(exc)


@app.command()
def bootstrap() -> None:
    """Generate a bootstrap briefing from the latest handoff."""
    try:
        client = _get_client()
        output = client.bootstrap()
        console.print(output)
    except ContextKeeperError as exc:
        _handle_error(exc)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON instead of rich table"),
) -> None:
    """Show project status summary."""
    try:
        client = _get_client()
        result = client.status()

        if json_output:
            console.print(json.dumps(result, indent=2))
            return

        table = Table(title="contextkeeper status", border_style="cyan")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Project", f"{result['name']} ({result['project_id']})")
        table.add_row("Backend", result["backend"])
        table.add_row("Coordination", result["coordination"])
        table.add_row("Sessions", str(result["session_count"]))
        table.add_row("Latest Handoff", result["latest_handoff"])

        if result["task_counts"]:
            counts = ", ".join(
                f"{k}: {v}" for k, v in result["task_counts"].items()
            )
            table.add_row("Tasks", counts)

        console.print(table)
    except ContextKeeperError as exc:
        _handle_error(exc)


@app.command()
def doctor() -> None:
    """Run health checks on the contextkeeper project."""
    try:
        client = _get_client()
        result = client.doctor()

        status_icons = {
            "ok": "[green]OK[/green]",
            "fail": "[red]FAIL[/red]",
            "warn": "[yellow]WARN[/yellow]",
            "info": "[cyan]INFO[/cyan]",
        }

        table = Table(title="contextkeeper doctor", border_style="cyan")
        table.add_column("Check", style="bold")
        table.add_column("Status")
        table.add_column("Detail")

        for check in result["checks"]:
            icon = status_icons.get(check["status"], "?")
            table.add_row(check["name"], icon, check["message"])

        console.print(table)

        if result["healthy"]:
            console.print("\n[green bold]All checks passed.[/green bold]")
        else:
            console.print("\n[red bold]Some checks failed.[/red bold]")
            raise typer.Exit(code=1)
    except ContextKeeperError as exc:
        _handle_error(exc)


@app.command()
def migrate(
    to: str = typer.Option(..., "--to", help="Target backend: file or sqlite"),
) -> None:
    """Migrate data from current backend to a different backend."""
    try:
        client = _get_client()
        result = client.switch_backend(to)
        console.print(Panel(
            f"[green]Migration complete[/green]\n"
            f"  From:     {result['from']}\n"
            f"  To:       {result['to']}\n"
            f"  Sessions: {result['sessions']}\n"
            f"  Handoffs: {result['handoffs']}",
            title="contextkeeper migrate",
            border_style="green",
        ))
    except ContextKeeperError as exc:
        _handle_error(exc)


if __name__ == "__main__":
    app()
