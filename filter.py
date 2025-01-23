# Script that filters next actions from `next_actions.py` down to those that match a specified
# list of available contexts, a maximum focus level, and/or a maximum amount of available time.

from .utils import dump_json, load_json, validate_time, validate_focus

def filter_next_actions(next_actions, contexts, people, max_time, max_focus):
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

    filtered = []
    for item in next_actions:
        # Skip all projects, they're not next actions and are only needed in the upcoming/urgent
        # sections
        if not item["time"]: continue

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
        # For time and focus, we have a maximum, allow anything up to that
        if max_time is not None:
            if item["time"] > max_time: continue
        if max_focus is not None:
            if item["focus"] > max_focus: continue

        filtered.append(item)

    # Sort by title
    filtered.sort(key=lambda item: item["title"])

    return filtered

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Filter next actions.", prog = "filter")
    parser.add_argument("-c", "--context", action="append", dest="contexts", help="Contexts to filter by (list of ORs).")
    parser.add_argument("-p", "--people", action="append", dest="people", help="People to filter by (list of ORs).")
    parser.add_argument("-f", "--focus", type=str, help="Maximum focus to filter by.")
    parser.add_argument("-t", "--time", type=str, help="Maximum time to filter by.")

    args = parser.parse_args(args)
    time = validate_time(args.time, "INPUT") if args.time else None
    focus = validate_focus(args.focus, "INPUT") if args.focus else None

    next_actions = load_json()
    dump_json(filter_next_actions(next_actions, args.contexts or [], args.people or [], time, focus))
