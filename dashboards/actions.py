#!/usr/bin/env python3
# Allows displaying next actions in a rich text format.

from datetime import datetime
from rich.console import group
from rich.markdown import Markdown, TextElement
from rich.padding import Padding
from rich.text import Text
from rich import print as rich_print
from ..utils import load_json

class LeftJustifiedHeading(TextElement):
    """
    A markdown heading, with styling designed for being embedded, rather than sticking out in the
    centre of the terminal.
    """

    @classmethod
    def create(cls, markdown, node) -> "LeftJustifiedHeading":
        heading = cls(node.level)
        return heading

    def on_enter(self, context):
        self.text = Text()
        context.enter_style(self.style_name)

    def __init__(self, level: int):
        self.level = level
        super().__init__()

    def __rich_console__(
        self, console, options
    ):
        text = self.text
        text.justify = "left"
        yield Text(f"{'#' * self.level} {text}")

def format_date(date_str, time_str, current_date, connective="on"):
    """
    Formats the given date for human readability, relative to the given date, applying the
    given connective when it needs to give a specific weekday (e.g. on Wednesday, for Thursday).
    This connective should be chosen based on whatever comes before.
    """

    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    days_difference = (date - current_date).days
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if days_difference == 0:
        day_str = "today"
    elif days_difference == 1:
        day_str = "tomorrow"
    elif days_difference == -1:
        day_str = "yesterday"
    elif 2 <= days_difference < 7:
        day_str = f"{connective} {weekdays[date.weekday()]}"
    elif -7 < days_difference < 0:
        day_str = f"last {weekdays[date.weekday()]}"
    elif 0 < days_difference < 14:
        day_str = f"next {weekdays[date.weekday()]}"
    else:
        day_str = f"{connective} {weekdays[date.weekday()]} {date.strftime('%d/%m/%Y')}"

    if time_str:
        day_str += f" at {time_str}"

    return day_str

def format_minutes(minutes):
    """
    Formats the given number of minutes into a string of the form `Xhr Ym` as sensible.
    """

    hours = minutes // 60
    remaining_minutes = minutes % 60
    result = []

    if hours > 0:
        result.append(f"{hours}hr")
    if remaining_minutes > 0:
        result.append(f"{remaining_minutes}m")

    return " ".join(result) if result else "0m"

@group()
def display_actions(actions, current_date):
    """
    Returns a Rich display of the given actions, with timestamps formatted relative to the given
    date.
    """

    for idx, action in enumerate(actions):
        yield Text(f"→ {action['title']}", style="bold")
        if action["timestamp"]:
            yield Text.from_markup("  [italic]Has a timestamp attached.[/italic]")
        if action["scheduled"]:
            scheduled = format_date(action["scheduled"]["date"], action["scheduled"]["time"], current_date, connective="for")
            yield Text.from_markup(f"  Scheduled [bold dark_orange3]{scheduled}[/bold dark_orange3]", style="italic")
        if action["deadline"]:
            deadline = format_date(action["deadline"]["date"], action["deadline"]["time"], current_date, connective="on")
            yield Text.from_markup(f"  Due [bold red]{deadline}[/bold red]", style="italic")

        # Only add these metadata for non-projects
        if action["time"]:
            focus_str = [ "minimal", "low", "medium", "high" ][action["focus"]]
            time_str = format_minutes(action["time"])
            context_str = ", ".join(action["context"]) if action["context"] else "none"

            yield Text.from_markup(f"  Context: [bold dodger_blue1]{context_str}[/bold dodger_blue1]", style="italic")
            yield Text.from_markup(f"  Focus: [bold green3]{focus_str}[/bold green3]", style="italic")
            yield Text.from_markup(f"  Time: [bold blue]{time_str}[/bold blue]", style="italic")

        if action["people"]:
            yield Text.from_markup("  People needed:", style="italic")
            for person_name, _ in action["people"]:
                yield Text.from_markup(f"    - [bold]{person_name}[/bold]", style="italic")

        should_pad = idx != len(actions) - 1
        if action["body"]:
            Markdown.elements["heading"] = LeftJustifiedHeading
            # We can't pad in the string, so pad the whole thing
            yield Padding(Markdown(action["body"], justify="left"), (0, 0, 1 if should_pad else 0, 2))
        elif should_pad:
            # If there is a body, the padding spaces us from the next task, if not, do that
            # manually
            yield Text("")

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Display next actions.", prog="actions")
    parser.add_argument("-d", "--date", type=str, required=False, help="The current date for relative date formatting.")

    args = parser.parse_args(args)
    current_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now().date()

    actions = load_json()
    actions_display = display_actions(actions, current_date)
    rich_print(actions_display)
