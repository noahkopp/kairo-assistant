"""Gmail + Google Calendar helpers for Kairo.

Every public function here returns plain Python data (dicts/lists) so it can be
sent back to Claude as JSON.
"""
import base64
import html
import re
import threading
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# gmail.modify = read, draft, send, archive (but NOT permanently delete)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

HERE = Path(__file__).parent
CREDENTIALS_FILE = HERE / "credentials.json"   # downloaded from Google Cloud
TOKEN_FILE = HERE / "token.json"               # created after you sign in once
MAX_BODY_CHARS = 8000                          # keeps long emails from eating tokens

# Google's client objects aren't thread-safe, so each thread gets its own copy.
_local = threading.local()
_creds_lock = threading.Lock()


# ---------------------------------------------------------------- sign-in ---
def _get_creds():
    with _creds_lock:
        return _load_or_sign_in()


def _load_or_sign_in():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None  # token was revoked or expired (common in Testing mode)

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            _find_downloaded_credentials()
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Gmail isn't set up yet. To connect it, run: ./kairo.command --google"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0, authorization_prompt_message="")  # opens the browser to sign in

    TOKEN_FILE.write_text(creds.to_json())
    return creds


def _find_downloaded_credentials():
    """Google names the download client_secret_....json; grab the newest from Downloads."""
    import shutil
    found = sorted((Path.home() / "Downloads").glob("client_secret_*.json"),
                   key=lambda f: f.stat().st_mtime, reverse=True)
    if found:
        shutil.copy(found[0], CREDENTIALS_FILE)
        import sys
        print(f"Using Google credentials from {found[0].name}", file=sys.stderr)


def gmail():
    if not hasattr(_local, "gmail"):
        _local.gmail = build("gmail", "v1", credentials=_get_creds(), cache_discovery=False)
    return _local.gmail


def calendar():
    if not hasattr(_local, "calendar"):
        _local.calendar = build("calendar", "v3", credentials=_get_creds(), cache_discovery=False)
    return _local.calendar


def warm_up():
    """Trigger the Google sign-in at startup instead of mid-conversation."""
    gmail()
    calendar()


# ---------------------------------------------------------------- helpers ---
def _headers(msg):
    return {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}


def _decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


def _extract_body(payload):
    plain, htmls = [], []

    def walk(part):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            if mime == "text/plain":
                plain.append(_decode(data))
            elif mime == "text/html":
                htmls.append(_decode(data))
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    if plain:
        return "\n".join(plain).strip()
    if htmls:
        return _html_to_text("\n".join(htmls))
    return "(no readable text in this email)"


def _build_message(to, subject, body, reply_to_id=None):
    """Build the Gmail API payload. If reply_to_id is given, it threads as a reply."""
    msg = EmailMessage()
    msg.set_content(body)
    msg["To"] = to
    thread_id = None

    if reply_to_id:
        orig = gmail().users().messages().get(
            userId="me", id=reply_to_id, format="metadata",
            metadataHeaders=["Message-ID", "Subject", "References"],
        ).execute(num_retries=2)
        h = _headers(orig)
        thread_id = orig["threadId"]
        if h.get("message-id"):
            msg["In-Reply-To"] = h["message-id"]
            msg["References"] = (h.get("references", "") + " " + h["message-id"]).strip()
        if not subject:
            s = h.get("subject", "")
            subject = s if s.lower().startswith("re:") else f"Re: {s}"

    msg["Subject"] = subject or "(no subject)"
    payload = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    if thread_id:
        payload["threadId"] = thread_id
    return payload


def email_label(email_id):
    """Short 'from X about Y' description, used in approval prompts."""
    try:
        msg = gmail().users().messages().get(
            userId="me", id=email_id, format="metadata", metadataHeaders=["From", "Subject"]
        ).execute(num_retries=2)
        h = _headers(msg)
        sender = re.sub(r"\s*<.*?>", "", h.get("from", "someone")).strip('" ')
        return f"the email from {sender} about '{h.get('subject', 'no subject')}'"
    except Exception:
        return f"email {email_id}"


# ------------------------------------------------------------------ Gmail ---
def list_emails(query="in:inbox", max_results=10):
    max_results = max(1, min(int(max_results), 25))
    svc = gmail()
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute(num_retries=2)
    ids = [m["id"] for m in resp.get("messages", [])]
    if not ids:
        return []

    found = {}

    def collect(request_id, msg, exception):
        if exception is None and msg:
            found[msg["id"]] = msg

    # One round trip for all emails instead of one per email.
    batch = svc.new_batch_http_request(callback=collect)
    for mid in ids:
        batch.add(svc.users().messages().get(
            userId="me", id=mid, format="metadata", metadataHeaders=["From", "Subject", "Date"]))
    batch.execute()

    out = []
    for mid in ids:
        msg = found.get(mid)
        if not msg:
            continue
        h = _headers(msg)
        out.append({
            "id": msg["id"],
            "from": h.get("from", ""),
            "subject": h.get("subject", ""),
            "date": h.get("date", ""),
            "snippet": html.unescape(msg.get("snippet", "")),
            "unread": "UNREAD" in msg.get("labelIds", []),
        })
    return out


def read_email(email_id):
    msg = gmail().users().messages().get(userId="me", id=email_id, format="full").execute(num_retries=2)
    h = _headers(msg)
    body = _extract_body(msg["payload"])
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "\n...(truncated)"
    return {
        "id": msg["id"],
        "from": h.get("from", ""),
        "to": h.get("to", ""),
        "subject": h.get("subject", ""),
        "date": h.get("date", ""),
        "body": body,
    }


def create_draft(to, subject, body, reply_to_id=None):
    draft = gmail().users().drafts().create(
        userId="me", body={"message": _build_message(to, subject, body, reply_to_id)}
    ).execute(num_retries=2)
    return {"draft_created": True, "draft_id": draft["id"]}


def send_email(to, subject, body, reply_to_id=None):
    sent = gmail().users().messages().send(
        userId="me", body=_build_message(to, subject, body, reply_to_id)
    ).execute(num_retries=2)
    return {"sent": True, "id": sent["id"]}


def archive_email(email_id):
    gmail().users().messages().modify(
        userId="me", id=email_id, body={"removeLabelIds": ["INBOX"]}
    ).execute(num_retries=2)
    return {"archived": True}


def _ids_for(query, limit=500):
    ids, token = [], None
    while len(ids) < limit:
        resp = gmail().users().messages().list(userId="me", q=query, maxResults=min(500, limit - len(ids)),
                                               pageToken=token).execute(num_retries=2)
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids


def _relabel(email_ids=None, query=None, add=(), remove=(), limit=500):
    ids = list(email_ids or []) or (_ids_for(query, limit) if query else [])
    for i in range(0, len(ids), 1000):
        gmail().users().messages().batchModify(userId="me", body={
            "ids": ids[i:i + 1000], "addLabelIds": list(add), "removeLabelIds": list(remove)}).execute(num_retries=2)
    return {"changed": len(ids)}


def mark_read(email_ids=None, query=None, limit=500):
    """Mark emails read, by id list or by Gmail search (e.g. 'is:unread category:promotions')."""
    return _relabel(email_ids, query, remove=["UNREAD"], limit=limit)


def mark_unread(email_ids=None, query=None, limit=500):
    return _relabel(email_ids, query, add=["UNREAD"], limit=limit)


def count_emails(query):
    return {"count": len(_ids_for(query, 2000)), "note": "capped at 2000"}


# --------------------------------------------------------------- Calendar ---
def list_events(days_ahead=7):
    start = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=max(1, min(int(days_ahead), 60)))
    resp = calendar().events().list(
        calendarId="primary", timeMin=start.isoformat(), timeMax=end.isoformat(),
        singleEvents=True, orderBy="startTime", maxResults=50,
    ).execute(num_retries=2)
    return [{
        "summary": e.get("summary", "(no title)"),
        "start": e["start"].get("dateTime", e["start"].get("date")),
        "end": e["end"].get("dateTime", e["end"].get("date")),
        "location": e.get("location", ""),
    } for e in resp.get("items", [])]


def _when(value):
    value = value.strip()
    if len(value) == 10:                      # "2026-11-25" -> all-day event
        return {"date": value}
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:                     # no offset given -> assume local time
        dt = dt.astimezone()
    return {"dateTime": dt.isoformat()}


def create_event(summary, start, end, description="", location=""):
    start_w, end_w = _when(start), _when(end)
    if "date" in start_w and "date" in end_w and end_w["date"] <= start_w["date"]:
        # Google treats an all-day event's end date as exclusive, so it must be the next day
        next_day = datetime.fromisoformat(start_w["date"]) + timedelta(days=1)
        end_w = {"date": next_day.date().isoformat()}
    event = calendar().events().insert(calendarId="primary", body={
        "summary": summary,
        "start": start_w,
        "end": end_w,
        "description": description,
        "location": location,
    }).execute(num_retries=2)
    return {"created": True, "link": event.get("htmlLink", "")}
