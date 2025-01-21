#!/usr/bin/env python3
# A scheduling script that takes the object of action items from stdin and prints an ICS file
# containing all action items with timestamps. This is intended to be composed with other scripts
# that filter those items.

import sys
from ics import Calendar, Event
import json
import re
from utils import timestamp_to_datetime

if __name__ == "__main__":
    cal_items = json.loads(sys.stdin.read())

    calendar = Calendar()
    for item in cal_items:
        # Form the body from the regular body and the associated people, if there are any
        body = item["body"]
        if item["people"]:
            body += "\n\nPeople: \n- " + "\n- ".join([name for name, _ in item["people"]])

        ts_start, ts_end = timestamp_to_datetime({"start": item["start"], "end": item["end"]})
        ev = Event(
            item["title"],
            begin=ts_start,
            description=body.strip()
        )
        if ts_end:
            ev.end = ts_end
        if not item["start"]["time"] and not item["end"]:
            ev.make_all_day()
        if item["location"]:
            ev.location = item["location"]

        calendar.events.add(ev)

    ics_str = calendar.serialize()
    # Remove all UTC timezone specifications (in DTSTART and DTEND properties)
    ics_str = re.sub(r'(DTSTART:\d+T\d+)Z', r'\1', ics_str)
    ics_str = re.sub(r'(DTEND:\d+T\d+)Z', r'\1', ics_str)

    print(ics_str)
