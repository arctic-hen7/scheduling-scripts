#!/usr/bin/env python3

import json
import sys
import argparse
from utils import associated_people, body_for_proj, create_datetime, validate_focus, validate_time, validate_planning_ts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter action items for next actions.")
    parser.add_argument("-c/--context", action="append", dest="contexts", help="Contexts to filter by (list of ORs).")
    parser.add_argument("-p/--people", action="append", dest="people", help="People to filter by (list of ORs).")
    parser.add_argument("-f/--focus", type=str, help="Maximum focus to filter by.")
    parser.add_argument("-t/--time", type=str, help="Maximum time to filter by.")

    args = parser.parse_args()

    action_items = json.loads(sys.stdin.read())
    action_items = {item["id"]: item for item in action_items}

    filtered = []
    for item in action_items.values():
        if item["metadata"]["keyword"]:
            if item["metadata"]["keyword"] == "PROJ":
                # Only include projects if they have scheduled/deadline timestamps that would make
                # them appear (otherwise they're not really *next actions*). Alternately, they
                # might have an actual timestamp which will impact the scheduling of their children,
                # so definitely include those!
                if not item["metadata"]["scheduled"] and not item["metadata"]["deadline"] and not item["metadata"]["timestamp"]: 
                    continue

                body = body_for_proj(item, action_items)
                # Projects don't have these, tasks do
                time = None
                focus = None
                people = None
                context = None
            else:
                body = item["body"] or ""
                time = validate_time(item["metadata"]["properties"].get("TIME"), item["id"])
                focus = validate_focus(item["metadata"]["properties"].get("FOCUS"), item["id"])
                people = associated_people(item)
                context = item["tags"]

            scheduled = validate_planning_ts(item["metadata"]["scheduled"], item["id"])
            deadline = validate_planning_ts(item["metadata"]["deadline"], item["id"])

            # Sanity check that the scheduled date is before the deadline date
            scheduled_dt = create_datetime(scheduled["date"], scheduled["time"]) if scheduled else None
            deadline_dt = create_datetime(deadline["date"], deadline["time"]) if deadline else None
            if scheduled_dt and deadline_dt and scheduled_dt > deadline_dt:
                raise ValueError(f"Item {item['id']} has a scheduled date after its deadline date")

            next_action = {
                "id": item["id"],
                "parent_id": item["parent_id"],
                "title": item["title"][-1],
                "body": body.strip(),
                "scheduled": validate_planning_ts(item["metadata"]["scheduled"], item["id"]),
                "deadline": validate_planning_ts(item["metadata"]["deadline"], item["id"]),
                "timestamp": item["metadata"]["timestamp"],
                "people": people,
                "context": context,
                "time": time,
                "focus": focus,
            }


            filtered.append(next_action)

    json.dump(filtered, sys.stdout, ensure_ascii=False)
