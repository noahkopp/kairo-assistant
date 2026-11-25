"""Kairo's email and calendar tools as one command, so Copilot can run them.

  ./kt list_emails '{"query": "is:unread newer_than:1d", "max_results": 10}'
  ./kt read_email '{"email_id": "..."}'
Prints the result as JSON.
"""
import json
import sys

import google_tools as g
import mac_calendar as mac
import mac_mail as mm

TOOLS = {
    "list_emails": lambda query="in:inbox", max_results=10: g.list_emails(query, max_results),
    "read_email": lambda email_id: g.read_email(email_id),
    "create_draft": lambda to, subject, body, reply_to_id="": g.create_draft(to, subject, body, reply_to_id or None),
    "send_email": lambda to, subject, body, reply_to_id="": g.send_email(to, subject, body, reply_to_id or None),
    "archive_email": lambda email_id: g.archive_email(email_id),
    "mark_read": lambda email_ids=None, query=None, limit=500: g.mark_read(email_ids, query, limit),
    "mark_unread": lambda email_ids=None, query=None, limit=500: g.mark_unread(email_ids, query, limit),
    "count_emails": lambda query: g.count_emails(query),
    "mail_accounts": lambda: mm.mail_accounts(),
    "list_mail": lambda account="", unread_only=False, max_results=10: mm.list_mail(account, unread_only, max_results),
    "read_mail": lambda email_id: mm.read_mail(email_id),
    "mark_mail_read": lambda email_ids=None, account="", all_unread=False: mm.mark_mail_read(email_ids, account, all_unread),
    "mark_mail_unread": lambda email_ids: mm.mark_mail_unread(email_ids),
    "mail_draft": lambda to, subject, body, account="": mm.mail_draft(to, subject, body, account),
    "mail_send": lambda to, subject, body, account="": mm.mail_send(to, subject, body, account),
    "list_google_events": lambda days_ahead=7: g.list_events(days_ahead),
    "create_google_event": lambda summary, start, end, description="", location="":
        g.create_event(summary, start, end, description, location),
    "list_mac_events": lambda days_ahead=7: mac.list_mac_events(days_ahead),
    "list_calendars": lambda: mac.list_calendars(),
    "create_mac_event": lambda title, start, end, calendar="", location="", notes="":
        mac.create_mac_event(title, start, end, calendar, location, notes),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
        print("Usage: ./kt TOOL '{json args}'. Tools: " + ", ".join(TOOLS))
        sys.exit(1)
    try:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip() else {}
        print(json.dumps(TOOLS[sys.argv[1]](**args), default=str, indent=1)[:20000])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
