# A composite for displaying next actions, filtered in some way.

from datetime import datetime
from rich import print as rich_print
from ..dashboards.actions import display_actions
from ..next_actions import filter_to_next_actions
from ..filter import filter_next_actions
from ..get import get_normalised_action_items
from ..utils import validate_time, validate_focus

# By default, expand everything two weeks from the given date
EXPAND_ADVANCE_DAYS = 14

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter next actions.", prog = "actions")
    parser.add_argument("-d", "--date", type=str, help="The current date.")
    parser.add_argument("-u", "--until", type=str, help="Date to get next actions up until (default: `date`).")
    parser.add_argument("-c", "--context", action="append", dest="contexts", help="Contexts to filter by (list of ORs).")
    parser.add_argument("-p", "--people", action="append", dest="people", help="People to filter by (list of ORs).")
    parser.add_argument("-f", "--focus", type=str, help="Maximum focus to filter by.")
    parser.add_argument("-t", "--time", type=str, help="Maximum time to filter by.")
    ty_group = parser.add_mutually_exclusive_group()
    ty_group.add_argument("--problems", action="store_true", help="Only show problems.")
    ty_group.add_argument("--tasks", action="store_true", help="Only show tasks.")

    args = parser.parse_args(args)
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else date
    date.replace(hour=0, minute=0, second=0)
    until.replace(hour=23, minute=59, second=59)
    time = validate_time(args.time, "INPUT") if args.time else None
    focus = validate_focus(args.focus, "INPUT") if args.focus else None
    ty = "problems" if args.problems else "tasks" if args.tasks else "all"

    action_items = get_normalised_action_items(until, ["body"])
    next_actions = filter_to_next_actions(action_items)
    filtered = filter_next_actions(next_actions, until, args.contexts or [], args.people or [], time, focus, ty)

    display = display_actions(filtered, date.date())
    rich_print(display)
