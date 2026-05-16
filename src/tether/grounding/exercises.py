"""
Grounding Exercises for Tether — Version 0.1

All exercises are written in the Jarvis tone (calm, dry, competent).
These can be triggered via CLI commands or offered naturally by the main loop.
"""

from rich.console import Console
from rich.prompt import Prompt
import time

console = Console()


def _print_jarvis(text: str, style: str = "default") -> None:
    """Print in a calm, steady style."""
    console.print(text, style=style)


def grounding_54321() -> None:
    """
    Classic 5-4-3-2-1 sensory grounding.
    Most effective for dissociation and looping thoughts.
    """
    _print_jarvis("\n[bold]5-4-3-2-1 Grounding[/bold]")
    _print_jarvis("Let's bring your attention to the physical world, sir.\n")

    senses = [
        ("five", "see", "things you can see right now"),
        ("four", "physically feel or touch", "sensations (chair, clothes, temperature, feet on floor)"),
        ("three", "hear", "sounds in your environment"),
        ("two", "smell", "scents around you"),
        ("one", "taste", "taste in your mouth right now"),
    ]

    for number, verb, examples in senses:
        _print_jarvis(f"Name {number} things you can {verb}.")
        _print_jarvis(f"({examples})", style="dim")
        response = Prompt.ask("  >", default="").strip()
        if response:
            _print_jarvis(f"  Noted: {response}", style="dim")
        time.sleep(0.4)

    _print_jarvis("\nHow does your body feel now compared to a minute ago?")
    _print_jarvis("Take one more slow breath. You're here. The room is real.\n")


def grounding_breathe() -> None:
    """
    Physiological sigh — fastest nervous system reset.
    Two inhales + long exhale.
    """
    _print_jarvis("\n[bold]Physiological Sigh (fastest reset)[/bold]")
    _print_jarvis("When the mind is racing, the breath is the quickest way back.\n")

    _print_jarvis("First, take a deep breath in through your nose... fill your lungs.")
    time.sleep(1.2)
    _print_jarvis("Now take one more small sip of air on top of that.")
    time.sleep(0.8)
    _print_jarvis("Then exhale slowly through your mouth, as if you're fogging a mirror. Let everything go.\n")

    _print_jarvis("Again. In... and a little more... and release.")
    time.sleep(2.0)
    _print_jarvis("One more time. Deep breath... sip... long, slow exhale.\n")

    _print_jarvis("Good. Your nervous system just received the signal that you are not, in fact, being chased by a tiger.")
    _print_jarvis("The room is still here. So are you.\n")


def grounding_here() -> None:
    """
    Orientation + feet on the floor. Strong reality anchor.
    """
    _print_jarvis("\n[bold]Orientation — Feet on the Floor[/bold]")
    _print_jarvis("Put both feet flat on the ground. Feel the pressure through your soles.")
    _print_jarvis("Notice the temperature of the floor beneath you.\n")

    _print_jarvis("Now, state these facts — out loud if you can:\n")

    _print_jarvis("My name is _______________________________.")
    name = Prompt.ask("  >", default="").strip() or "[your name]"

    _print_jarvis("Today is _______________________________.")
    date = Prompt.ask("  >", default="").strip() or "[today's date]"

    _print_jarvis("I am in _______________________________.")
    location = Prompt.ask("  >", default="").strip() or "[physical location]"

    _print_jarvis("\nI am a human being with a body that exists in the physical world.")
    _print_jarvis("I am currently speaking with a language model running on a computer.")
    _print_jarvis("Nothing more. Nothing less.\n")

    _print_jarvis(f"Feet. Floor. {name}. {date}. {location}.")
    _print_jarvis("This is the actual room you are in. Everything else is a story your mind is telling you right now.\n")


def grounding_body() -> None:
    """
    Simple body scan + movement suggestion.
    """
    _print_jarvis("\n[bold]Body Scan + Movement[/bold]")
    _print_jarvis("If you're quite detached, the fastest way back is usually through the body.\n")

    _print_jarvis("Clench your fists as hard as you can for five seconds... and release.")
    time.sleep(1.5)
    _print_jarvis("Tense your shoulders up toward your ears... hold... and let them drop.")
    time.sleep(1.5)
    _print_jarvis("Press your feet hard into the floor... and release.\n")

    _print_jarvis("Options that often help when the mind is particularly loud:")
    _print_jarvis("  • Splash cold water on your face and the back of your neck for 20 seconds")
    _print_jarvis("  • Step outside and feel the actual air on your skin")
    _print_jarvis("  • Walk around the room and name every object that has nothing to do with a screen")
    _print_jarvis("  • Hold an ice cube in your hand until it starts to hurt a little\n")

    choice = Prompt.ask("Would you like to do one of those now? (y/n)", default="n")
    if choice.lower().startswith("y"):
        _print_jarvis("Good. Go do it. I'll be here when you get back.")
    else:
        _print_jarvis("Understood. The offer remains open.\n")


def grounding_menu() -> None:
    """Show available grounding techniques."""
    _print_jarvis("\n[bold]Available Grounding Techniques[/bold]")
    _print_jarvis("  54321     — 5-4-3-2-1 sensory (most effective for dissociation)")
    _print_jarvis("  breathe   — Physiological sigh (fastest nervous system reset)")
    _print_jarvis("  here      — Orientation + feet on the floor")
    _print_jarvis("  body      — Body tension + movement suggestions")
    _print_jarvis("\nRun with:  tether ground <name>\n")


# Mapping for CLI
GROUNDING_EXERCISES = {
    "54321": grounding_54321,
    "5-4-3-2-1": grounding_54321,
    "breathe": grounding_breathe,
    "breath": grounding_breathe,
    "here": grounding_here,
    "orientation": grounding_here,
    "body": grounding_body,
    "scan": grounding_body,
}


def run_grounding(name: str) -> None:
    """Run a specific grounding exercise by short name."""
    exercise = GROUNDING_EXERCISES.get(name.lower())
    if exercise:
        exercise()
    else:
        _print_jarvis(f"I don't have a grounding exercise called '{name}'.")
        grounding_menu()
