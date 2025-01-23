# A composite for accumulating calendar and daily note info and displaying it. This can also
# return the calendar as ICS or upload it to Google.

from rich import print as rich_print
from ..gcal import upload_to_gcal
from ..ical import cal_to_ics
from ..cal import filter_to_calendar
from ..daily_notes import filter_to_daily_notes, daily_notes_to_cal
from ..get import get_normalised_action_items
from ..dashboards.cal import display_calendar
from ..utils import parse_range_str

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Extract daily notes from action items.", prog="cal")
    parser.add_argument("range", type=str, help="The range of dates to return daily notes for (`start:end`).")
    parser.add_argument("--gcal-email", type=str, default="env:GOOGLE_EMAIL", help="The email address to upload to Google Calendar with.")
    parser.add_argument("--gcal-calendar", type=str, default="primary", help="The calendar to upload to in Google Calendar.")
    parser.add_argument("--gcal-creds", type=str, default="env:GOOGLE_CALENDAR_CREDS", help="The path to the Google Calendar credentials file.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--text", default=True, action="store_true", help="Output to rich text.")
    output_group.add_argument("--ics", action="store_true", help="Output in iCalendar format.")
    output_group.add_argument("--gcal", action="store_true", help="Upload to Google Calendar.")

    args = parser.parse_args(args)
    range_start, range_end = parse_range_str(args.range)

    action_items = get_normalised_action_items(range_end, ["body"])
    cal_items = filter_to_calendar(action_items, range_start, range_end)
    daily_notes = filter_to_daily_notes(action_items, range_start, range_end)

    if args.ics:
        cal_items.extend(daily_notes_to_cal(daily_notes))
        ics_str = cal_to_ics(cal_items)
        print(ics_str)
    elif args.gcal:
        cal_items.extend(daily_notes_to_cal(daily_notes))
        upload_to_gcal(cal_items, args.gcal_email, args.gcal_calendar, args.gcal_creds)
        print("Calendar items uploaded successfully!")
    elif args.text: # Check last because default
        cal_display = display_calendar(cal_items, daily_notes)
        rich_print(cal_display)
