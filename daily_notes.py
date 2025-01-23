# Returns the daily notes for a particular range of dates.

from datetime import datetime
import uuid
from .utils import load_json, dump_json, parse_range_str

def daily_notes_to_cal(daily_notes):
    """
    Converts the given daily notes to a calendar item for each date, allowing them to be placed in
    the calendar as all-day informational events.
    """

    if not daily_notes:
        return []

    cal_items = {}
    for note in daily_notes:
        if note["date"] not in cal_items:
            cal_items[note["date"]] = {
                "id": uuid.uuid4().hex,
                "title": "📍 Daily information",
                "body": "",
                "location": None,
                "people": [],
                "start": {
                    "date": note["date"],
                    "time": None,
                },
                "end": None
            }

        body = note["body"].replace("\\$", "$")
        cal_items[note["date"]]["body"] += f"# {note['title']}\n{body}\n\n"

    cal_items = list(cal_items.values())
    for cal_item in cal_items:
        cal_item["body"] = cal_item["body"].strip()

    return cal_items

def filter_to_daily_notes(action_items, range_start, range_end):
    """
    Filters the given action items to daily notes in the given datetime range. If you want to
    filter between days, make sure `range_end` has a time ending at 23:59.
    """

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
                        "title": item["title"][-1],
                        "body": (item["body"] or "").strip(),
                        "date": ts["start"]["date"],
                    }
                    filtered.append(note_item)

    # Sort by date
    filtered.sort(key=lambda x: (x["date"], x["title"]))

    return filtered

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Extract daily notes from action items.", prog="daily_notes")
    parser.add_argument("range", type=str, help="The range of dates to return daily notes for (`start:end`).")

    args = parser.parse_args(args)
    range_start, range_end = parse_range_str(args.range)

    action_items = load_json()
    dump_json(filter_to_daily_notes(action_items, range_start, range_end))
