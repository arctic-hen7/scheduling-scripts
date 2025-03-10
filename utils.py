from datetime import datetime
import json
import sys

STARLING_API="http://localhost:3000/"
DEFAULT_PRIORITY = 10

def parse_range_str(range_str):
    """
    Parses a date range string of the form `start:end` into two `datetime` objects. This supports
    absent range starts, and single dates, which will return the same date for both.
    """

    if ":" in range_str:
        range_start, range_end = range_str.split(":")
    else:
        range_start = range_str
        range_end = range_start

    # It's possible to provide a range like `:X` to get only data from before that date
    range_start = datetime.strptime(range_start, "%Y-%m-%d") if range_start else None
    range_end = datetime.strptime(range_end, "%Y-%m-%d")
    # Make the range end be at the *very* end of the day
    range_end = range_end.replace(hour=23, minute=59, second=59)

    return range_start, range_end

def load_json():
    """
    Loads JSON data from stdin to allow us to filter another script's output.
    """

    return json.loads(sys.stdin.read())

def dump_json(data):
    """
    Dumps the given JSON data to stdout so it caan be ingested by another script.
    """

    json.dump(data, sys.stdout, ensure_ascii=False)

def create_datetime(date_str, time_str=None):
    """
    Creates Python datetimes from Orgish time and date strings.
    """

    if time_str:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    return datetime.strptime(date_str, "%Y-%m-%d")

def timestamp_to_datetime(timestamp):
    """
    Converts the given Orgish timestamp into a Python datetime.
    """
    ts_start = create_datetime(timestamp["start"]["date"], timestamp["start"]["time"])
    ts_end = create_datetime(timestamp["end"]["date"], timestamp["end"]["time"]) if timestamp["end"] else None
    return ts_start, ts_end

def body_for_proj(proj_item, action_items):
    """
    Forms the body for a project by finding all its tasks and formatting them together for
    at-a-glance reference in a calendar view.
    """

    body = proj_item["body"] + "\n\n" if proj_item["body"] else ""
    task_parts = []
    for task_id, _ in proj_item["children"]:
        task = action_items.get(task_id)

        if task:
            task_part = f"# TODO {task['title'][-1]}"
            if task["body"] and task["body"] != "":
                task_part += f"\n{task['body']}"
            task_parts.append(task_part)
    body += "\n\n".join(task_parts)

    return body

def associated_people(item):
    """
    Returns a list of names and IDs of people associated with the given item.
    """

    people = []
    if item["metadata"]["properties"].get("PEOPLE"):
        people_links = item["metadata"]["properties"]["PEOPLE"].split(", ")
        for person_link in people_links:
            # Link formatting guaranteed
            name, id = person_link[1:-1].removeprefix("(Person) ").split("](")
            people.append([name, id])

    return people

def validate_focus(focus_str, id):
    """
    Validates the given value of the `FOCUS` property for a task and returns a numeric version.
    """

    valid_focuses = [
        "min", # Zero brainpower, could be automated if I had the time
        "low", # Requires me to think very little (e.g. composing an email)
        "med", # Requires actual cogent thought (e.g. completing a problem set)
        "high", # Requires a high degree of advanced conceptual engagement (e.g. novel programming)
    ]
    if focus_str is None:
        raise ValueError(f"No focus level specified for node '{id}'")

    try:
        # The focus value we'll return needs to be comparable, so we'll use the index
        return valid_focuses.index(focus_str.lower())
    except ValueError:
        raise ValueError(f"Invalid focus value on node '{id}': {focus_str}")

def validate_time(time_str, id):
    """
    Validates the time string on the given node and returns a numeric version.
    """

    if time_str is None:
        raise ValueError(f"No time specified for node '{id}'")

    # Split the input string on spaces
    parts = time_str.split()

    total_minutes = 0
    for part in parts:
        if part.endswith('hr'):
            try:
                hours = int(part[:-2])
                total_minutes += hours * 60
            except ValueError:
                raise ValueError(f"Invalid value for time in node '{id}': {part}")
        elif part.endswith('m'):
            try:
                minutes = int(part[:-1])
                total_minutes += minutes
            except ValueError:
                raise ValueError(f"Invalid value for time in node '{id}': {part}")
        else:
            raise ValueError(f"Unknown time format in node '{id}': {part}")

    return total_minutes

def find_task_timestamp(item, next_actions):
    """
    Finds a timestamp for the given task if it or its parent has one. If there are multiple, this
    will just return the first one (from the task first, and then from the parent project).
    """

    # Sometimes this will be used on non-timestampable items, like waiting-for items, in which
    # case we can't find anything
    if "timestamp" not in item:
        return None

    # The next actions filter removed all inactive timestamps
    if item["timestamp"]:
        return item["timestamp"]
    else:
        parent = next_actions.get(item["parent_id"])
        if parent and parent["timestamp"]:
            return parent["timestamp"]
        else:
            return None

def validate_planning_ts(ts, item_id):
    """
    Validates the given planning timestamp, which must be a single datetime, not one spanning a
    range.
    """

    if not ts:
        return None
    if ts["end"]:
        raise ValueError(f"Planning timestamp on item {item_id} spans a range, which is not allowed")

    return ts["start"]

def should_surface_item(item, items):
    """
    Checks if the given item, or its project parent (if it has one) has a timestamp that would
    mean it doesn't need to be surfaced in the upcoming list. If it does, this will also make
    sure that timestamp makes sense with the item's deadline, if it has one.

    This returns `True` if the item should be surfaced, and `False` if it should not, and it
    will write a warning to stderr if the timestamp would not meet the deadline.
    """

    ts = find_task_timestamp(item, items)
    if ts and item["deadline"]:
        # We have a timestamp and a deadline it needs to come before
        deadline = create_datetime(item["deadline"]["date"], item["deadline"]["time"])
        ts_start, ts_end = timestamp_to_datetime(ts)
        # Deliberate `<` here; if the user starts *at* the deadline, that is pretty dumb
        if ts_start < deadline and (ts_end is None or ts_end <= deadline):
            # It does, the schedule is valid, we don't need to surface it
            return False
        else:
            # Bad schedule, warn the user! (stderr because stdout is for the JSON)
            sys.stderr.write(f"Warning: Scheduled item {item['id']} has a deadline you won't meet under current schedule!\n")
            return False
    elif ts:
        # If there's no deadline date to adhere to, but we have slated this to work on at
        # some stage, it doesn't need to be surfaced
        return False
    else:
        return True

def get_priority(item, items):
    """
    Gets the priority of the given item, inheriting any higher priorities from up the chain.
    """

    # Higher numbers are less important, so infinity is the default least
    active_item = item
    highest_priority = float("inf")
    while True:
        priority = active_item["metadata"]["priority"]
        try:
            priority = int(priority) if priority is not None else float("inf")
        except ValueError:
            raise ValueError(f"Invalid priority value on node '{item['id']}': {priority}")
        if priority < highest_priority:
            highest_priority = priority

        active_item = items.get(active_item["parent_id"])
        if not active_item:
            break

    return highest_priority

