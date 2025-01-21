#!/usr/bin/env python3
# Returns the "tickles" with timestamps up until a given date.

import json
import sys
import argparse
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract tickles from action items, up until a given date.")
    parser.add_argument("date", type=str, help="The date to extract tickles up until.")

    args = parser.parse_args()
    until = datetime.strptime(args.date, "%Y-%m-%d")

    action_items = json.loads(sys.stdin.read())

    filtered = []
    for item in action_items:
        if "tickles" in item["parent_tags"]:
            # Tickles should have a single-date timestamp, anything else is invalid
            ts = item["metadata"]["timestamp"]
            if ts and ts["end"]:
                raise ValueError(f"Item {item['id']} has a tickle with an end timestamp")
            elif ts and ts["start"]["time"]:
                raise ValueError(f"Item {item['id']} has a tickle with a time")
            elif ts:
                date = datetime.strptime(ts["start"]["date"], "%Y-%m-%d")
                if date <= until:
                    tickle_item = {
                        "id": item["id"],
                        "title": item["title"],
                        "body": (item["body"] or "").strip(),
                        "date": ts["start"]["date"],
                    }
                    filtered.append(tickle_item)

    # Sort by date
    filtered.sort(key=lambda x: (x["date"], x["title"]))

    json.dump(filtered, sys.stdout, ensure_ascii=False)
