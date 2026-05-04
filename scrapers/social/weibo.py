import json
import subprocess
import sys
from pathlib import Path


class WeiboScraper:
    platform = "weibo"

    async def scrape(self) -> list[dict]:
        worker = Path(__file__).parent.parent.parent / "_playwright_worker.py"
        result = subprocess.run(
            [sys.executable, str(worker), "weibo"],
            capture_output=True, text=True, timeout=300,
            cwd=Path(__file__).parent.parent.parent,
        )
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(line, file=sys.stderr)
        if result.returncode != 0:
            return []
        try:
            return json.loads(result.stdout.strip().split("\n")[-1])
        except (json.JSONDecodeError, IndexError):
            return []
