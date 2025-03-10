def sort_actions(actions):
    actions.sort(
        key=lambda item:
            (
                item["scheduled"]["date"] if item["scheduled"] else item["deadline"]["date"] if item["deadline"] else "9999",
                item["scheduled"]["time"] if item["scheduled"] else item["deadline"]["time"] if item["deadline"] else "9999",
                item["deadline"]["date"] if item["deadline"] else "9999",
                item["deadline"]["time"] if item["deadline"] else "9999",
                item["title"]
            )
    )
    return actions
