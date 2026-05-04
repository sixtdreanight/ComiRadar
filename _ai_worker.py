"""AI Worker：从社媒帖文提取演出信息。只做提取，不做知识库生成。"""
import json
import os
import re
import sys
import httpx

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"

CITIES = [
    "上海", "北京", "广州", "深圳", "成都", "杭州", "南京", "武汉", "重庆",
    "西安", "长沙", "苏州", "天津", "郑州", "沈阳", "青岛", "厦门", "合肥",
    "昆明", "大连", "济南", "哈尔滨", "长春", "南宁", "贵阳", "南昌", "太原",
    "石家庄", "海口", "珠海", "常州", "无锡", "佛山", "东莞", "福州", "宁波",
]

VENUE_KW = [
    "会展中心", "展览中心", "国际博览中心", "展览馆", "体育馆", "大剧院",
    "剧院", "艺术中心", "文化中心", "会议中心", "美术馆", "博物馆", "博览馆",
]

EVENT_KW = [
    "漫展", "同人展", "演唱会", "音乐会", "舞台剧", "展览", "嘉年华",
    "见面会", "ComiCup", "CP展", "ONLY", "萤火虫", "ChinaJoy",
    "IJOY", "BW", "BML", "CCG", "IDO",
]

CATEGORIES = ["漫展", "同人展", "演唱会", "音乐会", "展览", "其他"]

NOISE_PATTERNS = [
    r"返图", r"自拍", r"面基", r"集邮", r"扩列", r"求扩",
    r"#.*?#", r"超话", r"coser", r"好开心", r"玩得",
]

DATE_RE = re.compile(
    r"(\d{4}[年.\-/]\d{1,2}[月.\-/]\d{1,2}[日号]?)|"
    r"(\d{1,2}[月.\-/]\d{1,2}[日号]?\s*[-至到]\s*\d{1,2}[日号]?)|"
    r"(\d{1,2}月\d{1,2}[日号]?)"
)

PROMPT = """从社媒情报中提取近期或未来的演出活动信息（只提取今天之后的活动，忽略已结束的）。

规则：
1. 只提取有明确活动名称的演出
2. date 必须是未来日期（2026年5月或更晚），过去的不要
3. city/venue 不确定就留空
4. category 从：漫展、同人展、演唱会、音乐会、展览、其他
5. 多条情报指向同一事件时合并
6. 返图、自拍、闲聊忽略

输入：
{posts}

输出纯JSON数组：
[{{"title":"活动名","date":"YYYY-MM-DD","endDate":"YYYY-MM-DD或null","city":"或空","venue":"或空","category":"类别","confidence":0.7}}]"""


def prefilter(posts: list[dict]) -> list[dict]:
    refined = []
    for p in posts:
        text = p.get("text", "")
        if len(text) < 15:
            continue

        # 丢弃纯噪音
        noise = False
        for pat in NOISE_PATTERNS:
            if re.search(pat, text):
                noise = True
                break
        if noise and not any(kw in text for kw in ["展", "届", "音乐会", "演唱会", "官宣", "定档"]):
            continue

        score = 0
        city = ""
        dates = []

        for c in CITIES:
            if c in text:
                city = c
                score += 1
                break

        for vk in VENUE_KW:
            if vk in text:
                score += 1
                break

        dates = [m.group(0) for m in DATE_RE.finditer(text)]
        if dates:
            score += 2  # date is most important

        for ek in EVENT_KW:
            if ek.lower() in text.lower():
                score += 1
                break

        # Compress: only keep lines with keywords
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        key_lines = [l for l in lines if any(kw in l for kw in CITIES + VENUE_KW + EVENT_KW) or re.search(r"\d", l)]
        summary = " | ".join(key_lines[:2]) if key_lines else text[:100]

        if score >= 3:
            refined.append({
                "text": summary[:200],
                "date_hint": p.get("date", ""),
                "city": city,
                "dates_found": dates[:2],
                "score": score,
            })

    # Dedup similar texts
    seen = set()
    uniq = []
    for r in sorted(refined, key=lambda x: x["score"], reverse=True):
        key = r["text"][:40]
        if key not in seen:
            seen.add(key)
            uniq.append(r)

    # Filter out posts about past events (mention pre-2026 dates)
    uniq = [r for r in uniq if not re.search(r"202[0-4]|2025", r["text"])]

    print(f"  [prefilter] {len(posts)}→{len(uniq)} posts", file=sys.stderr)
    return uniq


async def analyze(posts: list[dict]) -> list[dict]:
    if not API_KEY:
        return []

    refined = prefilter(posts)
    if not refined:
        return []

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": PROMPT.replace("{posts}", json.dumps(refined, ensure_ascii=False))}],
                "temperature": 0.1,
                "max_tokens": 6000,
            },
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removesuffix("```").strip()
        try:
            events = json.loads(content)
        except json.JSONDecodeError:
            events = []

    # Post-filter: require at least title
    events = [e for e in events if e.get("title") and e["title"] != "null"]
    # Normalize categories
    for e in events:
        cat = e.get("category", "其他")
        if cat not in CATEGORIES:
            e["category"] = "其他"
        if not e.get("confidence"):
            e["confidence"] = 0.5
        # Clean title
        e["title"] = e["title"].strip().replace("  ", " ")

    print(f"  [AI] {len(events)} events extracted", file=sys.stderr)
    return events


async def main():
    try:
        input_file = sys.argv[1] if len(sys.argv) > 1 else None
        if input_file:
            with open(input_file, encoding="utf-8") as f:
                posts = json.load(f)
        else:
            posts = json.loads(sys.stdin.read())

        print(f"[AI] {len(posts)} posts", file=sys.stderr)
        events = await analyze(posts)
        print(json.dumps(events, ensure_ascii=False))
    except Exception as e:
        print(f"[AI] error: {e}", file=sys.stderr)
        print("[]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
