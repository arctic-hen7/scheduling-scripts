# Allows displaying tickles in a rich format.

from datetime import datetime
from rich.console import group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
from rich import print as rich_print
from .utils import LeftJustifiedHeading, format_date
from ..utils import load_json

@group()
def display_tickles(tickles, current_date):
    """
    Returns a Rich display of the given tickles, with timestamps formatted relative to the given
    date.
    """

    for idx, tickle in enumerate(tickles):
        yield Text(f"→ {tickle['title']}", style="bold")
        if tickle.get("date"):
            yield Text.from_markup(f"  Appeared [bold dodger_blue1]{format_date(tickle['date'], None, current_date, connective='on')}[/bold dodger_blue1]", style="italic")

        should_pad = idx != len(tickles) - 1
        if tickle["body"]:
            Markdown.elements["heading"] = LeftJustifiedHeading
            # We can't pad in the string, so pad the whole thing
            yield Padding(Markdown(tickle["body"], justify="left"), (1 if not tickle["body"].startswith("- ") and not tickle["body"].startswith("1. ") else 0, 0, 1 if should_pad else 0, 2))
        elif should_pad:
            # If there is a body, the padding spaces us from the next task, if not, do that
            # manually
            yield Text("")

    if not tickles:
        yield Text.from_markup("[red italic]No tickles found.[/red italic]")

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Display tickles.", prog="tickles")
    parser.add_argument("-d", "--date", type=str, required=False, help="The current date for relative date formatting.")

    args = parser.parse_args(args)
    current_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now().date()

    tickles = load_json()
    tickles_display = display_tickles(tickles, current_date)
    rich_print(tickles_display)
