"""Typer CLI entry point for agentlock."""

import typer
from rich.console import Console

app = typer.Typer(
    name="agentlock",
    help="Zero model drift between AI agents. Universal session continuity protocol and CLI for Claude, GPT, Gemini, and any LLM.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(
    project: str = typer.Option(None, "--project", "-p", help="Project slug"),
    project_type: str = typer.Option(None, "--type", "-t", help="Project type override"),
    bridge: str = typer.Option(None, "--bridge", help="Bridge repo (e.g. user/workbench)"),
) -> None:
    """Initialize agentlock state files in the current project."""
    from agentlock.init import init_project

    init_project(project=project, project_type=project_type, bridge=bridge)


@app.command()
def sync(
    bridge: str = typer.Option(None, "--bridge", help="Bridge repo override"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without pushing"),
) -> None:
    """Sync state files to the bridge repo."""
    from agentlock.sync import sync_project

    sync_project(bridge=bridge, dry_run=dry_run)


@app.command()
def status(
    bridge: str = typer.Option(None, "--bridge", help="Bridge repo"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show status of all projects in the bridge repo."""
    from agentlock.status import show_status

    show_status(bridge=bridge, json_output=json_output)


@app.command()
def bootstrap(
    project: str = typer.Option(..., "--project", "-p", help="Project slug"),
    bridge: str = typer.Option(None, "--bridge", help="Bridge repo override"),
    clipboard: bool = typer.Option(False, "--clipboard", help="Copy to clipboard"),
) -> None:
    """Generate a paste-ready bootstrap prompt for any AI."""
    from agentlock.bootstrap import generate_bootstrap

    generate_bootstrap(project=project, bridge=bridge, clipboard=clipboard)


if __name__ == "__main__":
    app()
