"""AI推理 Worker：预筛选 + DeepSeek 推理演出信息。"""
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
    "见面会", "CP展", "ComiCup", "CP", "ONLY", "only", "CD", "萤火虫",
    "IJOY", "BW", "BML", "CJ", "ChinaJoy", "CCG", "ido", "IDO",
]

DATE_RE = re.compile(
    r"(\d{4}[年.\-/]\d{1,2}[月.\-/]\d{1,2}[日号]?)|"
    r"(\d{1,2}[月.\-/]\d{1,2}[日号]?\s*[-至到]\s*\d{1,2}[日号]?)|"
    r"(\d{1,2}月\d{1,2}[日号]?)"
)

NOISE_RE = re.compile(r"(返图|自拍|面基|集邮|扩列|求扩|#.*?#|超话|coser)")

PROMPT = """你是二次元演出情报助手。从以下精炼的社媒情报中推理演出信息。同时利用你的知识列出已知的2026年中国漫展/同人展/二次元音乐会。

社媒情报:
{posts}

规则：
1. 只提取明确是演出活动的情报，忽略无关内容
2. 多条情报指向同一事件时合并，交叉验证
3. 利用你的知识补全：如果你知道某活动的典型时间和场馆，请补全
4. 日期模糊时合理推断（如"五一期间"→5月1-5日，"端午"→查2026年端午=6月19-21日）
5. 同时列出你训练数据中知道的2026年已知活动（如ComiCup、萤火虫、IJOY等）

输出JSON对象（不要markdown）:
{
  "events": [{"title":"活动名","date":"YYYY-MM-DD","endDate":"YYYY-MM-DD","city":"城市","venue":"场馆","category":"漫展/同人展/演唱会/展览/音乐会/其他","confidence":0.7,"source":"social/knowledge"}],
  "knowledge": [{"title":"已知活动名","typicalMonth":"通常月份","city":"城市","venue":"场馆","notes":"备注"}]
}"""


def prefilter(posts: list[dict]) -> list[dict]:
    """提取关键信息，过滤噪音，减少 token 消耗。"""
    refined = []
    for p in posts:
        text = p.get("text", "")
        if not text or len(text) < 15:
            continue
        # 丢弃纯噪音
        if NOISE_RE.search(text) and not any(kw in text for kw in ["展", "届", "音乐会", "演唱会"]):
            continue

        score = 0
        city = ""
        venue = ""
        dates = []

        # 提取城市
        for c in CITIES:
            if c in text:
                city = c
                score += 1
                break

        # 提取场馆
        for vk in VENUE_KW:
            idx = text.find(vk)
            if idx >= 0:
                start = max(0, idx - 6)
                end = min(len(text), idx + len(vk) + 6)
                venue = text[start:end].strip()
                score += 1
                break

        # 提取日期
        for m in DATE_RE.finditer(text):
            dates.append(m.group(0))
        if dates:
            score += 1

        # 提取活动关键词
        for ek in EVENT_KW:
            if ek.lower() in text.lower():
                score += 1
                break

        # 生成精炼摘要: 只保留关键行
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        key_lines = [l for l in lines if any(
            kw in l for kw in CITIES + VENUE_KW + EVENT_KW
        ) or re.search(r"\d", l)]
        summary = " | ".join(key_lines[:3]) if key_lines else text[:120]

        if score >= 2 or (score >= 1 and any(d in text for d in ["第", "届", "官宣", "定档"])):
            refined.append({
                "text": summary[:200],
                "date": p.get("date", ""),
                "city": city,
                "venue": venue,
                "dates_found": dates[:3],
                "score": score,
            })

    # 按 score 降序，去重（相同 text 只保留一条）
    seen = set()
    uniq = []
    for r in sorted(refined, key=lambda x: x["score"], reverse=True):
        key = r["text"][:50]
        if key not in seen:
            seen.add(key)
            uniq.append(r)

    print(f"  [prefilter] {len(posts)}→{len(uniq)} posts (score>=2)", file=sys.stderr)
    return uniq


async def analyze(posts: list[dict]) -> dict:
    if not API_KEY:
        print("[AI] No API key", file=sys.stderr)
        return {"events": [], "knowledge": []}

    # Pre-filter
    refined = prefilter(posts)
    if not refined:
        return {"events": [], "knowledge": []}

    # Batch send to AI (single call with all refined data)
    posts_text = json.dumps(refined, ensure_ascii=False)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": PROMPT.replace("{posts}", posts_text)}],
                "temperature": 0.1,
                "max_tokens": 8000,
            },
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removesuffix("```").strip()
        try:
            result = json.loads(content)
            events = result.get("events", []) if isinstance(result, dict) else []
            knowledge = result.get("knowledge", []) if isinstance(result, dict) else []
        except json.JSONDecodeError:
            events = json.loads(content) if isinstance(content, str) else []
            knowledge = []

    print(f"  [AI] {len(events)} events + {len(knowledge)} known activities", file=sys.stderr)
    return {"events": events, "knowledge": knowledge}


async def main():
    try:
        input_file = sys.argv[1] if len(sys.argv) > 1 else None
        if input_file:
            with open(input_file, encoding="utf-8") as f:
                posts = json.load(f)
        else:
            posts = json.loads(sys.stdin.read())

        print(f"[AI] Processing {len(posts)} posts...", file=sys.stderr)
        result = await analyze(posts)
        all_events = result.get("events", [])
        for k in result.get("knowledge", []):
            all_events.append({
                "title": k.get("title", ""),
                "date": "",
                "city": k.get("city", ""),
                "venue": k.get("venue", ""),
                "category": k.get("category", "其他"),
                "confidence": 0.3,
                "source": "ai_knowledge",
            })
        print(json.dumps(all_events, ensure_ascii=False))
    except Exception as e:
        print(f"[AI] fatal: {e}", file=sys.stderr)
        print("[]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
