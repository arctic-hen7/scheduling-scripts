# A composite for displaying next actions, filtered in some way.

from datetime import datetime, timedelta
from rich import print as rich_print
from ..waiting import filter_to_waiting
from ..upcoming import filter_to_upcoming
from ..dashboards.actions import display_actions
from ..get import get_normalised_action_items

# By default, expand everything two weeks from the given date
EXPAND_ADVANCE_DAYS = 14

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Print a dashboard of waiting-for items.", prog="waiting")
    parser.add_argument("-d", "--date", type=str, help="The current date.")
    parser.add_argument("-u", "--until", type=str, help="The cutoff date to surface items up until.")

    args = parser.parse_args(args)
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else date + timedelta(days=EXPAND_ADVANCE_DAYS)
    until.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    waiting_items = filter_to_waiting(action_items)
    upcoming = filter_to_upcoming(waiting_items, until, "all")

    display = display_actions(upcoming, date.date())
    rich_print(display)
