# Script that filters next actions from `next_actions.py` down to those that match a specified
# list of available contexts, a maximum focus level, and/or a maximum amount of available time.

from datetime import datetime
from .utils import dump_json, load_json, validate_time, validate_focus, should_surface_item
from .sort import sort_actions

def filter_next_actions(next_actions, until, contexts, people, max_time, max_focus, ty):
    # TODO: sorting by relevance, somehow...
    """
    Filters the given next actions by context, time required, focus required, and people needed.
    This is very different from `filter_to_next_actions`, which turns action items into next
    actions, which can *then* be filtered with this function!

    The given list of contexts will be taken as the list of contexts which are available, so
    tasks which have contexts not in this list will be filtered out, as well as tasks which have
    none of those contexts (when the list is non-empty, this will be items without a context,
    which are typically person-associated).

    The given list of people will be taken as the list of people available, and will be treated
    identically to the list of contexts.

    The given maximum time should be a number of minutes, and tasks requiring longer than this will
    be filtered out.

    The given maximum focus should be a number from 0-3, and tasks requiring more focus than this
    will be filtered out.
    """

    # We want quick indexing on these
    contexts = set(contexts)
    people = set(people)
    next_actions_map = {item["id"]: item for item in next_actions}

    filtered = []
    for item in next_actions:
        # Skip anything that's been scheduled, any projects, and any non-actionable items. They
        # should all be visible in the desktop systems, because there I can see the full context
        # of where they sit and work out what needs to be done. In the field, I just want to see
        # things I can *do* straight away.
        if not should_surface_item(item, next_actions_map):
            continue
        # Skip all projects, they're not next actions and are only needed in the upcoming/urgent
        # sections
        if item["keyword"] == "PROJ": continue
        # Skip anything scheduled after the current date (shouldn't be started yet)
        if item["scheduled"] and datetime.strptime(item["scheduled"]["date"], "%Y-%m-%d") > until: continue

        if ty == "tasks" and item["keyword"] != "TODO": continue
        if ty == "problems" and item["keyword"] != "PROB": continue

        # If we're filtering by context, this item's list of contexts is an AND list, so make sure
        # all of them are available in `contexts`, and exclude items that don't have any
        # of those contexts
        if contexts:
            we_have_all = True
            item_has_one = False
            for ctx in item["context"]:
                if ctx not in contexts:
                    we_have_all = False
                    break
                else:
                    item_has_one = True

            if not we_have_all or not item_has_one: continue
        if people:
            we_have_all = True
            item_has_one = False
            for person, _ in item["people"]:
                if person not in people:
                    we_have_all = False
                    break
                else:
                    item_has_one = True

            if not we_have_all or not item_has_one: continue
        # For time and focus, we have a maximum, allow anything up to that. We fall back to
        # infinity for problems, which shouldn't show up in these searches
        if max_time is not None:
            if (item["time"] or float("inf")) > max_time: continue
        if max_focus is not None:
            if (item["focus"] or float("inf")) > max_focus: continue

        filtered.append(item)

    return sort_actions(filtered)

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter next actions.", prog = "filter")
    parser.add_argument("-u", "--until", type=str, required=True, help="The date to show scheduled actions until.")
    parser.add_argument("-c", "--context", action="append", dest="contexts", help="Contexts to filter by (list of ORs).")
    parser.add_argument("-p", "--people", action="append", dest="people", help="People to filter by (list of ORs).")
    parser.add_argument("-f", "--focus", type=str, help="Maximum focus to filter by.")
    parser.add_argument("-t", "--time", type=str, help="Maximum time to filter by.")
    ty_group = parser.add_mutually_exclusive_group()
    ty_group.add_argument("--problems", action="store_true", help="Only show problems.")
    ty_group.add_argument("--tasks", action="store_true", help="Only show tasks.")

    args = parser.parse_args(args)
    until = datetime.strptime(args.until, "%Y-%m-%d")
    time = validate_time(args.time, "INPUT") if args.time else None
    focus = validate_focus(args.focus, "INPUT") if args.focus else None
    ty = "problems" if args.problems else "tasks" if args.tasks else "all"

    next_actions = load_json()
    dump_json(filter_next_actions(next_actions, until, args.contexts or [], args.people or [], time, focus, ty))
