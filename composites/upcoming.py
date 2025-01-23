# A composite for displaying next actions, filtered in some way.

from datetime import datetime, timedelta
from rich import print as rich_print
from ..upcoming import filter_to_upcoming
from ..dashboards.actions import display_actions
from ..next_actions import filter_to_next_actions
from ..get import get_normalised_action_items

# By default, expand everything a week from the given date
EXPAND_ADVANCE_DAYS = 7

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter by deadline/scheduled dates to upcoming items.", prog="upcoming")
    parser.add_argument("-d", "--date", type=str, help="The current date.")
    parser.add_argument("-u", "--until", type=str, help="The cutoff date to surface scheduled items up until.")

    args = parser.parse_args(args)
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else date + timedelta(days=EXPAND_ADVANCE_DAYS)
    until.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    next_actions = filter_to_next_actions(action_items)
    upcoming = filter_to_upcoming(next_actions, until)

    display = display_actions(upcoming, date.date())
    rich_print(display)
