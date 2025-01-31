# Collects goals for the previous day, relevant week, and general things to surface daily to
# produce a Markdown file the user can review at the start of the given date to help them
# stay on track and live their best life.

import os
from pathlib import Path
import requests
from datetime import datetime, timedelta
from .utils import STARLING_API

# Change this!
DAILY_SURFACES_ID = "9a73deb2-e702-47d0-8967-dc82de424237"
DAILY_GOALS_TITLE = "Goals for Tomorrow"
WEEKLY_GOALS_TITLE = "Goals for Next Week"

def get_daily_surfaces():
    """
    Gets the body of the items which should be surfaced every day (expected to be a list). This
    goes off a hardcoded ID.
    """

    response = requests.get(f"{STARLING_API}/node/{DAILY_SURFACES_ID}", json={"conn_format": "markdown", "body": True})
    if response.status_code == 200:
        goals = response.json()["body"].strip()
        if goals == "-" or goals == "":
            return []
        else:
            return ("\n" + goals).split("\n- ")[1:]
    else:
        raise Exception(f"Failed to get daily surfaces: {response.text}")

def get_journal_goals(date, heading):
    """
    Gets the goals noted down in the journal file for the given date under the given heading, which
    allows this function to be used for both daily and weekly goal fetching. This will return an
    empty array if there are no goals, or if the journal file does not exist.
    """

    journal_path = os.environ["ACE_JOURNALS_DIR"] + f"/{date.strftime('%Y')}/{date.strftime('%m')}/{date.strftime('%d')}.md"
    if not os.path.exists(journal_path):
        return []

    # We have an absolute path, but it needs to be relative to `$ACE_MAIN_DIR`
    journal_path = Path(journal_path).relative_to(os.environ["ACE_MAIN_DIR"])
    journal_path_url = "%2F".join(journal_path.parts)

    response = requests.get(f"{STARLING_API}/root-id/{journal_path_url}")
    if response.status_code == 200:
        root_id = response.json()

        response = requests.get(f"{STARLING_API}/node/{root_id}", json={"conn_format": "markdown", "children": True})
        if response.status_code == 200:
            for child in response.json()["children"]:
                if child[1] == heading:
                    response = requests.get(f"{STARLING_API}/node/{child[0]}", json={"conn_format": "markdown", "body": True})
                    if response.status_code == 200:
                        goals = response.json()["body"].strip()
                        if goals == "-" or goals == "":
                            return []
                        else:
                            return ("\n" + goals).split("\n- ")[1:]
                    else:
                        raise Exception(f"Failed to get goals under '{heading}' for {date}: {response.text}")
            return []
        else:
            raise Exception(f"Failed to get daily journal node for {date}: {response.text}")
    else:
        raise Exception(f"Failed to get root ID of journal for {date}: {response.text}")

def get_week_date(date):
    """
    Gets the date of the Sunday of the week before the one the given date is in (i.e. the date of
    the journal file where the weekly goals for the week the given date is in are stored).
    """

    # We want to get the Sunday of the week before the one the given date is in
    return date - timedelta(days=date.weekday() + 1)

def assemble_goals_file(date):
    """
    Produces a Markdown file containing all the goals for each period, to provide a suamry for the
    given date.
    """

    daily_surfaces = get_daily_surfaces()
    day_goals = get_journal_goals(date - timedelta(days=1), DAILY_GOALS_TITLE)
    week_goals = get_journal_goals(get_week_date(date), WEEKLY_GOALS_TITLE)

    daily_surfaces_str = "- " + "\n- ".join(daily_surfaces) if daily_surfaces else "*No daily surfaces.*"
    day_goals_str = "- " + "\n- ".join(day_goals) if day_goals else "*No daily goals.*"
    week_goals_str = "- " + "\n- ".join(week_goals) if week_goals else "*No weekly goals.*"

    return f"# Daily Goals\n\n{day_goals_str}\n\n# Weekly Goals\n\n{week_goals_str}\n\n# Daily Surfaces\n\n{daily_surfaces_str}"

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Collects goals for the previous day, relevant week, and general things to surface daily.", prog="goals")
    parser.add_argument("date", help="The date to prepare a morning goal summary for.")

    args = parser.parse_args(args)
    date = datetime.strptime(args.date, "%Y-%m-%d")

    print(assemble_goals_file(date))
