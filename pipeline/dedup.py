import hashlib
import re
from db.schema import EventModel

TITLE_ALIASES = {
    "cp": "comicup", "cp展": "comicup", "cp2026": "comicup2026",
    "cj": "chinajoy", "bw": "bilibiliworld", "bml": "bilibilimacrolink",
    "ccg": "ccgexpo", "cd": "comiday",
}

TITLE_CLEANUP = re.compile(r"[　\s!！?？。，,、·•「」『』【】()（）\[\]{}:：#＃\-\-~～★☆♥♦♣♠✓✔✗✘]+")


def _normalize_title(title: str) -> str:
    """归一化标题，处理别名和特殊字符。"""
    t = TITLE_CLEANUP.sub("", title.lower().strip())
    for alias, full in TITLE_ALIASES.items():
        t = t.replace(alias, full)
    return t


def make_fingerprint(event: EventModel) -> str:
    parts = [
        _normalize_title(event.title),
        event.city.strip(),
        event.start_date,
    ]
    raw = "|".join(p for p in parts if p)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def deduplicate(events: list[EventModel]) -> list[EventModel]:
    # First pass: fingerprint exact match
    seen: dict[str, EventModel] = {}
    for e in events:
        fp = e.fingerprint or make_fingerprint(e)
        if fp in seen:
            existing = seen[fp]
            if e.confidence > existing.confidence:
                e.fingerprint = fp
                seen[fp] = e
            # Merge missing fields from higher-confidence source
            if e.confidence <= existing.confidence:
                _merge_fields(existing, e)
        else:
            e.fingerprint = fp
            seen[fp] = e

    # Second pass: fuzzy merge by city+date proximity
    result = list(seen.values())
    result.sort(key=lambda x: x.start_date or "")

    merged = []
    for e in result:
        found = False
        for m in merged:
            if _is_same_event(e, m):
                if e.confidence > m.confidence:
                    _merge_fields(e, m)
                else:
                    _merge_fields(m, e)
                found = True
                break
        if not found:
            merged.append(e)

    print(f"Dedup: {len(events)}→{len(seen)}→{len(merged)}", file=__import__("sys").stderr)
    return merged


def _is_same_event(a: EventModel, b: EventModel) -> bool:
    """Same city, titles similar, dates close."""
    if not a.city or not b.city:
        return False
    if a.city != b.city:
        return False
    if not a.title or not b.title:
        return False
    # Title fuzzy match
    ta = _normalize_title(a.title)
    tb = _normalize_title(b.title)
    if ta == tb:
        return True
    if len(ta) >= 4 and len(tb) >= 4 and (ta[:6] == tb[:6] or ta in tb or tb in ta):
        return True
    # Date proximity
    if a.start_date and b.start_date:
        if a.start_date[:7] == b.start_date[:7]:  # same month
            return True
    return False


def _merge_fields(target: EventModel, source: EventModel):
    """用 source 补全 target 的缺失字段。"""
    for field in ["venue", "end_date", "price_range", "ticket_url", "image_url"]:
        src_val = getattr(source, field, None)
        tgt_val = getattr(target, field, None)
        if not tgt_val and src_val:
            setattr(target, field, src_val)
