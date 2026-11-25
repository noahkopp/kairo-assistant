"""Read and add events through the Mac's own Calendar app (Apple EventKit).

Every calendar synced to this Mac shows up here: iCloud/Apple Calendar, your
school Outlook/Exchange calendar, and Google if you've added it too. To add an
account: System Settings -> Internet Accounts.

The first time this runs, macOS asks whether Terminal may access your calendars.
Click Allow (choose "Full Access" if asked).
"""
import threading
from datetime import datetime, timedelta

_store = None
_ek = None


def _get_store():
    global _store, _ek
    if _store is not None:
        return _store
    try:
        import EventKit
        import Foundation  # noqa: F401  (loads NSDate)
    except ImportError:
        raise RuntimeError("Mac calendar support isn't installed. Run ./kairo.command again.")
    _ek = EventKit
    store = EventKit.EKEventStore.alloc().init()

    done = threading.Event()
    result = {"granted": False}

    def handler(granted, error):
        result["granted"] = bool(granted)
        done.set()

    if hasattr(store, "requestFullAccessToEventsWithCompletion_"):      # macOS 14+
        store.requestFullAccessToEventsWithCompletion_(handler)
    else:
        store.requestAccessToEntityType_completion_(EventKit.EKEntityTypeEvent, handler)
    done.wait(60)
    if not result["granted"]:
        raise RuntimeError("Calendar access was not allowed. Turn it on in System Settings -> "
                           "Privacy & Security -> Calendars -> Terminal, then start Kairo again.")
    _store = store
    return store


def _to_py(nsdate):
    return datetime.fromtimestamp(nsdate.timeIntervalSince1970()).astimezone()


def _to_ns(dt):
    from Foundation import NSDate
    return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())


def _parse(value):
    value = value.strip()
    if len(value) == 10:
        return datetime.fromisoformat(value).astimezone(), True
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.astimezone()), False


def list_calendars():
    store = _get_store()
    cals = store.calendarsForEntityType_(_ek.EKEntityTypeEvent)
    return [{"name": c.title(), "account": c.source().title(),
             "can_add_events": bool(c.allowsContentModifications())} for c in cals]


def list_mac_events(days_ahead=7):
    store = _get_store()
    start = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=max(1, min(int(days_ahead), 60)))
    pred = store.predicateForEventsWithStartDate_endDate_calendars_(_to_ns(start), _to_ns(end), None)
    events = sorted(store.eventsMatchingPredicate_(pred) or [], key=lambda e: e.startDate().timeIntervalSince1970())
    out = []
    for e in events[:100]:
        out.append({
            "title": e.title() or "(no title)",
            "start": _to_py(e.startDate()).isoformat(),
            "end": _to_py(e.endDate()).isoformat(),
            "all_day": bool(e.isAllDay()),
            "calendar": e.calendar().title(),
            "account": e.calendar().source().title(),
            "location": e.location() or "",
        })
    return out


def create_mac_event(title, start, end, calendar="", location="", notes=""):
    store = _get_store()
    start_dt, all_day = _parse(start)
    end_dt, _ = _parse(end)
    if all_day and end_dt <= start_dt:
        end_dt = start_dt + timedelta(days=1)

    target = None
    if calendar:
        for c in store.calendarsForEntityType_(_ek.EKEntityTypeEvent):
            if calendar.lower() in c.title().lower() and c.allowsContentModifications():
                target = c
                break
        if target is None:
            names = [c["name"] for c in list_calendars() if c["can_add_events"]]
            raise ValueError(f"No writable calendar named '{calendar}'. Options: {names}")
    else:
        target = store.defaultCalendarForNewEvents()

    ev = _ek.EKEvent.eventWithEventStore_(store)
    ev.setTitle_(title)
    ev.setStartDate_(_to_ns(start_dt))
    ev.setEndDate_(_to_ns(end_dt))
    ev.setAllDay_(all_day)
    if location:
        ev.setLocation_(location)
    if notes:
        ev.setNotes_(notes)
    ev.setCalendar_(target)
    ok, err = store.saveEvent_span_error_(ev, _ek.EKSpanThisEvent, None)
    if not ok:
        raise RuntimeError(f"Calendar app refused the event: {err}")
    return {"created": True, "calendar": target.title()}
