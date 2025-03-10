# Script that filters next actions/waiting-for items down to those that are upcoming.

from datetime import datetime
from .utils import create_datetime, dump_json, load_json, should_surface_item

def filter_to_upcoming(items, until, ty):
    """
    Filters the given next actions down to those which are upcoming with respect to the given date.
    Specifically, this will surface items with a scheduled date before the given cutoff, as well as
    any items with a deadline at any time. In both cases, it will first check to ensure the item or
    its project parent doesn't have a timestamp set for when to work on it (the user is considered
    to have handled these, so surfacing them would just be clutter).

    This can work with both next actions and waiting-for items; technically anything with `scheduled`
    and/or `deadline` dates.
    """

    items_map = {item["id"]: item for item in items}

    filtered = []
    for item in items:
        if ty == "tasks" and item["keyword"] != "TODO": continue
        if ty == "problems" and item["keyword"] != "PROB": continue

        if item["scheduled"]:
            # This is guaranteed not to have an end datetime from the next actions filter
            scheduled = create_datetime(item["scheduled"]["date"], item["scheduled"]["time"])

            # Check timestamps and cross-reference with the deadline
            if not should_surface_item(item, items_map):
                continue

            # We've filtered out anything that's already been scheduled (and by doing that on
            # everything with a scheduled date implicitly checked possible timestamp issues), so
            # surface this if the scheduled date falls within our window
            if scheduled <= until:
                filtered.append(item)
        elif item["deadline"]:
            # We have a deadline without a scheduled constraint, this should be displayed always
            # unless there's a timestamp (check validity as before)
            if not should_surface_item(item, items_map):
                continue

            filtered.append(item)

    # Sort by scheduled/deadline date (whichever the item has, scheduled first), and then deadline
    filtered.sort(
        key=lambda item:
            (
                item["scheduled"]["date"] if item["scheduled"] else item["deadline"]["date"],
                item["scheduled"]["time"] or "" if item["scheduled"] else item["deadline"]["time"] or "",
                item["deadline"]["date"] if item["deadline"] else "",
                item["deadline"]["time"] or "" if item["deadline"] else "",
                item["title"]
            )
    )

    return filtered

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter by deadline/scheduled dates to upcoming items.", prog="upcoming")
    parser.add_argument("date", type=str, help="The cutoff date to surface scheduled items up until.")
    ty_group = parser.add_mutually_exclusive_group()
    ty_group.add_argument("--problems", action="store_true", help="Only show problems.")
    ty_group.add_argument("--tasks", action="store_true", help="Only show tasks.")

    args = parser.parse_args(args)
    until = datetime.strptime(args.date, "%Y-%m-%d")
    until.replace(hour=23, minute=59, second=59)
    ty = "problems" if args.problems else "tasks" if args.tasks else "all"

    items = load_json()
    dump_json(filter_to_upcoming(items, until, ty))
