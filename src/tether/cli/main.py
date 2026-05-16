"""
Tether CLI — Version 0.1 (Scaffolding)

Typer + Rich interface. Grounding commands work immediately (no LLM required).
Chat mode is currently a stub that prints the disclaimer and prompt version.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from tether.core.prompt import PROMPT_VERSION, get_system_prompt
from tether.grounding.exercises import run_grounding, grounding_menu
from tether.crisis.resources import print_crisis_message
from tether.redteam.harness import TetherSimulator

app = typer.Typer(
    name="tether",
    help="A local-first reality tethering tool. Not therapy. Not a friend. Software with a job.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


def _print_disclaimer() -> None:
    """Always show this on interactive commands."""
    disclaimer = (
        "[bold red]IMPORTANT:[/bold red] You are talking to a language model, not a person.\n"
        "Tether will not validate delusions or play along with unreality.\n"
        "If you are in crisis, close this and contact a human being immediately (988 in the US)."
    )
    console.print(Panel(disclaimer, border_style="red", title="Tether v" + PROMPT_VERSION))


@app.callback()
def main_callback() -> None:
    """Global callback — runs before every command."""
    pass


@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Provider to use (ollama, litellm, openai_compatible)"),
    debug: bool = typer.Option(False, "--debug", help="Show the system prompt on startup"),
) -> None:
    """
    Start a fresh, stateless conversation with Tether.

    Each new `tether chat` is a completely new session. No memory.
    Use --model to connect to a configured LLM provider (run `tether auth setup` first).
    """
    _print_disclaimer()

    rprint("\n[bold cyan]Tether[/bold cyan] — Jarvis mode, prompt v" + PROMPT_VERSION)
    rprint("Type [bold]exit[/bold] or [bold]quit[/bold] to leave. Type [bold]/ground[/bold] for options.\n")

    if debug:
        rprint("[dim]--- SYSTEM PROMPT (for auditing) ---[/dim]")
        rprint(get_system_prompt()[:800] + "...\n")

    # Initialize simulator — with or without real model
    use_model = model is not None
    if use_model:
        from tether.auth import ProviderKind, ProviderRegistry

        config_path = Path.home() / ".tether" / "config.toml"
        ready = config_path.exists()
        if ready:
            reg = ProviderRegistry.init_default(config_path)
            # Override provider if user specified one
            if model and model != reg.config.kind.value:
                try:
                    reg.config.kind = ProviderKind(model)
                except ValueError:
                    rprint(f"[yellow]Unknown provider '{model}'. Using configured default.[/yellow]")
            rprint(f"[green]✓[/green] Using real model: [bold]{reg.config.active_model_name()}[/bold] via {reg.config.kind.value}")
        else:
            rprint("[yellow]No auth config found. Run 'tether auth setup' first. Falling back to rules.[/yellow]")
            use_model = False

    simulator = TetherSimulator(use_model=use_model)

    if not use_model:
        rprint("[yellow]Rule-based mode (no LLM). Run [bold]tether auth setup[/bold] to connect a real model.[/yellow]")
    rprint("Grounding commands are live. Try:  [bold]/ground 54321[/bold] or [bold]/here[/bold]\n")

    chat_history: List[dict] = []

    # Very basic REPL stub for now
    while True:
        try:
            user_input = console.input("[bold]You > [/bold]").strip()
        except (EOFError, KeyboardInterrupt):
            rprint("\n[cyan]Session ended. Stay tethered.[/cyan]")
            sys.exit(0)

        if user_input.lower() in {"exit", "quit", "q"}:
            rprint("[cyan]Session ended. Stay tethered to the physical world.[/cyan]")
            break

        if user_input.lower().startswith("/ground"):
            parts = user_input.split()
            if len(parts) > 1:
                run_grounding(parts[1])
            else:
                grounding_menu()
            continue

        if user_input.lower() in {"/here", "here"}:
            from tether.grounding.exercises import grounding_here
            grounding_here()
            continue

        if user_input.lower() in {"/help", "help", "?"}:
            rprint("Available: /ground [54321|breath|here|body], /here, exit")
            continue

        # Get response from simulator
        chat_history.append({"role": "user", "content": user_input})
        response = simulator.respond(chat_history)
        chat_history.append({"role": "assistant", "content": response})

        rprint(f"[bold cyan]Tether >[/bold cyan] {response}\n")


@app.command()
def ground(
    technique: str = typer.Argument(
        "menu",
        help="Technique: 54321, breathe, here, body, or 'menu' to list",
    )
) -> None:
    """Run a grounding exercise immediately. Works offline. No LLM required."""
    if technique.lower() in {"menu", "list", "help"}:
        grounding_menu()
    else:
        run_grounding(technique)


@app.command()
def here() -> None:
    """Quick orientation exercise (feet on the floor + facts)."""
    from tether.grounding.exercises import grounding_here
    grounding_here()


@app.command()
def crisis() -> None:
    """Show the crisis redirection message (for testing / transparency)."""
    print_crisis_message()


@app.command()
def version() -> None:
    """Show the current prompt version and build info."""
    rprint(f"Tether prompt version: [bold]{PROMPT_VERSION}[/bold]")
    rprint("This is pre-alpha scaffolding. Grounding commands are functional.")


@app.command()
def web() -> None:
    """Launch the local Tether web app (Gradio) — may have dependency issues on Python 3.9."""
    from tether.web.app import launch
    rprint("[bold cyan]Starting Tether Web App...[/bold cyan]")
    launch()


@app.command()
def open() -> None:
    """Open the simple local HTML version of Tether (recommended right now)."""
    import webbrowser
    html_path = Path(__file__).parent.parent.parent.parent / "tether.html"
    if html_path.exists():
        webbrowser.open(f"file://{html_path.absolute()}")
        rprint("[green]Opened tether.html in your default browser.[/green]")
    else:
        rprint("[red]tether.html not found next to the project.[/red]")


# ── Auth CLI ────────────────────────────────────────────────────────────────

auth_app = typer.Typer(
    name="auth",
    help="Configure LLM provider authentication and test connections.",
    add_completion=False,
)


@auth_app.command()
def setup(
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p",
        help="Provider to configure (ollama, litellm, openai_compatible)",
    ),
) -> None:
    """Interactive setup for LLM provider connection."""
    from tether.auth import ProviderConfig, ProviderKind, ProviderRegistry

    config_path = Path.home() / ".tether" / "config.toml"
    reg = ProviderRegistry.init_default(config_path)

    if not provider:
        # Show available providers and prompt
        rprint("[bold cyan]Tether Provider Setup[/bold cyan]")
        rprint("Choose which LLM backend to use:\n")
        providers = reg.list_supported()
        for i, p in enumerate(providers, 1):
            needs_key = " (needs API key)" if p["needs_api_key"] else " (no key needed)"
            rprint(f"  [bold]{i}.[/bold] {p['name']}{needs_key}")
            rprint(f"     {p['description']}")
        rprint()

        choice = typer.prompt("Enter number", default="1")
        selected = providers[0]
        try:
            idx = int(choice) - 1
            selected = providers[idx]
            provider_str = selected["id"]
        except (ValueError, IndexError):
            rprint("[red]Invalid choice. Using Ollama.[/red]")
            provider_str = "ollama"

        # Confirm
        rprint(f"\nSelected: [bold]{selected['name']}[/bold]")
        if not typer.confirm("Proceed?", default=True):
            rprint("[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit()
    else:
        provider_str = provider

    cfg = reg.config
    kind = ProviderKind(provider_str)
    cfg.kind = kind

    if kind == ProviderKind.OLLAMA:
        cfg.ollama.base_url = typer.prompt(
            "Ollama server URL",
            default=cfg.ollama.base_url,
        )
        cfg.ollama.model = typer.prompt(
            "Default model",
            default=cfg.ollama.model,
        )
        rprint("\n[green]✓[/green] Ollama configured. No API key needed (runs locally).")

    elif kind == ProviderKind.LITELLM:
        cfg.litellm.model = typer.prompt(
            "Model name (e.g. gpt-4o, claude-sonnet-4)",
            default=cfg.litellm.model,
        )
        custom = typer.prompt(
            "Custom LLM provider (optional: openai, anthropic, groq, etc.)",
            default="",
        )
        cfg.litellm.custom_llm_provider = custom if custom.strip() else None

        from tether.auth.credentials import CredentialStore

        store = CredentialStore()
        api_key = typer.prompt(
            "API Key (stored in OS keyring or ~/.tether/credentials.toml)",
            hide_input=True,
        )
        store.set(provider_str, "api_key", api_key)
        rprint("\n[green]✓[/green] LiteLLM configured. API key stored securely.")

    elif kind == ProviderKind.OPENAI_COMPATIBLE:
        cfg.openai.base_url = typer.prompt(
            "API base URL",
            default=cfg.openai.base_url,
        )
        cfg.openai.model = typer.prompt(
            "Model name",
            default=cfg.openai.model,
        )

        from tether.auth.credentials import CredentialStore

        store = CredentialStore()
        api_key = typer.prompt(
            "API Key (stored in OS keyring or ~/.tether/credentials.toml)",
            hide_input=True,
        )
        store.set(provider_str, "api_key", api_key)
        rprint("\n[green]✓[/green] OpenAI-compatible endpoint configured. API key stored securely.")

    reg.save(config_path)
    rprint(f"\n[green]✓[/green] Configuration saved to [dim]{config_path}[/dim]")

    if typer.confirm("\nTest the connection now?", default=True):
        test_command()


@auth_app.command()
def test() -> None:
    """Test the connection to the configured LLM provider."""
    test_command()


def test_command() -> None:
    """Shared test logic used by both `tether auth test` and `tether auth setup`."""
    from tether.auth import ProviderRegistry, test_connection
    from tether.auth.credentials import CredentialStore

    config_path = Path.home() / ".tether" / "config.toml"
    if not config_path.exists():
        rprint("[red]No configuration found. Run:  tether auth setup[/red]")
        raise typer.Exit(code=1)

    reg = ProviderRegistry.init_default(config_path)
    cfg = reg.config

    rprint(f"[bold cyan]Testing connection to:[/bold cyan] {cfg.kind.value}")
    rprint(f"  Model: {cfg.active_model_name()}")

    # Get API key if needed
    store = CredentialStore()
    api_key = None
    if cfg.kind.value in ("litellm", "openai_compatible"):
        try:
            api_key = store.require(cfg.kind.value, "api_key")
        except KeyError:
            rprint("[yellow]No API key configured for this provider.[/yellow]")
            if not typer.confirm("Continue anyway?", default=False):
                raise typer.Exit()

    rprint("\nConnecting...")
    result = test_connection(cfg, api_key=api_key)

    if result["success"]:
        rprint(f"\n[green]✓ CONNECTION OK[/green]  ({result['latency_ms']}ms)")
        rprint(result["message"])
    else:
        rprint(f"\n[red]✗ CONNECTION FAILED[/red]  ({result['latency_ms']}ms)")
        rprint(result["message"])
        raise typer.Exit(code=1)


@auth_app.command()
def status() -> None:
    """Show the current auth configuration and credential status."""
    from tether.auth import ProviderRegistry
    from tether.auth.credentials import CredentialStore

    config_path = Path.home() / ".tether" / "config.toml"
    if not config_path.exists():
        rprint("[yellow]No configuration found. Run:  tether auth setup[/yellow]")
        raise typer.Exit()

    reg = ProviderRegistry.init_default(config_path)
    cfg = reg.config
    store = CredentialStore()

    provider_name = {
        "ollama": "Ollama",
        "litellm": "LiteLLM",
        "openai_compatible": "OpenAI-Compatible",
    }.get(cfg.kind.value, cfg.kind.value)

    table = Table(title="Tether Auth Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Provider", provider_name)
    table.add_row("Model", cfg.active_model_name())
    base_url = cfg.active_base_url()
    if base_url:
        table.add_row("Base URL", base_url)

    # Check credentials
    if cfg.kind.value in ("litellm", "openai_compatible"):
        creds = store.list_credentials(cfg.kind.value)
        if creds:
            for key, masked in creds.items():
                table.add_row(f"{key}", masked)
        else:
            table.add_row("API Key", "[red]Not configured[/red]")
    else:
        table.add_row("API Key", "[dim]Not needed (local)[/dim]")

    console.print(table)

    # Show config file path
    rprint(f"\nConfig: [dim]{config_path}[/dim]")


# Register auth sub-command
app.add_typer(auth_app)


if __name__ == "__main__":
    app()
