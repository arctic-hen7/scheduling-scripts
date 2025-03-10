# The main weekly dashboard, which displays a calendar, upcoming actions, important dates, tickles,
# and waiting-for items over the coming week, from tomorrow.

from datetime import datetime, timedelta
from rich import print as rich_print
from rich.table import Table
from rich.panel import Panel
from ..dashboards.tickles import display_tickles
from ..waiting import filter_to_waiting
from ..tickles import filter_to_tickles
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
    parser = argparse.ArgumentParser(description="Return a dashboard for the given week.", prog="week")
    parser.add_argument("-d", "--date", type=str, help="The date to start the week on.")

    args = parser.parse_args(args)
    if args.date == "tmrw" or args.date == "tomorrow":
        date = datetime.now() + timedelta(days=1)
    elif not args.date:
        date = datetime.now()
    else:
        date = datetime.strptime(args.date, "%Y-%m-%d")

    date.replace(hour=0, minute=0, second=0)
    until = (date + timedelta(days=7)).replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    dates = filter_to_dates(action_items, until)
    next_actions = filter_to_next_actions(action_items)
    upcoming = filter_to_upcoming(next_actions, until, "all")
    tickles = filter_to_tickles(action_items, until)
    waiting_items = filter_to_upcoming(filter_to_waiting(action_items), until, "all")

    upcoming_view = Panel(display_actions(upcoming, date.date()), title="Upcoming Actions")
    tickles_view = Panel(display_tickles(tickles, date.date()), title="Tickles")
    waiting_view = Panel(display_actions(waiting_items, date.date()), title="Waiting-For Items")
    dates_view = Panel(display_dates(dates, date.date()), title="Important Dates")

    # The calendar/daily notes views are split into two halves
    cal_items_1 = filter_to_calendar(action_items, date, until - timedelta(days=3))
    daily_notes_1 = filter_to_daily_notes(action_items, date, until - timedelta(days=3))
    cal_items_2 = filter_to_calendar(action_items, until - timedelta(days=3), until)
    daily_notes_2 = filter_to_daily_notes(action_items, until - timedelta(days=3), until)

    cal_view_1 = Panel(display_calendar(cal_items_1, daily_notes_1), title="Calendar")
    cal_view_2 = Panel(display_calendar(cal_items_2, daily_notes_2), title="Calendar")

    # Layouts are the size of the terminal, we have more content so use nested grids
    view = Table.grid()
    view.add_column()
    view.add_column()
    view.add_row(cal_view_1, cal_view_2)
    view.add_row(dates_view, waiting_view)
    view.add_row(tickles_view, upcoming_view)

    rich_print(view)
