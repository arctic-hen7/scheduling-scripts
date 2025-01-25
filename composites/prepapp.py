# A composite for preparing the actions app and returning an HTML string.

from datetime import datetime
from ..actions_app import format_actions_for_app, produce_actions_app, format_actions_for_app
from ..next_actions import filter_to_next_actions
from ..get import get_normalised_action_items

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Prepares the actions app.", prog="prepapp")
    parser.add_argument("-u", "--until", type=str, help="The cutoff date to expand timestamps until.")

    args = parser.parse_args(args)
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else datetime.now()
    until.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    next_actions = filter_to_next_actions(action_items)
    data = format_actions_for_app(next_actions)
    app_html = produce_actions_app(data)

    print(app_html)
