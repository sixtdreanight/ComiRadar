import json
import os
import subprocess
import sys
from pathlib import Path

from chinese_scraper_utils import DeepSeekClient, EventExtractor

ROOT = Path(__file__).parent.parent.parent


class WeiboScraper:
    platform = "weibo"

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self._extractor = EventExtractor(
            client=DeepSeekClient(api_key=api_key, model="deepseek-v4-flash"),
            event_types=["漫展", "同人展", "演唱会", "音乐会", "展览"],
            min_confidence=0.4,
        ) if api_key else None

    async def scrape(self) -> list[dict]:
        # Step 1: Playwright 抓取微博帖文
        pw_result = subprocess.run(
            [sys.executable, str(ROOT / "_playwright_worker.py"), "weibo"],
            capture_output=True, text=True, timeout=300, cwd=ROOT,
        )
        if pw_result.stderr:
            for line in pw_result.stderr.strip().split("\n"):
                print(line, file=sys.stderr)
        if pw_result.returncode != 0:
            return []

        try:
            posts = json.loads(pw_result.stdout.strip())
        except (json.JSONDecodeError, IndexError):
            return []

        if not posts:
            return []

        # Step 2: 使用 EventExtractor 的 LLM 提取管道（替代原来的 subprocess _ai_worker.py）
        if self._extractor:
            texts = [p.get("text", "") for p in posts]
            extracted = self._extractor.extract(texts)

            events = []
            for e in extracted:
                events.append({
                    "title": e.title,
                    "date": e.date,
                    "endDate": e.end_date,
                    "city": e.city,
                    "venue": e.venue,
                    "category": e.category,
                    "confidence": e.confidence,
                    "_source": "weibo_ai",
                })
            print(f"  [weibo] EventExtractor found {len(events)} events", file=sys.stderr)
            return events

        # Fallback: 旧的关键词过滤
        event_keywords = ["展", "会", "演唱会", "音乐会", "见面会", "嘉年华", "ONLY", "only", "同人"]
        posts = [p for p in posts if any(kw in p.get("text", "") for kw in event_keywords)]
        print(f"  [weibo] keyword fallback: {len(posts)} posts", file=sys.stderr)
        return []
