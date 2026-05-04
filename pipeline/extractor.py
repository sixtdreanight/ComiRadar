import hashlib
import re
from datetime import datetime
from db.schema import EventModel

CITIES = [
    "上海", "北京", "广州", "深圳", "成都", "杭州", "南京", "武汉", "重庆",
    "西安", "长沙", "苏州", "天津", "郑州", "东莞", "青岛", "沈阳", "宁波",
    "昆明", "大连", "厦门", "合肥", "佛山", "无锡", "福州", "济南", "哈尔滨",
    "长春", "石家庄", "南宁", "贵阳", "南昌", "太原", "乌鲁木齐", "兰州",
    "海口", "银川", "西宁", "拉萨", "珠海", "常州", "南通", "徐州", "温州",
    "绍兴", "嘉兴", "金华", "泉州", "漳州", "三亚",
]

VENUE_KEYWORDS = [
    "会展中心", "展览中心", "国际博览中心", "展览馆", "体育馆", "大剧院",
    "剧院", "艺术中心", "文化中心", "大会堂", "展厅", "博览馆", "会议中心",
    "美术馆", "博物馆", "科技馆", "livehouse", "live house", "LiveHouse",
]

DATE_PATTERNS = [
    re.compile(r"(\d{4})[年.\-](\d{1,2})[月.\-](\d{1,2})[日号]?"),
    re.compile(r"(\d{1,2})月(\d{1,2})[日号]?\s*[-–—至到]\s*(\d{1,2})[日号]?"),
]


def extract_events(platform: str, raw_items: list[dict]) -> list[EventModel]:
    events = []
    for item in raw_items:
        text = item.get("text", "")
        if not text:
            continue
        event = _extract_one(platform, item)
        if event:
            events.append(event)
    return events


def _extract_one(platform: str, item: dict) -> EventModel | None:
    text = item.get("text", "")
    title = _extract_title(text) or item.get("user", "") + " 发布的演出"
    city = _extract_city(text)
    date = _extract_date(text)
    venue = _extract_venue(text)
    event_id = hashlib.sha256(f"{title}|{city}|{date}".encode()).hexdigest()[:16]
    score = sum([bool(date), bool(city), bool(venue)])
    confidence = {3: 0.9, 2: 0.7, 1: 0.5}.get(score, 0.5)
    return EventModel(
        id=f"{platform}_{event_id}",
        source_type="social",
        source_name=platform,
        source_id=item.get("url", ""),
        title=title,
        category=_guess_category(text),
        city=city,
        venue=venue,
        start_date=date or datetime.now().strftime("%Y-%m-%d"),
        ticket_url=None,
        image_url=(item.get("images") or [None])[0],
        status="预告",
        confidence=confidence,
    )


def _extract_title(text: str) -> str:
    # Look for event name patterns like "XXX展", "第X届XXX"
    m = re.search(r"(第[一二三四五六七八九十\d]+届)?[^\s，。,\.]{2,20}(展|同人展|嘉年华|见面会|演唱会)", text)
    if m:
        return m.group(0)
    # Fallback: first line or first sentence
    for sep in ("。", "！", "！", "\n"):
        if sep in text:
            return text[:text.index(sep)]
    return text[:50]


def _extract_city(text: str) -> str:
    for city in CITIES:
        if city in text:
            return city
    return ""


def _extract_date(text: str) -> str:
    year = datetime.now().year
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if m:
            groups = m.groups()
            y = int(groups[0]) if len(str(groups[0])) == 4 else year
            mth = int(groups[0]) if len(str(groups[0])) != 4 else int(groups[1])
            day = int(groups[1]) if len(str(groups[0])) != 4 else int(groups[2])
            try:
                dt = datetime(y, mth, day)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


def _extract_venue(text: str) -> str:
    for kw in VENUE_KEYWORDS:
        # Find the keyword and get surrounding context as venue name
        idx = text.find(kw)
        if idx >= 0:
            start = max(0, idx - 8)
            end = min(len(text), idx + len(kw) + 4)
            return text[start:end].strip()
    return ""


def _guess_category(text: str) -> str:
    aliases = {
        "漫展": "漫展", "同人展": "同人展", "演唱会": "演唱会",
        "舞台剧": "舞台剧", "音乐会": "音乐会", "cosplay": "漫展",
        "Cosplay": "漫展", "动漫展": "漫展", "嘉年华": "漫展",
    }
    for alias, cat in aliases.items():
        if alias.lower() in text.lower():
            return cat
    return "其他"
