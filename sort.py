from datetime import datetime, timedelta

from utils import DEFAULT_PRIORITY

def sort_actions(actions):
    critical_cutoff = datetime.now() + timedelta(days=1)
    critical_cutoff.replace(hour=23, minute=59, second=59)
    critical_cutoff = datetime.strftime(critical_cutoff, "%Y-%m-%d")

    actions.sort(
        key=lambda item:
            (
                item["deadline"]["date"] if item["deadline"] else "9999",
                item["deadline"]["time"] if item["deadline"] else "9999",
                item["scheduled"]["date"] if item["scheduled"] else "9999",
                item["scheduled"]["time"] if item["scheduled"] else "9999",
                item.get("priority") or DEFAULT_PRIORITY, # Lower is better
                item["title"]
            )
    )
    return actions
