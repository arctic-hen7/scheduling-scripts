#!/usr/bin/env python3
# Filters the given action items to a list of calendar events and scheduled work blocks.

import json
import sys
import argparse
from utils import associated_people, timestamp_to_datetime, body_for_proj
from datetime import datetime

def ts_in_range(ts, range_start, range_end):
    """
    Determines if the given timestamp is in the given range.
    """

    ts_start, ts_end = timestamp_to_datetime(ts)
    ts_end = ts_end or ts_start
    return (range_start and ts_start <= range_end and ts_end >= range_start) or (not range_start and ts_start <= range_end)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert action items to calendar events.")
    parser.add_argument("range", type=str, help="The range of dates to return events for (`start:end`).")

    args = parser.parse_args()
    if ":" in args.range:
        range_start, range_end = args.range.split(":")
    else:
        range_start = args.range
        range_end = range_start

    # It's possible to provide a range like `:X` to get only events from before that date
    # which haven't yet been marked as done
    range_start = datetime.strptime(range_start, "%Y-%m-%d") if range_start else None
    range_end = datetime.strptime(range_end, "%Y-%m-%d")
    # Make the range end be at the *very* end of the day
    range_end = range_end.replace(hour=23, minute=59, second=59)

    action_items = json.loads(sys.stdin.read())
    action_items = {item["id"]: item for item in action_items}

    # Get all the items with a timestamp, and insert them as many times as they have timestamps
    cals = []
    for item in action_items.values():
        # Strip out dates associated with people (e.g. birthdays), daily info items, and tickles
        if "person_dates" in item["parent_tags"] or "tickles" in item["parent_tags"] or "daily_notes" in item["parent_tags"]: continue

        ts = item["metadata"]["timestamp"]
        if ts and ts_in_range(ts, range_start, range_end):
            # If a project is scheduled, assemble a body of the project's tasks (which will
            # all be action items we should have, so we can get them by their IDs)
            if item["metadata"]["keyword"] == "PROJ":
                body = body_for_proj(item, action_items)
            else:
                body = item["body"] or ""

            cal_item = {
                "id": item["id"],
                "title": item["title"][-1],
                "body": body.strip(),
                "location": item["metadata"]["properties"].get("LOCATION"),
                "people": associated_people(item),
                "start": ts["start"],
                "end": ts["end"]
            }
            cals.append(cal_item)

    # Sort by start date, then start time, then title
    cals.sort(key=lambda x: (x["start"]["date"], x["start"]["time"] or "00:00", x["title"]))

    json.dump(cals, sys.stdout, ensure_ascii=False)
