from datetime import datetime, timedelta

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
                item["priority"], # Lower is better
                item["title"]
            )
    )
    return actions
