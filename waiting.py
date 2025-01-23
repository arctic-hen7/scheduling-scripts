#!/usr/bin/env python3
# Extract waiting-for items from the given list of action items. These can then be filtered to a
# window of concern with the same upcoming filter used for next actions.

from utils import associated_people, create_datetime, dump_json, load_json, validate_planning_ts

def filter_to_waiting(action_items):
    """
    Filters the given action items down to those which qualify as "waiting-for" items.
    """

    filtered = []
    for item in action_items:
        if "waiting" in item["parent_tags"]:
            scheduled = validate_planning_ts(item["metadata"]["scheduled"], item["id"])
            deadline = validate_planning_ts(item["metadata"]["deadline"], item["id"])

            # Sanity check that the scheduled date is before the deadline date
            scheduled_dt = create_datetime(scheduled["date"], scheduled["time"]) if scheduled else None
            deadline_dt = create_datetime(deadline["date"], deadline["time"]) if deadline else None
            if scheduled_dt and deadline_dt and scheduled_dt > deadline_dt:
                raise ValueError(f"Item {item['id']} has a scheduled date after its deadline date")

            if not "SENT" in item["metadata"]["properties"]:
                raise ValueError(f"Item {item['id']} has no SENT property")

            wait_item = {
                "id": item["id"],
                "title": item["title"],
                "body": item["body"],
                "scheduled": scheduled,
                "deadline": deadline,
                "sent": item["metadata"]["properties"]["SENT"],
                "people": associated_people(item),
            }
            filtered.append(wait_item)

    return filtered

if __name__ == "__main__":
    action_items = load_json()
    dump_json(filter_to_waiting(action_items))
