#!/usr/bin/env python3
# Script that filters the given list of upcoming next actions and projects down to those which
# are urgent.

from datetime import datetime, timedelta
from utils import create_datetime, dump_json, load_json

def filter_to_urgent(upcoming, current_date, cutoff_date):
    """
    Filters the given next actions (which are expected to have gone through the upcoming filter)
    to those with deadlines before the given cutoff date, provided they've passed their scheduled
    date with respect to the given current date.
    """

    filtered = []
    for item in upcoming:
        # Anything without a deadline will never be urgent
        if not item["deadline"]: continue

        deadline = create_datetime(item["deadline"]["date"], item["deadline"]["time"])
        scheduled = create_datetime(item["scheduled"]["date"], item["scheduled"]["time"]) if item["scheduled"] else None

        # Skip anything we haven't reached the scheduled date for yet (next actions filter
        # guarantees the deadline is after it)
        if scheduled and scheduled > current_date:
            continue
        # Skip anything with a deadline after the cutoff date, that's too far in the future to be
        # considered urgent for our purposes
        if deadline > cutoff_date:
            continue

        filtered.append(item)

    # The upcoming filter did the ordering by deadline/scheduled for us
    return filtered

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Filter by deadline dates to urgent items.")
    parser.add_argument("-d", "--date", type=str, required=True, help="The current date to filter by.")
    parser.add_argument("-p", "--proximity", type=int, required=True, help="The number of days into the future to consider.")

    args = parser.parse_args()
    current_date = datetime.strptime(args.date, "%Y-%m-%d")
    cutoff_date = current_date + timedelta(days=args.proximity)

    upcoming = load_json()
    dump_json(filter_to_urgent(upcoming, current_date, cutoff_date))
