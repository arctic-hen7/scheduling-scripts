#!/usr/bin/env python3
# Script that gets action items from the Starling server for fitlering and display by the other
# scripts. This also expands any repeating timestamps into multiple entries (which will have the
# same ID), allowing later scripts to ignore that complexity.

import requests
import argparse
import copy
from datetime import datetime
from utils import dump_json, timestamp_to_datetime, STARLING_API

def get_action_items(opts):
    """
    Gets all action items from the Starling server, sending the provided extra arguments.
    """
    response = requests.get(f"{STARLING_API}/index/action_items/nodes", json={"conn_format": "markdown", "metadata": True, "children": True, **(opts or {})})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get action items: {response.text}")

def get_next_timestamp(timestamp):
    """
    Gets the next repeat of the given timestamp if there is one.
    """
    # Send the timestamp as a JSON body (adding back `active`)
    response = requests.get(f"{STARLING_API}/utils/next-timestamp", json={**timestamp, "active": True})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get next timestamp: {response.text}")

def ts_in_range(ts_start, ts_end, start, end):
    """
    Determines if the given timestamp is in the given range.
    """
    return ts_start <= end and (ts_end is None or ts_end >= start)

def has_ts_before(item, until):
    """
    Returns whether or not any timestamp on the given item applies before the given date. This
    is used to check when we should stop computing the repeats of an item.
    """

    if item["metadata"]["timestamp"]:
        ts_start, _ = timestamp_to_datetime(item["metadata"]["timestamp"])
        if ts_start <= until:
            return True

    scheduled = item["metadata"]["scheduled"]
    deadline = item["metadata"]["deadline"]
    closed = item["metadata"]["closed"]

    if scheduled and timestamp_to_datetime(scheduled)[0] <= until:
        return True
    if deadline and timestamp_to_datetime(deadline)[0] <= until:
        return True
    if closed and timestamp_to_datetime(closed)[0] <= until:
        return True

    return False

def repeat_once(item):
    """
    Produces the next repeat of the given entry, if there is one, by attempting to repeat
    all associated timestamps on their individual cadences.

    Like `repeat_until`, this should be passed the modified, single-main-timestamp, version
    of the item, and only for active main timestamps.
    """

    # Copy the whole entry and remove any timestamps, we'll add them back if they repeat
    is_next_repeat = False
    next_repeat = copy.deepcopy(item)
    next_repeat["metadata"]["timestamp"] = None
    next_repeat["metadata"]["scheduled"] = None
    next_repeat["metadata"]["deadline"] = None
    next_repeat["metadata"]["closed"] = None

    # If there's a repeating main timestamp, preserve that
    if item["metadata"]["timestamp"] and item["metadata"]["timestamp"]["repeater"] is not None:
        is_next_repeat = True
        next_repeat["metadata"]["timestamp"] = get_next_timestamp(item["metadata"]["timestamp"])

    scheduled = item["metadata"]["scheduled"]
    deadline = item["metadata"]["deadline"]
    closed = item["metadata"]["closed"]

    if scheduled and scheduled["repeater"] is not None:
        is_next_repeat = True
        next_repeat["metadata"]["scheduled"] = get_next_timestamp(scheduled)
    if deadline and deadline["repeater"] is not None:
        is_next_repeat = True
        next_repeat["metadata"]["deadline"] = get_next_timestamp(deadline)
    if closed and closed["repeater"] is not None:
        is_next_repeat = True
        next_repeat["metadata"]["closed"] = get_next_timestamp(closed)

    return next_repeat if is_next_repeat else None

def repeat_until(item, until):
    """
    Tries to repeat the given action item until the given date. This will return the repeaterless
    action items, as many as could be repeated in the given timeframe. If there are no repeating
    timestamps, the list will just contain the original item.

    This should be passed a modified version of the original Starling item with only one "main"
    timestamp (i.e. not planning, like deadline/scheduled). Items with multiple timestamps should
    thus have this function called multiple times on them so later scripts don't have to worry
    about items with multiple timestamps. This also simplifies repeating cadences.
    """
    repeats = []

    # While we loop, we need to keep repeater information for the next repeat
    while True:
        next_repeat = repeat_once(repeats[-1]) if len(repeats) > 0 else item
        if next_repeat is None or not has_ts_before(next_repeat, until):
            break
        repeats.append(next_repeat)

    # Make sure we take account of items that don't repeat
    if len(repeats) == 0:
        repeats.append(item)

    # But now we don't need repeater info anymore, so remove it
    for j, repeat in enumerate(repeats):
        repeat["id"] = f"{repeat['id']}-{j}"

        if repeat["metadata"]["timestamp"]:
            del repeat["metadata"]["timestamp"]["repeater"]
        if repeat["metadata"]["scheduled"]:
            del repeat["metadata"]["scheduled"]["repeater"]
        if repeat["metadata"]["deadline"]:
            del repeat["metadata"]["deadline"]["repeater"]
        if repeat["metadata"]["closed"]:
            del repeat["metadata"]["closed"]["repeater"]

    return repeats

def prune_inactive_ts(ts):
    """
    Removes the `active` key from active timestamps or returns `None` if they're inactive.
    """

    if not ts:
        return None
    elif not ts["active"]:
        return None
    else:
        del ts["active"]
        return ts

def get_normalised_action_items(until, opts=[]):
    """
    Gets the list of action items from Starling, extracting and repeating any timestamps so the
    caller doesn't have to worry about multiple or repeating timestamps. This will also entirely
    remove inactive timestamps.

    This will repeat timestamps until the given `until` date. This also takes an array of
    parameters to set to `true` when getting the data from the server (e.g. `body`).
    """

    items = get_action_items({key: True for key in opts})

    # Expand every timestamp to avoid handling the complexities of repeats later
    expanded_items = []
    for item in items:
        # Skip completed items (still indexed!)
        keyword = item["metadata"]["keyword"]
        if keyword and keyword == "DONE":
            continue

        # Remove inactive planning timestamps
        item["metadata"]["scheduled"] = prune_inactive_ts(item["metadata"]["scheduled"])
        item["metadata"]["deadline"] = prune_inactive_ts(item["metadata"]["deadline"])
        item["metadata"]["closed"] = prune_inactive_ts(item["metadata"]["closed"])

        # Split out multiple timestamps into separate items
        for i, ts in enumerate(item["metadata"]["timestamps"]):
            # Ignore any inactive main timestamps
            if not ts["active"]: continue
            del ts["active"]

            # Use this active main timestamp to guide a potential repeat cadence
            item_clone = copy.deepcopy(item)
            item_clone["id"] = f"{item['id']}-{i}"
            del item_clone["metadata"]["timestamps"]
            item_clone["metadata"]["timestamp"] = ts
            expanded_items.extend(repeat_until(item_clone, until))

        # Handle items with no main timestamps (they should still be accounted for)
        if not item["metadata"]["timestamps"]:
            del item["metadata"]["timestamps"]
            item["metadata"]["timestamp"] = None
            expanded_items.extend(repeat_until(item, until))

    return expanded_items

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Get action items from the Starling server.")
    parser.add_argument("until", type=str, help="The date to expand timestamps up until.")
    parser.add_argument("-o", action="append", dest="opts", help="Additional arguments to be set to true (e.g. body).")

    args = parser.parse_args()
    until = datetime.strptime(args.until, "%Y-%m-%d")

    dump_json(get_normalised_action_items(until, args.opts or []))
