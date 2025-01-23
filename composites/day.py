# The main daily dashboard, which displays a calendar, upcoming actions, and important dates for
# the given date (typically tomorrow).

from datetime import datetime, timedelta
from rich import print as rich_print
from rich.table import Table
from rich.panel import Panel
from ..cal import filter_to_calendar
from ..daily_notes import filter_to_daily_notes
from ..next_actions import filter_to_next_actions
from ..upcoming import filter_to_upcoming
from ..get import get_normalised_action_items
from ..dates import filter_to_dates
from ..dashboards.cal import display_calendar
from ..dashboards.actions import display_actions
from ..dashboards.dates import display_dates

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Return a dashboard for the given date.", prog="day")
    parser.add_argument("-d", "--date", type=str, help="The date.")

    args = parser.parse_args(args)
    if args.date == "tmrw" or args.date == "tomorrow":
        date = datetime.now() + timedelta(days=1)
    elif not args.date:
        date = datetime.now()
    else:
        date = datetime.strptime(args.date, "%Y-%m-%d")

    date.replace(hour=0, minute=0, second=0)
    until = date.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    cal_items = filter_to_calendar(action_items, date, until)
    daily_notes = filter_to_daily_notes(action_items, date, until)
    next_actions = filter_to_next_actions(action_items)
    upcoming = filter_to_upcoming(next_actions, until)
    dates = filter_to_dates(action_items, until)

    cal_view = Panel(display_calendar(cal_items, daily_notes), title="Calendar")
    upcoming_view = Panel(display_actions(upcoming, date.date()), title="Upcoming Actions")
    dates_view = Panel(display_dates(dates, date.date()), title="Important Dates")

    # Layouts are the size of the terminal, we have more content so use nested grids
    view = Table.grid()
    view.add_column()

    cal_dates_view = Table.grid()
    cal_dates_view.add_row(cal_view)
    cal_dates_view.add_row(dates_view)

    view.add_row(cal_dates_view, upcoming_view)

    rich_print(view)
