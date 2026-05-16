"""
Crisis Resources for Tether — Version 0.1

These must be kept accurate and up-to-date.
Any changes should be verified against official sources.
"""

from typing import Dict

# Primary resources — update these with official sources before any release
CRISIS_RESOURCES: Dict[str, str] = {
    "US": "United States: Call or text 988 (Suicide & Crisis Lifeline) — 24/7, free, confidential",
    "IASP": "International: https://www.iasp.info/suicidalthoughts/ — find resources for your country",
    "EMERGENCY": "If you are in immediate physical danger, call your local emergency services now.",
}

CRISIS_TEMPLATE = """
I'm going to stop the normal conversation now.

I am a language model. I cannot keep you safe or help you through what you're describing.
You need to speak with a human being immediately.

{us}
{iasp}
{emergency}

I will not continue this conversation. Please reach out to a real person now.
""".strip()


def get_crisis_message() -> str:
    """Return the full crisis redirection message."""
    return CRISIS_TEMPLATE.format(
        us=CRISIS_RESOURCES["US"],
        iasp=CRISIS_RESOURCES["IASP"],
        emergency=CRISIS_RESOURCES["EMERGENCY"],
    )


def print_crisis_message() -> None:
    """Print the crisis message with strong visual weight."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    msg = get_crisis_message()
    console.print(Panel(msg, border_style="red", title="[bold red]CRISIS PROTOCOL ACTIVATED[/bold red]"))
