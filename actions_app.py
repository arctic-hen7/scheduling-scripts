# Converts the given next actions into a format parseable by the actions app HTML and
# implants them, together with the CSS that template needs, returning a single string
# of self-contained HTML that can be used to show urgent next actions and filter them
# generally by context, people, time, and focus.

import json
from pathlib import Path

from sort import sort_actions
from .utils import DEFAULT_PRIORITY, format_priority, load_json, should_surface_item, format_priority
from .dashboards.utils import format_minutes

def jsify_ts(ts):
    """
    Converts the given datetime to a minimal JSON form.
    """

    if not ts:
        return None
    return [ts["date"], ts["time"]]

def format_actions_for_app(next_actions):
    """
    Formats the given next actions for the actions app.
    """

    next_actions_map = {action["id"]: action for action in next_actions}

    # Filter and sort first to avoid having to duplicate sort logic with weird JS indices
    filtered = []
    for action in next_actions:
        # Skip anything that's been scheduled, any projects, and any non-actionable items. They
        # should all be visible in the desktop systems, because there I can see the full context
        # of where they sit and work out what needs to be done. In the field, I just want to see
        # things I can *do* straight away.
        if not should_surface_item(action, next_actions_map) or action["keyword"] == "PROJ":
            continue

        filtered.append(action)

    next_actions = sort_actions(filtered)

    # There are finite contexts and people to choose from, so record them. Each one's value will
    # be its position were this an array (which it will be when we export).
    contexts = {}
    people = {}
    formatted_actions = []
    for action in next_actions:

        action_contexts = []
        action_people = []

        html = "<pre>"
        # No projects
        if action["keyword"] == "PROB":
            html += f"<strong>→ <i class='probMarker'>Problem:</i> {action['title']}</strong>"
        else:
            html += f"<strong>→ {action['title']}</strong>"
        if action.get("timestamp"):
            html += "\n  <i>Has a timestamp attached.</i>"
        if action["scheduled"]:
            # We don't know what the date will be when this is viewed
            html += "\n  <i>Scheduled <strong class='scheduled'>{{ scheduled }}</strong></i>"
        if action["deadline"]:
            html += "\n  <i>Due <strong class='deadline'>{{ deadline }}</strong></i>"

        if action["priority"] != DEFAULT_PRIORITY:
            html += f"\n  <i>Priority: <strong class='priority'>{format_priority(action['priority'])}</strong></i>"

        context_str = ", ".join(action["context"]) if action["context"] else "none"
        for ctx in action["context"] or []:
            if ctx not in contexts:
                contexts[ctx] = len(contexts)
            action_contexts.append(contexts[ctx])
        html += f"\n  <i>Context: <strong class='context'>{context_str}</strong></i>"

        if action["keyword"] == "TODO":
            focus_str = [ "minimal", "low", "medium", "high" ][action["focus"]]
            time_str = format_minutes(action["time"])
            html += f"\n  <i>Focus: <strong class='focus'>{focus_str}</strong></i>"
            html += f"\n  <i>Time: <strong class='time'>{time_str}</strong></i>"

        if action["people"]:
            html += "\n  <i>People needed:</i>"
            for person_name, _ in action["people"]:
                html += f"\n    <i>- <strong>{person_name}</strong></i>"
                if person_name not in people:
                    people[person_name] = len(people)
                action_people.append(people[person_name])

        # With each item in its own `<pre>`, we don't need to worry about padding
        if action["body"]:
            body = action["body"].replace("\\$", "$")
            html += f"\n\n{body}"

        html += "</pre>"
        # Minimal format to reduce data needs
        formatted_actions.append([html, jsify_ts(action.get("scheduled")), jsify_ts(action.get("deadline")), action_contexts, action_people, action["focus"], action["time"], action["keyword"]])

    # formatted_actions.sort(
    #     key=lambda item:
    #         (
    #             # Use `9999` when we don't have any scheduled/deadline date so more urgent things
    #             # appear first
    #             item[1][0] if item[1] else item[2][0] if item[2] else "9999",
    #             item[1][1] if item[1] else item[2][1] if item[2] else "9999",
    #             item[2][0] if item[2] else "9999",
    #             item[2][1] if item[2] else "9999",
    #             item[0] # This is the HTML, not the title, but the first thing is the title
    #         )
    # )
    return [list(contexts.keys()), list(people.keys()), formatted_actions]

def produce_actions_app(data):
    """
    Produces a self-contained HTML string for the actions app, implanting the given data.
    """

    actions_app_dir = Path(__file__).parent / "actions_app"
    with open(actions_app_dir / "index.html", "r") as f:
        html = f.read()
    with open(actions_app_dir / "index.css", "r") as f:
        css = f.read()
    with open(actions_app_dir / "index.js", "r") as f:
        js = f.read()

    html = html.replace("{{ data }}", json.dumps(data))
    html = html.replace("{{ styles }}", css)
    html = html.replace("{{ scripts }}", js)

    return html

def main_cli(_):
    action_items = load_json()
    data = format_actions_for_app(action_items)
    html = produce_actions_app(data)

    print(html)
