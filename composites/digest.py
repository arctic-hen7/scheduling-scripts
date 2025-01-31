# Prepares a daily digest file containing everything the user needs to know about the given day.

from datetime import datetime, timedelta

from dashboards.utils import format_minutes

from ..goals import assemble_goals_file
from ..cal import filter_to_calendar
from ..daily_notes import filter_to_daily_notes
from ..next_actions import filter_to_next_actions
from ..upcoming import filter_to_upcoming
from ..urgent import filter_to_urgent
from ..get import get_normalised_action_items

DIGEST_SCRIPT_PROMPT = "You are a helpful assistant in part of a pipeline to deliver a spoken daily digest to a user. You will be given the raw Markdown of a daily digest file containing events, daily notes (i.e. things to remember), goals for the day, week, and general goals that are shown every day, and urgent actions that need to be done during the day. You should provide a script version of this that can be spoken fluently by a text-to-speech engine. Make sure to include all the detail of the daily digest and not change anything, just reformat it so it can be spoken fluently. You should open with a cheerful \"Good morning\" or similar, and close with a positive message to have a great day."

def main_cli(args):
    import argparse
    parser = argparse.ArgumentParser(description="Return a digest for the given day.", prog="digest")
    parser.add_argument("date", type=str, help="The date.")
    parser.add_argument("-a", "--audio", type=str, help="Output the digest as an AI-generated audio file to the given path (requires `$OPENAI_API_KEY`).")

    args = parser.parse_args(args)
    if args.date == "tmrw" or args.date == "tomorrow":
        date = datetime.now() + timedelta(days=1)
    elif not args.date:
        date = datetime.now()
    else:
        date = datetime.strptime(args.date, "%Y-%m-%d")

    date.replace(hour=0, minute=0, second=0)
    until = date.replace(hour=23, minute=59, second=59)

    action_items = get_normalised_action_items(until, ["body"])
    cal_items = filter_to_calendar(action_items, date, until)
    daily_notes = filter_to_daily_notes(action_items, date, until)
    next_actions = filter_to_next_actions(action_items)
    upcoming = filter_to_upcoming(next_actions, until)
    urgent = filter_to_urgent(upcoming, date, until)
    goals_md = assemble_goals_file(date)

    # Format the calendar items in a summary (already in time order)
    cal_md = "## Events\n\n"
    if not cal_items:
        cal_md += "*No events.*"
    for event in cal_items:
        # We know all events start and end on this day, so we can ignore the date
        if event["start"] and event["end"]:
            time_str = f"from **{event['start']['time'].removesuffix(':00')}** to **{event['end']['time'].removesuffix(':00')}**"
        elif event["start"]:
            time_str = f"from **{event['start']['time'].removesuffix(':00')}**"
        elif event["end"]:
            time_str = f"until **{event['end']['time'].removesuffix(':00')}**"
        else:
            time_str = "**all day**"

        if event["location"]:
            loc_str = f" at *{event['location']}*"
        else:
            loc_str = ""

        cal_md += f"- {event['title']} ({time_str}{loc_str})\n"
    cal_md = cal_md.strip()

    # We'll just sumamrise the daily notes with their titles
    daily_notes_md = "## Daily Notes\n\n"
    if not daily_notes:
        daily_notes_md += "*No daily notes.*"
    for note in daily_notes:
        daily_notes_md += f"- {note['title']}\n"
    daily_notes_md = daily_notes_md.strip()

    # Urgent actions
    urgent_md = "## Urgent Actions\n\n"
    if not urgent:
        urgent_md += "*No urgent actions.*"
    for action in urgent:
        if action["keyword"] == "PROJ":
            proj_str = "(Project) "
            details_str = ""
        else:
            proj_str = ""
            details_str = f" ({[ 'minimal', 'low', 'medium', 'high' ][action['focus']]} focus; {format_minutes(action['time'])}; context: {', '.join(action['context']) if action['context'] else 'none'})"
        urgent_md += f"- {proj_str}{action['title']}{details_str}\n"

    # Format the goals for fitting into the broader file
    goals_md = "## Goals\n\n" + goals_md.replace("# ", "### ")

    digest = f"# Daily Digest for {date.strftime('%A, %B %d, %Y')}\n\n{cal_md}\n\n{daily_notes_md}\n\n{goals_md}\n\n{urgent_md}"

    if args.audio:
        from openai import OpenAI
        client = OpenAI()

        print("Converting digest to script...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": DIGEST_SCRIPT_PROMPT},
                {
                    "role": "user",
                    "content": digest
                }
            ],
            temperature=0.3
        )
        print("Generating digest audio...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=completion.choices[0].message.content,
        )
        response.stream_to_file(args.audio)
    else:
        print(digest)
