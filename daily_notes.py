#!/usr/bin/env python3
# Returns the daily notes for a particular range of dates.

import json
import sys
import argparse
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract daily notes from action items.")
    parser.add_argument("range", type=str, help="The range of dates to return daily notes for (`start:end`).")

    args = parser.parse_args()
    if ":" in args.range:
        range_start, range_end = args.range.split(":")
    else:
        range_start = args.range
        range_end = range_start

    # It's possible to provide a range like `:X` to get only notes from before that date
    # which haven't yet been marked as done
    range_start = datetime.strptime(range_start, "%Y-%m-%d") if range_start else None
    range_end = datetime.strptime(range_end, "%Y-%m-%d")
    # Make the range end be at the *very* end of the day
    range_end = range_end.replace(hour=23, minute=59, second=59)

    action_items = json.loads(sys.stdin.read())

    filtered = []
    for item in action_items:
        if "daily_notes" in item["parent_tags"]:
            # Daily notes should have a single-date timestamp, anything else is invalid
            ts = item["metadata"]["timestamp"]
            if ts and ts["end"]:
                raise ValueError(f"Daily note {item['id']} has an end timestamp")
            elif ts and ts["start"]["time"]:
                raise ValueError(f"Daily note {item['id']} has a time")
            elif ts:
                date = datetime.strptime(ts["start"]["date"], "%Y-%m-%d")
                if (range_start and range_start <= date <= range_end) or (not range_start and date <= range_end):
                    note_item = {
                        "id": item["id"],
                        "title": item["title"],
                        "body": (item["body"] or "").strip(),
                        "date": ts["start"]["date"],
                    }
                    filtered.append(note_item)

    # Sort by date
    filtered.sort(key=lambda x: (x["date"], x["title"]))

    json.dump(filtered, sys.stdout, ensure_ascii=False)
