# Filters the given action items down to people-related dates and displays them up until
# a given cutoff date.

import requests
import urllib.parse
from datetime import datetime, timedelta
from .utils import STARLING_API, load_json, dump_json

def get_person_name(filename):
    """
    Gets the name and ID of the person described in the given file.
    """

    filename = urllib.parse.quote(filename, safe=[])
    response = requests.get(f"{STARLING_API}/root-id/{filename}")
    if response.status_code == 200:
        root_id = response.json()
        response = requests.get(f"{STARLING_API}/node/{root_id}", json={"conn_format": "markdown"})
        if response.status_code == 200:
            data = response.json()
            name = data["title"][-1].removeprefix("(Person) ")
            return [name, data["id"]]
        else:
            raise Exception(f"Failed to get person name: {response.text}")
    else:
        raise Exception(f"Failed to get person root ID: {response.text}")

def parse_advance(advance_str, id):
    """
    Parses advance strings of the form `Xw Yd` or similar into a number of days.
    """

    if not advance_str:
        raise ValueError(f"No advance string for person-related date {id}")
    advance = 0
    for part in advance_str.split():
        if part.endswith("w"):
            advance += int(part[:-1]) * 7
        elif part.endswith("d"):
            advance += int(part[:-1])
        else:
            raise ValueError(f"Invalid advance string in date {id}: {advance_str}")
    return advance

def filter_to_dates(action_items, until):
    """
    Filters the given action items to important dates about people. This will return all those
    dates whose advance warning periods fall before the given `until` date.
    """

    filtered = []
    for item in action_items:
        if "person_dates" in item["parent_tags"]:
            # Person-related dates should have a single-date timestamp, anything else is invalid
            ts = item["metadata"]["timestamp"]
            if ts and ts["end"]:
                raise ValueError(f"Person-related date {item['id']} has an end timestamp")
            elif ts and ts["start"]["time"]:
                raise ValueError(f"Person-related date {item['id']} has a timestamp with a time")
            elif ts:
                date = datetime.strptime(ts["start"]["date"], "%Y-%m-%d")
                # There should also be a property that tells us how long in advance we should be
                # notified of this date
                advance = parse_advance(item["metadata"]["properties"].get("ADVANCE"), item["id"])
                notify_date = date + timedelta(days=-advance)

                if notify_date <= until:
                    tickle_item = {
                        "id": item["id"],
                        "title": item["title"],
                        "body": (item["body"] or "").strip(),
                        "date": ts["start"]["date"],
                        # We could just use the first element of the title, but that wouldn't get us
                        # their ID as well
                        "person": get_person_name(item["path"]),
                    }
                    filtered.append(tickle_item)

    # Sort by date
    filtered.sort(key=lambda x: (x["date"], x["title"], x["person"][0]))

    return filtered

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Extract people-related dates from action items, up until a given date.", prog="dates")
    parser.add_argument("date", type=str, help="The date to extract people-related dates up until.")

    args = parser.parse_args(args)
    until = datetime.strptime(args.date, "%Y-%m-%d")

    action_items = load_json()
    dump_json(filter_to_dates(action_items, until))
