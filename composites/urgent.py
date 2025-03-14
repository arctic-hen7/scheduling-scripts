# A composite for displaying next actions, filtered in some way.

from datetime import datetime, timedelta
from rich import print as rich_print

from ..upcoming import filter_to_upcoming
from ..urgent import filter_to_urgent
from ..dashboards.actions import display_actions
from ..next_actions import filter_to_next_actions
from ..get import get_normalised_action_items

# By default, consider everything in the next week urgent
PROXIMITY_DAYS = 7

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter by deadline dates to urgent items.", prog="urgent")
    parser.add_argument("-d", "--date", type=str, help="The current date to filter by.")
    parser.add_argument("-p", "--proximity", type=int, default=PROXIMITY_DAYS, help="The number of days into the future to consider.")
    ty_group = parser.add_mutually_exclusive_group()
    ty_group.add_argument("--problems", action="store_true", help="Only show problems.")
    ty_group.add_argument("--tasks", action="store_true", help="Only show tasks.")

    args = parser.parse_args(args)
    current_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    cutoff_date = current_date + timedelta(days=args.proximity)
    current_date.replace(hour=0, minute=0, second=0)
    cutoff_date.replace(hour=23, minute=59, second=59)
    ty = "problems" if args.problems else "tasks" if args.tasks else "all"

    action_items = get_normalised_action_items(cutoff_date, ["body"])
    next_actions = filter_to_next_actions(action_items)
    upcoming = filter_to_upcoming(next_actions, cutoff_date, ty)
    urgent = filter_to_urgent(upcoming, current_date, cutoff_date)

    display = display_actions(urgent, current_date.date())
    rich_print(display)
