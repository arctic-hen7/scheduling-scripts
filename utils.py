from datetime import datetime

STARLING_API="http://localhost:3000/"

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
        task = action_items[task_id]
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
