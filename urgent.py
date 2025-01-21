#!/usr/bin/env python3
# Script that filters the given list of upcoming next actions and projects down to those which
# are urgent within a proximity cutoff (e.g. a week). This will show only those items which have
# a deadline before the proximity cutoff, and only if they've passed their scheduled cutoff. This
# takes in a current date to compute all this for, as well as a cutoff date. It's designed for use
# "in the field" to quickly see the items which haven't been scheduled already (handled by the
# upcoming filter) which need to be actioned very soon. They will be ordered by deadline.
#
# Because this script is designed to be synced with my phone, it doesn't import from utils.

import json
import sys
import argparse
from datetime import datetime, timedelta

def create_datetime(date_str, time_str=None):
    """
    Creates Python datetimes from Orgish time and date strings.
    """

    if time_str:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    return datetime.strptime(date_str, "%Y-%m-%d")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter by deadline dates to urgent items.")
    parser.add_argument("-d", "--date", type=str, required=True, help="The current date to filter by.")
    parser.add_argument("-p", "--proximity", type=int, required=True, help="The number of days into the future to consider.")

    args = parser.parse_args()
    current_date = datetime.strptime(args.date, "%Y-%m-%d")
    cutoff_date = current_date + timedelta(days=args.proximity)

    upcoming = json.loads(sys.stdin.read())

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

    # We've piggybacked off the upcoming filter's sorting implicitly
    json.dump(filtered, sys.stdout, ensure_ascii=False)
