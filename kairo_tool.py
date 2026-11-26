"""Kairo's email and calendar tools as one command, so Copilot can run them on any system.

  ./kt list_emails query="is:unread newer_than:1d" max_results=10
  ./kt read_email email_id=18c2f...
  ./kt mark_read email_ids=ID1,ID2
(JSON also works: ./kt list_emails '{"query": "is:unread"}'.) Prints the result as JSON.
"""
import json
import platform
import sys

MAC = platform.system() == "Darwin"


def g():
    import google_tools
    return google_tools


def mac(module):
    if not MAC:
        raise RuntimeError("This works only on a Mac (it uses the Mac Calendar/Mail apps). "
                           "Use the Gmail and Google Calendar tools instead.")
    return __import__(module)


TOOLS = {
    # Gmail + Google Calendar (every system)
    "list_emails": lambda query="in:inbox", max_results=10: g().list_emails(query, max_results),
    "read_email": lambda email_id: g().read_email(email_id),
    "create_draft": lambda to, subject, body, reply_to_id="": g().create_draft(to, subject, body, reply_to_id or None),
    "send_email": lambda to, subject, body, reply_to_id="": g().send_email(to, subject, body, reply_to_id or None),
    "archive_email": lambda email_id: g().archive_email(email_id),
    "mark_read": lambda email_ids=None, query=None, limit=500: g().mark_read(email_ids, query, limit),
    "mark_unread": lambda email_ids=None, query=None, limit=500: g().mark_unread(email_ids, query, limit),
    "count_emails": lambda query: g().count_emails(query),
    "list_google_events": lambda days_ahead=7: g().list_events(days_ahead),
    "create_google_event": lambda summary, start, end, description="", location="":
        g().create_event(summary, start, end, description, location),
    # Computer controls: every system
    "open_app": lambda name: __import__("computer").open_app(name),
    "quit_app": lambda name: __import__("computer").quit_app(name),
    "open_url": lambda url: __import__("computer").open_url(url),
    "search_web": lambda query: __import__("computer").search_web(query),
    "open_file": lambda path: __import__("computer").open_file(path),
    "set_volume": lambda percent=None, mute=None: __import__("computer").set_volume(
        None if percent is None else int(percent),
        None if mute is None else str(mute).lower() in ("1", "true", "yes")),
    # Full computer control (opt-in): see the screen, click, type
    "screenshot": lambda: __import__("computer").screenshot(),
    "click": lambda x, y, button="left", clicks=1: __import__("computer").click(x, y, button, clicks),
    "type_text": lambda text: __import__("computer").type_text(text),
    "press": lambda keys: __import__("computer").press(keys),
    "scroll": lambda direction="down", amount=5: __import__("computer").scroll(direction, amount),
    # Your files folder (syllabi, schedules, notes): every system
    "list_files": lambda folder="": __import__("kairo_files").list_files(folder),
    "read_file": lambda name, search="": __import__("kairo_files").read_file(name, search),
    # Mac only: everything in the Calendar and Mail apps (Outlook, iCloud, school/work)
    "list_mac_events": lambda days_ahead=7: mac("mac_calendar").list_mac_events(days_ahead),
    "list_calendars": lambda: mac("mac_calendar").list_calendars(),
    "create_mac_event": lambda title, start, end, calendar="", location="", notes="":
        mac("mac_calendar").create_mac_event(title, start, end, calendar, location, notes),
    "mail_accounts": lambda: mac("mac_mail").mail_accounts(),
    "list_mail": lambda account="", unread_only=False, max_results=10:
        mac("mac_mail").list_mail(account, unread_only, max_results),
    "read_mail": lambda email_id: mac("mac_mail").read_mail(email_id),
    "mark_mail_read": lambda email_ids=None, account="", all_unread=False:
        mac("mac_mail").mark_mail_read(email_ids, account, all_unread),
    "mark_mail_unread": lambda email_ids: mac("mac_mail").mark_mail_unread(email_ids),
    "mail_draft": lambda to, subject, body, account="": mac("mac_mail").mail_draft(to, subject, body, account),
    "mail_send": lambda to, subject, body, account="": mac("mac_mail").mail_send(to, subject, body, account),
}
LISTS = {"email_ids"}
INTS = {"max_results", "days_ahead", "limit", "x", "y", "clicks", "amount"}
BOOLS = {"unread_only", "all_unread"}


def parse_args(argv):
    """key=value pairs (or one JSON object) -> dict of arguments."""
    if len(argv) == 1 and argv[0].lstrip().startswith("{"):
        return json.loads(argv[0])
    args = {}
    for item in argv:
        if "=" not in item:
            raise ValueError(f"Expected name=value, got: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if key in LISTS:
            args[key] = [v.strip() for v in value.split(",") if v.strip()]
        elif key in INTS:
            args[key] = int(value)
        elif key in BOOLS:
            args[key] = value.strip().lower() in ("1", "true", "yes", "y")
        else:
            args[key] = value.replace("\\n", "\n")
    return args


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
        print("Usage: kt TOOL name=value ...  Tools: " + ", ".join(TOOLS))
        sys.exit(1)
    try:
        result = TOOLS[sys.argv[1]](**parse_args(sys.argv[2:]))
        print(json.dumps(result, default=str, indent=1)[:20000])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
