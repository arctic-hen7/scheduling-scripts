# Allows displaying next actions in a rich text format.

from datetime import datetime
from rich.console import group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
from rich import print as rich_print
from .utils import LeftJustifiedHeading, format_date, format_minutes
from ..utils import load_json

@group()
def display_actions(actions, current_date):
    """
    Returns a Rich display of the given actions, with timestamps formatted relative to the given
    date.
    """

    for idx, action in enumerate(actions):
        yield Text(f"→ {action['title']}", style="bold")
        if action.get("timestamp"):
            yield Text.from_markup("  [italic]Has a timestamp attached.[/italic]")
        if action["scheduled"]:
            scheduled = format_date(action["scheduled"]["date"], action["scheduled"]["time"], current_date, connective="for")
            yield Text.from_markup(f"  Scheduled [bold dark_orange3]{scheduled}[/bold dark_orange3]", style="italic")
        if action["deadline"]:
            deadline = format_date(action["deadline"]["date"], action["deadline"]["time"], current_date, connective="on")
            yield Text.from_markup(f"  Due [bold red]{deadline}[/bold red]", style="italic")

        # Only add these metadata for actual tasks
        if action.get("time"):
            focus_str = [ "minimal", "low", "medium", "high" ][action["focus"]]
            time_str = format_minutes(action["time"])
            context_str = ", ".join(action["context"]) if action["context"] else "none"

            yield Text.from_markup(f"  Context: [bold dodger_blue1]{context_str}[/bold dodger_blue1]", style="italic")
            yield Text.from_markup(f"  Focus: [bold green3]{focus_str}[/bold green3]", style="italic")
            yield Text.from_markup(f"  Time: [bold blue]{time_str}[/bold blue]", style="italic")

        if action.get("sent"):
            yield Text.from_markup(f"  Sent [bold dodger_blue1]{format_date(action['sent'], None, current_date, connective='on')}[/bold dodger_blue1]", style="italic")

        if action["people"]:
            yield Text.from_markup("  People needed:", style="italic")
            for person_name, _ in action["people"]:
                yield Text.from_markup(f"    - [bold]{person_name}[/bold]", style="italic")

        should_pad = idx != len(actions) - 1
        if action["body"]:
            Markdown.elements["heading"] = LeftJustifiedHeading
            # We can't pad in the string, so pad the whole thing
            yield Padding(Markdown(action["body"], justify="left"), (1 if not action["body"].startswith("- ") and not action["body"].startswith("1. ") else 0, 0, 1 if should_pad else 0, 2))
        elif should_pad:
            # If there is a body, the padding spaces us from the next task, if not, do that
            # manually
            yield Text("")

    if not actions:
        yield Text.from_markup("[red italic]No actions found.[/red italic]")

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Display next actions.", prog="actions")
    parser.add_argument("-d", "--date", type=str, required=False, help="The current date for relative date formatting.")

    args = parser.parse_args(args)
    current_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now().date()

    actions = load_json()
    actions_display = display_actions(actions, current_date)
    rich_print(actions_display)
