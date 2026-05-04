import json
import os
import hashlib
import httpx
from db.schema import EventModel

AI_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
AI_API_URL = "https://api.deepseek.com/v1/chat/completions"

PROMPT = """从以下社交媒体帖子中提取漫展/二次元演出信息。返回纯JSON数组（不要markdown代码块）。

帖子内容: {text}

提取字段: title(活动名), date(日期YYYY-MM-DD), city(城市), venue(场馆), category(漫展/同人展/演唱会/舞台剧/其他)
如果某字段无法确定，填null。每条帖子返回一个对象。

示例输出:
[{"title":"CP2026上海同人展","date":"2026-06-15","city":"上海","venue":"国家会展中心","category":"同人展"}]"""


async def extract_with_ai(platform: str, items: list[dict]) -> list[EventModel]:
    if not AI_API_KEY:
        return _fallback_extract(platform, items)
    events = []
    for item in items:
        text = item.get("text", "")
        if not text or len(text) < 20:
            continue
        try:
            parsed = await _call_ai(text[:2000])
            for p in parsed:
                if p.get("title") and p.get("date"):
                    eid = hashlib.sha256(f"{p['title']}|{p.get('city','')}|{p['date']}".encode()).hexdigest()[:16]
                    events.append(EventModel(
                        id=f"{platform}_ai_{eid}",
                        source_type="social", source_name=platform,
                        source_id=item.get("url", ""),
                        title=p["title"], category=p.get("category", "其他"),
                        city=p.get("city", ""), venue=p.get("venue", ""),
                        start_date=p["date"],
                        ticket_url=None, image_url=None,
                        status="预告", confidence=0.7,
                    ))
        except Exception:
            continue
    return events


async def _call_ai(text: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            AI_API_URL,
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": PROMPT.format(text=text)}],
                "temperature": 0.1,
                "max_tokens": 500,
            },
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removesuffix("```").strip()
        return json.loads(content)


def _fallback_extract(platform: str, items: list[dict]) -> list[EventModel]:
    # Regex-based extraction when no AI API key
    from pipeline.extractor import extract_events
    return extract_events(platform, items)
