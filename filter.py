#!/usr/bin/env python3
# Script that filters next actions from `next_actions.py` down to those that match a specified
# list of available contexts, a maximum focus level, and/or a maximum amount of available time.

# TODO: sorting by relevance, somehow...

import json
import sys
import argparse
from utils import validate_time, validate_focus

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter next actions.")
    parser.add_argument("-c", "--context", action="append", dest="contexts", help="Contexts to filter by (list of ORs).")
    parser.add_argument("-p", "--people", action="append", dest="people", help="People to filter by (list of ORs).")
    parser.add_argument("-f", "--focus", type=str, help="Maximum focus to filter by.")
    parser.add_argument("-t", "--time", type=str, help="Maximum time to filter by.")

    args = parser.parse_args()
    contexts = set(args.contexts or [])
    people = set(args.people or [])
    time = validate_time(args.time, "INPUT") if args.time else None
    focus = validate_focus(args.focus, "INPUT") if args.focus else None

    next_actions = json.loads(sys.stdin.read())

    filtered = []
    for item in next_actions:
        # Skip all projects, they're not next actions and are only needed in the upcoming/urgent
        # sections
        if not item["time"]: continue

        # If we're filtering by context, this item's list of contexts is an AND list, so make sure
        # all of them are available in `contexts`, and exclude items that don't have any
        # of those contexts
        if contexts:
            we_have_all = True
            item_has_one = False
            for ctx in item["context"]:
                if ctx not in contexts:
                    we_have_all = False
                    break
                else:
                    item_has_one = True

            if not we_have_all or not item_has_one: continue
        if people:
            we_have_all = True
            item_has_one = False
            for person, _ in item["people"]:
                if person not in people:
                    we_have_all = False
                    break
                else:
                    item_has_one = True

            if not we_have_all or not item_has_one: continue
        # For time and focus, we have a maximum, allow anything up to that
        if time is not None:
            if item["time"] > time: continue
        if focus is not None:
            if item["focus"] > focus: continue

        filtered.append(item)

    # Sort by title
    filtered.sort(key=lambda item: item["title"])

    json.dump(filtered, sys.stdout, ensure_ascii=False)
