# A scheduling script that takes the object of action items from stdin and prints an ICS file
# containing all action items with timestamps. This is intended to be composed with other scripts
# that filter those items.

import re
from ics import Calendar, Event
from .utils import load_json, timestamp_to_datetime
from .daily_notes import daily_notes_to_cal

def cal_to_ics(cal_items):
    """
    Converts the given list of action items to an ICS calendar string.
    """

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

    return ics_str

def main_cli(_):
    # We'll either have an array of calendar items, or a hybrid stream with `calendar` and
    # `daily_notes` keys
    json_data = load_json()
    if isinstance(json_data, dict):
        cal_items = json_data["calendar"]
        cal_items.extend(daily_notes_to_cal(json_data["daily_notes"]))
    else:
        cal_items = json_data

    ics_str = cal_to_ics(cal_items)
    print(ics_str)
