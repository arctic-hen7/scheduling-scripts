# A composite for accumulating calendar and daily note info and displaying it.

from rich import print as rich_print
from ..cal import filter_to_calendar
from ..daily_notes import filter_to_daily_notes
from ..get import get_normalised_action_items
from ..dashboards.cal import display_calendar
from ..utils import parse_range_str

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Extract daily notes from action items.", prog="cal")
    parser.add_argument("range", type=str, help="The range of dates to return daily notes for (`start:end`).")

    args = parser.parse_args(args)
    range_start, range_end = parse_range_str(args.range)

    action_items = get_normalised_action_items(range_end, ["body"])
    cal_items = filter_to_calendar(action_items, range_start, range_end)
    daily_notes = filter_to_daily_notes(action_items, range_start, range_end)

    cal_display = display_calendar(cal_items, daily_notes)
    rich_print(cal_display)
