import hashlib
from db.schema import EventModel


def make_fingerprint(event: EventModel) -> str:
    parts = [
        _normalize(event.title),
        event.city,
        event.venue,
        event.start_date,
    ]
    raw = "|".join(p for p in parts if p)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def deduplicate(events: list[EventModel]) -> list[EventModel]:
    seen: dict[str, EventModel] = {}
    for e in events:
        fp = e.fingerprint or make_fingerprint(e)
        if fp in seen:
            existing = seen[fp]
            if e.confidence > existing.confidence:
                seen[fp] = e
        else:
            e.fingerprint = fp
            seen[fp] = e
    return list(seen.values())


def _normalize(s: str) -> str:
    return s.strip().lower().replace(" ", "").replace("　", "")
