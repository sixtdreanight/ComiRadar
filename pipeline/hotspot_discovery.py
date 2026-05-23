"""
Hotspot Discovery — 从微博/知乎热搜中自动发现新的漫展活动。

这是 ComiRadar 的全新能力：原来只从票务平台抓已上架的活动，
现在可以通过社媒热点提前发现未上架的漫展/演唱会消息。
"""

import os
from chinese_scraper_utils import (
    scrape_weibo_hot,
    scrape_zhihu_hot,
    EventExtractor,
    DeepSeekClient,
    search_web,
    HotTopic,
    ExtractedEvent,
)


# 活动相关关键词（粗筛，省 AI 费用）
_EVENT_KEYWORDS = [
    "漫展", "同人展", "演唱会", "音乐会", "展览", "嘉年华",
    "ComiCup", "CP", "ChinaJoy", "BML", "BW", "ONLY",
    "见面会", "舞台剧", "音乐节", "Live",
]


def _is_event_related(topic: HotTopic) -> bool:
    """粗筛：话题是否可能与活动相关。"""
    text = f"{topic.title} {topic.summary}".lower()
    return any(kw.lower() in text for kw in _EVENT_KEYWORDS)


def discover_from_hotspots(api_key: str) -> list[ExtractedEvent]:
    """从微博/知乎热搜中发现新的漫展/演出活动。

    Args:
        api_key: DeepSeek API key。

    Returns:
        高置信度的 ExtractedEvent 列表。
    """
    # 1. 抓取热点
    topics = scrape_weibo_hot() + scrape_zhihu_hot()
    if not topics:
        return []

    # 2. 粗筛（只保留可能相关的）
    candidates = [t for t in topics if _is_event_related(t)]
    if not candidates:
        return []

    # 3. LLM 提取结构化信息
    client = DeepSeekClient(api_key=api_key, model="deepseek-v4-flash")
    extractor = EventExtractor(
        client=client,
        event_types=["漫展", "同人展", "演唱会", "音乐会", "展览"],
        min_confidence=0.45,  # 比默认低一点，因为热搜信息可能不完整
    )

    texts = [f"{t.title}。{t.summary}" for t in candidates]
    events = extractor.extract(texts)

    # 4. 高置信度事件进一步搜索验证
    enriched = []
    for event in events:
        if event.confidence >= 0.5 and event.title:
            try:
                results = search_web(f"{event.title} {event.city} 活动 时间 地点", max_results=3)
                if results:
                    # 用搜索结果补充缺失字段
                    if not event.venue:
                        event.venue = _extract_venue_from_snippets([r.snippet for r in results])
            except Exception:
                pass
        enriched.append(event)

    return enriched


def _extract_venue_from_snippets(snippets: list[str]) -> str:
    """从搜索片段中提取场馆名。"""
    venue_keywords = [
        "会展中心", "展览中心", "国际博览中心", "展览馆", "体育馆",
        "大剧院", "剧院", "艺术中心", "文化中心", "会议中心",
        "美术馆", "博物馆", "LiveHouse", "livehouse",
    ]
    for snippet in snippets:
        for kw in venue_keywords:
            import re
            m = re.search(rf"([^\s，。]{{2,12}}{re.escape(kw)})", snippet)
            if m:
                return m.group(1)
    return ""
