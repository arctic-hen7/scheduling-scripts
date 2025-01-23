# Allows displaying dates in a rich format.

from datetime import datetime
from rich.console import group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
from rich import print as rich_print
from .utils import LeftJustifiedHeading, format_date
from ..utils import load_json

@group()
def display_dates(dates, current_date):
    """
    Returns a Rich display of the given important dates, with timestamps formatted relative to the
    given date.
    """

    for idx, item in enumerate(dates):
        yield Text(f"→ {item['title']}", style="bold")
        if item.get("date"):
            yield Text.from_markup(f"  Date: [bold dodger_blue1]{format_date(item['date'], None, current_date, connective='on')}[/bold dodger_blue1]", style="italic")

        yield Text.from_markup(f"  Person: [bold]{item['person'][0]}[/bold]", style="italic")

        should_pad = idx != len(dates) - 1
        if item["body"]:
            Markdown.elements["heading"] = LeftJustifiedHeading
            # We can't pad in the string, so pad the whole thing
            yield Padding(Markdown(item["body"], justify="left"), (1 if not item["body"].startswith("- ") and not item["body"].startswith("1. ") else 0, 0, 1 if should_pad else 0, 2))
        elif should_pad:
            # If there is a body, the padding spaces us from the next task, if not, do that
            # manually
            yield Text("")

    if not dates:
        yield Text.from_markup("[red italic]No important dates found.[/red italic]")

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Display important dates.", prog="date")
    parser.add_argument("-d", "--date", type=str, required=False, help="The current date for relative date formatting.")

    args = parser.parse_args(args)
    current_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now().date()

    dates = load_json()
    dates_display = display_dates(dates, current_date)
    rich_print(dates_display)
