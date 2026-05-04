from datetime import datetime, timedelta
from db.schema import EventModel

NORMALIZERS: dict[str, callable] = {}
CATEGORY_ALIASES = {
    "漫展": "漫展", "同人展": "同人展", "演唱会": "演唱会",
    "舞台剧": "舞台剧", "音乐会": "音乐会", "展览": "展览",
    "二次元": "漫展", "cosplay": "漫展", "动漫": "漫展",
}


def register(platform: str):
    return lambda fn: NORMALIZERS.update({platform: fn}) or fn


def normalize(platform: str, raw_events: list[dict]) -> list[EventModel]:
    fn = NORMALIZERS.get(platform)
    if not fn:
        return []
    return [e for raw in raw_events if (e := _try_normalize(fn, raw)) is not None]


def _try_normalize(fn, raw: dict) -> EventModel | None:
    try:
        return fn(raw)
    except Exception:
        return None


@register("bilibili")
def _(raw: dict) -> EventModel:
    detail = raw.get("_detail") or {}
    pid = str(raw.get("id") or detail.get("id", ""))
    title = detail.get("name") or raw.get("project_name") or raw.get("name", "")
    tlabel = raw.get("tlabel", "")
    start, end = _parse_tlabel(tlabel)
    price = _extract_bili_price(detail)
    ptype = detail.get("project_type") or raw.get("project_type", 1)
    category = {1: "漫展", 2: "演唱会", 3: "展览", 4: "其他"}.get(int(ptype), "其他")
    status = _bili_status(raw.get("label", ""), raw.get("countdown", ""))
    cover = raw.get("cover", "")
    if cover and not cover.startswith("http"):
        cover = "https:" + cover
    return EventModel(
        id=f"bilibili_{pid}",
        source_type="ticketing",
        source_name="bilibili",
        source_id=pid,
        title=title or f"演出 #{pid}",
        category=category,
        city=raw.get("city", ""),
        venue=str(raw.get("venueId", "")),
        start_date=start or datetime.now().strftime("%Y-%m-%d"),
        end_date=end,
        price_range=price,
        ticket_url=f"https://show.bilibili.com/platform/detail.html?id={pid}",
        image_url=cover,
        status=status,
        confidence=1.0,
    )


@register("damai")
def _(raw: dict) -> EventModel:
    rid = str(raw.get("itemId") or raw.get("id") or raw.get("projectId", ""))
    title = raw.get("name") or raw.get("title") or raw.get("itemName", "")
    return EventModel(
        id=f"damai_{rid}",
        source_type="ticketing",
        source_name="damai",
        source_id=rid,
        title=title,
        category=_guess_category(title),
        city=raw.get("cityName") or raw.get("city", ""),
        venue=raw.get("venueName") or raw.get("venue", ""),
        start_date=_parse_date(raw.get("showTime") or raw.get("startTime") or raw.get("startDate", "")),
        price_range=raw.get("priceStr") or raw.get("priceRange", ""),
        ticket_url=raw.get("detailUrl") or raw.get("url", ""),
        image_url=raw.get("poster") or raw.get("image", ""),
        status=_guess_status(raw),
        confidence=1.0,
    )


@register("showstart")
def _(raw: dict) -> EventModel:
    sid = str(raw.get("id") or raw.get("showId", ""))
    return EventModel(
        id=f"showstart_{sid}",
        source_type="ticketing",
        source_name="showstart",
        source_id=sid,
        title=raw.get("title") or raw.get("showName", ""),
        category=_guess_category(raw.get("title", "")),
        city=raw.get("city") or raw.get("cityName", ""),
        venue=raw.get("venue") or raw.get("venueName", ""),
        start_date=_parse_date(raw.get("startTime") or raw.get("showTime", "")),
        price_range=raw.get("price") or raw.get("priceRange", ""),
        ticket_url=raw.get("url") or f"https://www.showstart.com/event/{sid}",
        image_url=raw.get("poster") or raw.get("image", ""),
        status=_guess_status(raw),
        confidence=1.0,
    )


@register("maoyan")
def _(raw: dict) -> EventModel:
    mid = str(raw.get("id") or hash(raw.get("title", "")))
    return EventModel(
        id=f"maoyan_{mid}",
        source_type="ticketing",
        source_name="maoyan",
        source_id=mid,
        title=raw.get("title", ""),
        category=_guess_category(raw.get("title", "")),
        start_date=_parse_date(raw.get("showDate") or raw.get("date", "")),
        ticket_url=raw.get("url", ""),
        image_url=raw.get("image", ""),
        status="售票中",
        confidence=1.0,
    )


@register("piaoxingqiu")
def _(raw: dict) -> EventModel:
    sid = str(hash(raw.get("title", "")))
    return EventModel(
        id=f"piaoxingqiu_{sid}",
        source_type="ticketing",
        source_name="piaoxingqiu",
        source_id=sid,
        title=raw.get("title", ""),
        category=_guess_category(raw.get("title", "")),
        ticket_url=raw.get("url", ""),
        status="售票中",
        confidence=1.0,
    )


@register("yongle")
def _(raw: dict) -> EventModel:
    sid = str(hash(raw.get("title", "")))
    return EventModel(
        id=f"yongle_{sid}",
        source_type="ticketing",
        source_name="yongle",
        source_id=sid,
        title=raw.get("title", ""),
        category=_guess_category(raw.get("title", "")),
        ticket_url=raw.get("url", ""),
        status="售票中",
        confidence=1.0,
    )


def _parse_date(s: str) -> str:
    if not s:
        return datetime.now().strftime("%Y-%m-%d")
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
        try:
            return datetime.strptime(s[:len(fmt)], fmt).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue
    # Try ISO format
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    return s[:10] if len(s) >= 10 else s


def _format_price(low, high) -> str:
    if low is None and high is None:
        return "待定"
    l = int(low) if low else 0
    h = int(high) if high else 0
    if l and h and l != h:
        return f"¥{l}-{h}"
    if l:
        return f"¥{l}起"
    if h:
        return f"¥{h}"
    return "待定"


def _guess_category(title: str) -> str:
    t = title.lower().replace(" ", "")
    for alias, cat in CATEGORY_ALIASES.items():
        if alias.lower() in t:
            return cat
    return "其他"


def _parse_tlabel(tlabel: str) -> tuple[str, str | None]:
    """Parse B站 tlabel like '2026.05.04' or '2026.05.03 - 05.05'"""
    if not tlabel:
        return "", None
    tlabel = tlabel.replace(".", "-").replace(" ", "")
    if " - " in tlabel:
        parts = tlabel.split(" - ")
        start = parts[0]
        end = parts[1]
        if len(end) < 8:
            end = start[:5] + "-" + end
        return start, end
    return tlabel, None


def _extract_bili_price(detail: dict) -> str:
    """Extract price from B站 detail API response."""
    performances = detail.get("performance", []) or []
    for perf in performances:
        screens = perf.get("screenList", []) or []
        for screen in screens:
            skus = screen.get("skuList", []) or screen.get("skus", []) or []
            prices = [s.get("price", 0) for s in skus if s.get("price")]
            if prices:
                lo, hi = min(prices), max(prices)
                if lo and hi:
                    return f"¥{int(lo/100)}-{int(hi/100)}"
    return "待定"


def _bili_status(label: str, countdown: str) -> str:
    s = (label + countdown).lower()
    if any(w in s for w in ["热卖", "售票", "销售"]):
        return "售票中"
    if any(w in s for w in ["即将", "预告", "预售"]):
        return "即将开票"
    if any(w in s for w in ["截止", "结束", "停售"]):
        return "已结束"
    return "售票中"


def _guess_status(raw: dict) -> str:
    s = str(raw.get("status", "")).lower()
    if s in ("1", "onsale", "selling", "售票中"):
        return "售票中"
    if s in ("0", "upcoming", "coming", "预告"):
        return "预告"
    if s in ("2", "end", "over", "已结束"):
        return "已结束"
    return "售票中"
