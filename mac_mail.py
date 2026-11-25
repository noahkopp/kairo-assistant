"""Read and act on email in the Mac Mail app (for the school Outlook account) via mac_mail.js.

The first time, macOS asks whether Terminal may control Mail: click OK.
If the school account isn't in Mail: System Settings -> Internet Accounts -> (school account)
-> turn on Mail.
"""
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "mac_mail.js"


def _run(action, **args):
    r = subprocess.run(["osascript", "-l", "JavaScript", str(SCRIPT), action, json.dumps(args)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        msg = (r.stderr or "").strip().split("Error:")[-1].strip() or "Mail didn't respond"
        if "-1743" in (r.stderr or "") or "not allowed" in (r.stderr or "").lower():
            msg = ("Terminal isn't allowed to control Mail. Turn it on in System Settings -> Privacy & "
                   "Security -> Automation -> Terminal -> Mail.")
        raise RuntimeError(msg)
    return json.loads(r.stdout or "null")


def mail_accounts():
    return _run("accounts")


def list_mail(account="", unread_only=False, max_results=10):
    return _run("list", account=account, unread_only=bool(unread_only), max_results=int(max_results))


def read_mail(email_id):
    return _run("read", email_id=str(email_id))


def mark_mail_read(email_ids=None, account="", all_unread=False):
    return _run("mark_read", email_ids=[str(i) for i in (email_ids or [])] or None,
                account=account, all_unread=bool(all_unread))


def mark_mail_unread(email_ids):
    return _run("mark_unread", email_ids=[str(i) for i in email_ids])


def mail_draft(to, subject, body, account=""):
    return _run("draft", to=to, subject=subject, body=body, account=account)


def mail_send(to, subject, body, account=""):
    return _run("send", to=to, subject=subject, body=body, account=account)
