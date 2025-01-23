# A composite for displaying important dates.

from datetime import datetime
from rich import print as rich_print
from ..dates import filter_to_dates
from ..dashboards.dates import display_dates
from ..get import get_normalised_action_items

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Return a dashboard of important dates.", prog="dates")
    parser.add_argument("-d", "--date", type=str, help="The current date.")
    parser.add_argument("-u", "--until", type=str, help="The cutoff date to surface dates (same as the current date by default).")

    args = parser.parse_args(args)
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    # Different to upcoming: we don't need anything in advance unless we're told to
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else date
    until.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    dates = filter_to_dates(action_items, until)

    display = display_dates(dates, date.date())
    rich_print(display)
