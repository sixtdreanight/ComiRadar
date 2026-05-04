import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


class WeiboScraper:
    platform = "weibo"

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

        # Filter: keep only posts likely to contain event announcements
        event_keywords = ["展", "会", "演唱会", "音乐会", "见面会", "嘉年华", "ONLY", "only", "同人"]
        posts = [p for p in posts if any(kw in p.get("text", "") for kw in event_keywords)]

        if not posts:
            return []

        # Step 2: AI 推理
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False)
            tmp_path = f.name

        ai_result = subprocess.run(
            [sys.executable, str(ROOT / "_ai_worker.py"), tmp_path],
            capture_output=True, text=True, timeout=600, cwd=ROOT,
        )
        Path(tmp_path).unlink(missing_ok=True)

        if ai_result.stderr:
            for line in ai_result.stderr.strip().split("\n"):
                print(line, file=sys.stderr)
        if ai_result.returncode != 0:
            print(f"  [weibo] AI worker exit={ai_result.returncode}", file=sys.stderr)
        if not ai_result.stdout.strip():
            print(f"  [weibo] AI worker empty stdout, stderr lines={len(ai_result.stderr.split(chr(10)))}", file=sys.stderr)

        try:
            events = json.loads(ai_result.stdout.strip())
            for e in events:
                e["_source"] = "weibo_ai"
            print(f"  [weibo] AI extracted {len(events)} events", file=sys.stderr)
            return events
        except (json.JSONDecodeError, IndexError) as e:
            print(f"  [weibo] AI parse error: {e}", file=sys.stderr)
            return []
