# Filters the given action items to a list of calendar events and scheduled work blocks.

from .utils import associated_people, dump_json, load_json, parse_range_str, timestamp_to_datetime, body_for_proj

def ts_in_range(ts, range_start, range_end):
    """
    Determines if the given timestamp is in the given range.
    """

    ts_start, ts_end = timestamp_to_datetime(ts)
    ts_end = ts_end or ts_start
    return (range_start and ts_start <= range_end and ts_end >= range_start) or (not range_start and ts_start <= range_end)

def filter_to_calendar(action_items, range_start, range_end):
    """
    Filters the given action items to events and scheduled work blocks in the given datetime range.
    If you want to filter between days, make sure `range_end` has a time ending at 23:59.
    """
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

    return cals

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Convert action items to calendar events.", prog="cal")
    parser.add_argument("range", type=str, help="The range of dates to return events for (`start:end`).")

    args = parser.parse_args(args)
    range_start, range_end = parse_range_str(args.range)

    action_items = load_json()
    dump_json(filter_to_calendar(action_items, range_start, range_end))
