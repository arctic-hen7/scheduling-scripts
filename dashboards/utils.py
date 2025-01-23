from rich.text import Text
from rich.markdown import TextElement
from datetime import datetime

def format_date(date_str, time_str, current_date, connective="on"):
    """
    Formats the given date for human readability, relative to the given date, applying the
    given connective when it needs to give a specific weekday (e.g. on Wednesday, for Thursday).
    This connective should be chosen based on whatever comes before.
    """

    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    days_difference = (date - current_date).days
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if days_difference == 0:
        day_str = "today"
    elif days_difference == 1:
        day_str = "tomorrow"
    elif days_difference == -1:
        day_str = "yesterday"
    elif 2 <= days_difference < 7:
        day_str = f"{connective} {weekdays[date.weekday()]}"
    elif -7 < days_difference < 0:
        day_str = f"last {weekdays[date.weekday()]}"
    elif 0 < days_difference < 14:
        day_str = f"next {weekdays[date.weekday()]}"
    else:
        day_str = f"{connective} {weekdays[date.weekday()]} {date.strftime('%d/%m/%Y')}"

    if time_str:
        day_str += f" at {time_str}"

    return day_str

class LeftJustifiedHeading(TextElement):
    """
    A markdown heading, with styling designed for being embedded, rather than sticking out in the
    centre of the terminal.
    """

    @classmethod
    def create(cls, markdown, node) -> "LeftJustifiedHeading":
        heading = cls(node.level)
        return heading

    def on_enter(self, context):
        self.text = Text()
        context.enter_style(self.style_name)

    def __init__(self, level: int):
        self.level = level
        super().__init__()

    def __rich_console__(
        self, console, options
    ):
        text = self.text
        text.justify = "left"
        yield Text(f"{' ' * (self.level - 1)}→ {text}")
