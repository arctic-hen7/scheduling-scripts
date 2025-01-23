# Script that filters next actions/waiting-for items down to those that are upcoming.

import sys
from datetime import datetime
from .utils import create_datetime, dump_json, load_json, timestamp_to_datetime, find_task_timestamp

def should_surface_item(item, items):
    """
    Checks if the given item, or its project parent (if it has one) has a timestamp that would
    mean it doesn't need to be surfaced in the upcoming list. If it does, this will also make
    sure that timestamp makes sense with the item's deadline, if it has one.

    This returns `True` if the item should be surfaced, and `False` if it should not, and it
    will write a warning to stderr if the timestamp would not meet the deadline.
    """

    ts = find_task_timestamp(item, items)
    if ts and item["deadline"]:
        # We have a timestamp and a deadline it needs to come before
        deadline = create_datetime(item["deadline"]["date"], item["deadline"]["time"])
        ts_start, ts_end = timestamp_to_datetime(ts)
        # Deliberate `<` here; if the user starts *at* the deadline, that is pretty dumb
        if ts_start < deadline and (ts_end is None or ts_end <= deadline):
            # It does, the schedule is valid, we don't need to surface it
            return False
        else:
            # Bad schedule, warn the user! (stderr because stdout is for the JSON)
            sys.stderr.write(f"Warning: Scheduled item {item['id']} has a deadline you won't meet under current schedule!\n")
            return False
    elif ts:
        # If there's no deadline date to adhere to, but we have slated this to work on at
        # some stage, it doesn't need to be surfaced
        return False
    else:
        return True

def filter_to_upcoming(items, until):
    """
    Filters the given next actions down to those which are upcoming with respect to the given date.
    Specifically, this will surface items with a scheduled date before the given cutoff, as well as
    any items with a deadline at any time. In both cases, it will first check to ensure the item or
    its project parent doesn't have a timestamp set for when to work on it (the user is considered
    to have handled these, so surfacing them would just be clutter).

    This can work with both next actions and waiting-for items; technically anything with `scheduled`
    and/or `deadline` dates.
    """

    items = {item["id"]: item for item in items}

    filtered = []
    for item in items.values():
        if item["scheduled"]:
            # This is guaranteed not to have an end datetime from the next actions filter
            scheduled = create_datetime(item["scheduled"]["date"], item["scheduled"]["time"])

            # Check timestamps and cross-reference with the deadline
            if not should_surface_item(item, items):
                continue

            # We've filtered out anything that's already been scheduled (and by doing that on
            # everything with a scheduled date implicitly checked possible timestamp issues), so
            # surface this if the scheduled date falls within our window
            if scheduled <= until:
                filtered.append(item)
        elif item["deadline"]:
            # We have a deadline without a scheduled constraint, this should be displayed always
            # unless there's a timestamp (check validity as before)
            if not should_surface_item(item, items):
                continue

            filtered.append(item)

    # Sort by scheduled/deadline date (whichever the item has, scheduled first), and then deadline
    filtered.sort(
        key=lambda item:
            (
                item["scheduled"]["date"] if item["scheduled"] else item["deadline"]["date"],
                item["scheduled"]["time"] if item["scheduled"] else item["deadline"]["time"],
                item["deadline"]["date"] if item["deadline"] else "",
                item["deadline"]["time"] if item["deadline"] else "",
                item["title"]
            )
    )

    return filtered

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter by deadline/scheduled dates to upcoming items.", prog="upcoming")
    parser.add_argument("date", type=str, help="The cutoff date to surface scheduled items up until.")

    args = parser.parse_args(args)
    until = datetime.strptime(args.date, "%Y-%m-%d")
    until.replace(hour=23, minute=59, second=59)

    items = load_json()
    dump_json(filter_to_upcoming(items, until))
