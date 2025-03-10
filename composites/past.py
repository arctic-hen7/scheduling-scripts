# A dashboard of all calendar entries and important dates up to one day before the given date,
# which shows everything needing refiling/clearing.

from datetime import datetime, timedelta
from rich import print as rich_print
from rich.table import Table
from rich.panel import Panel
from ..dashboards.tickles import display_tickles
from ..tickles import filter_to_tickles
from ..waiting import filter_to_waiting
from ..cal import filter_to_calendar
from ..daily_notes import filter_to_daily_notes
from ..get import get_normalised_action_items
from ..dates import filter_to_dates
from ..upcoming import filter_to_upcoming
from ..dashboards.cal import display_calendar
from ..dashboards.actions import display_actions
from ..dashboards.dates import display_dates

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Return a dashboard for everything prior to the given date.", prog="day")
    parser.add_argument("-d", "--date", type=str, help="The date.")

    args = parser.parse_args(args)
    if args.date == "tmrw" or args.date == "tomorrow":
        date = datetime.now()
    elif not args.date:
        date = datetime.now() - timedelta(days=1)
    else:
        date = datetime.strptime(args.date, "%Y-%m-%d") - timedelta(days=1)

    until = date.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    cal_items = filter_to_calendar(action_items, None, until)
    daily_notes = filter_to_daily_notes(action_items, None, until)
    dates = filter_to_dates(action_items, until)
    tickles = filter_to_tickles(action_items, until)
    waiting_items = filter_to_upcoming(filter_to_waiting(action_items), until, "all")

    cal_view = Panel(display_calendar(cal_items, daily_notes), title="Calendar")
    tickles_view = Panel(display_tickles(tickles, date.date()), title="Tickles")
    waiting_view = Panel(display_actions(waiting_items, date.date()), title="Waiting-For Items")
    dates_view = Panel(display_dates(dates, date.date()), title="Important Dates")

    view = Table.grid()
    view.add_column()
    view.add_column()
    view.add_row(cal_view, tickles_view)
    view.add_row(dates_view, waiting_view)

    rich_print(view)
