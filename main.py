#!/usr/bin/env python3
# Central entrypoint script.

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scheduling_scripts import cal, daily_notes, dates, filter, gcal, get, ical, next_actions, tickle, upcoming, urgent, waiting, dashboards
from scheduling_scripts.dashboards import actions as d_actions
from scheduling_scripts.composites import cal as c_cal, actions as c_actions

# This script acts as the central script endpoint for everything in the scheduling scripts. It
# can be executed with just `python main.py` due to the above `sys.path` modification, and it
# will then import the `main_cli` functions from all the other files needed to support full
# operation. We define those scripts below, and the sub-scripts as well, and then just iterate
# through `sys.argv` as we make our way down a structure. Once we reach a function, the remaining
# arguments are passed to it. The only caveat of this approach is that `sys.argv[0]` no longer
# represents the program name, so `argparse.ArgumentParser` needs to have `prog` specified.
#
# This is generally a very good solution for personal Python repos with many binaries!

ARGS = {
    "raw": {
        "cal": cal.main_cli,
        "daily_notes": daily_notes.main_cli,
        "dates": dates.main_cli,
        "filter": filter.main_cli,
        "gcal": gcal.main_cli,
        "get": get.main_cli,
        "ical": ical.main_cli,
        "next_actions": next_actions.main_cli,
        "tickle": tickle.main_cli,
        "upcoming": upcoming.main_cli,
        "urgent": urgent.main_cli,
        "waiting": waiting.main_cli,

        "dashboards": {
            "actions": d_actions.main_cli,
        }
    },
    "cal": c_cal.main_cli,
    "actions": c_actions.main_cli,
}

if __name__ == "__main__":
    argspace = ARGS
    sys.argv.pop(0)
    while isinstance(argspace, dict):
        if not sys.argv:
            raise Exception("No command provided")

        arg = sys.argv.pop(0)
        if arg in argspace:
            argspace = argspace[arg]

    argspace(sys.argv)
