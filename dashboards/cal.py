#!/usr/bin/env python3
# A dashboard for displaying calendar events and daily notes over the range of the given items.
# This ingests data from both the calendar and daily notes scripts.

from copy import deepcopy
import json
import sys
from datetime import datetime, timedelta
from rich import print as rich_print
from rich.console import group
from rich.text import Text
from rich.markdown import Markdown
from rich.padding import Padding
from .utils import LeftJustifiedHeading

def split_timestamp(start, end):
    """
    Splits the given timestamp object into an array with one for each day the timestamp applies
    to. This allows easily handling timestamps which stretch over multiple days. Each of these
    timestamps will have `start` and `end` *time* fields, along with a `date`.
    """

    start_date = datetime.strptime(start["date"], "%Y-%m-%d")
    end_date = datetime.strptime(end["date"], "%Y-%m-%d") if end else start_date

    # For every day between the start and end, create a timestamp
    timestamps = []
    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i) # Starts at 0; with no difference this is `start_date`

        ts = {
            "date": date,
            "start": None,
            "end": None
        }
        if date == start_date and start["time"]:
            ts["start"] = start["time"]
        if date == end_date and end and end["time"]:
            ts["end"] = end["time"]

        timestamps.append(ts)

    return timestamps

@group()
def display_calendar(cal_items, daily_notes):
    """
    Displays the given calendar items and daily notes in a rich text format.
    """

    # First, combine the calendar items and daily notes for each day present in the data
    dates = {}
    for item in cal_items:
        for ts in split_timestamp(item["start"], item["end"]):
            date = ts["date"]
            if date not in dates:
                dates[date] = { "calendar": [], "daily_notes": [] }

            # Make a clone for this date and set the timestamps to be actual times
            item_clone = deepcopy(item)
            item_clone["start"] = ts["start"]
            item_clone["end"] = ts["end"]
            dates[date]["calendar"].append(item_clone)

    for note in daily_notes:
        date = datetime.strptime(note["date"], "%Y-%m-%d")
        if date not in dates:
            dates[date] = { "calendar": [], "daily_notes": [] }

        dates[date]["daily_notes"].append(note)

    dates = dict(sorted(dates.items()))
    for i, date in enumerate(dates):
        yield Text.from_markup(f"[bold underline]{date.strftime('%A, %B %d')}[/bold underline]")

        if dates[date]["daily_notes"]:
            yield Text.from_markup("[bold italic]Daily Notes:[/bold italic]")
        for j, note in enumerate(dates[date]["daily_notes"]):
            yield Text.from_markup(f"  → {note['title']}")

            # Only pad the very last daily note on the very last date when there are no calendar items after
            should_pad = i != len(dates) - 1 or j != len(dates[date]["daily_notes"]) - 1 or len(dates[date]["calendar"]) != 0
            if note["body"]:
                Markdown.elements["heading"] = LeftJustifiedHeading
                # We can't pad in the string, so pad the whole thing
                yield Padding(Markdown(note["body"], justify="left"), (1 if not note["body"].startswith("- ") and not note["body"].startswith("1. ") else 0, 0, 1 if should_pad else 0, 4))
            elif should_pad:
                # If there is a body, the padding spaces us from the next task, if not, do that
                # manually
                yield Text("")


        for j, item in enumerate(dates[date]["calendar"]):
            if item["start"] and item["end"]:
                time_str = f"from {item['start'].removesuffix(':00')} to {item['end'].removesuffix(':00')}"
            elif item["start"]:
                time_str = f"from {item['start'].removesuffix(':00')}"
            elif item["end"]:
                time_str = f"until {item['end'].removesuffix(':00')}"
            else:
                time_str = "all day"

            yield Text.from_markup(f"→ {item['title']} [bold yellow]{time_str}[/bold yellow]")

            if item["location"]:
                yield Text.from_markup(f"  Location: [bold dodger_blue1]{item['location']}[/bold dodger_blue1]", style="italic")

            if item["people"]:
                yield Text.from_markup("  People needed:", style="italic")
                for person_name, _ in item["people"]:
                    yield Text.from_markup(f"    - [bold]{person_name}[/bold]", style="italic")

            # Only pad the very last calendar item in the very last date
            should_pad = i != len(dates) - 1 or j != len(dates[date]["calendar"]) - 1
            if item["body"]:
                Markdown.elements["heading"] = LeftJustifiedHeading
                # We can't pad in the string, so pad the whole thing
                yield Padding(Markdown(item["body"], justify="left"), (1 if not item["body"].startswith("- ") and not item["body"].startswith("1. ") else 0, 0, 1 if should_pad else 0, 2))
            elif should_pad:
                # If there is a body, the padding spaces us from the next task, if not, do that
                # manually
                yield Text("")


def main_cli(_):
    data = json.loads(sys.stdin.read())
    cal_items = data["calendar"]
    daily_notes = data["daily_notes"]

    cal_display = display_calendar(cal_items, daily_notes)
    rich_print(cal_display)

