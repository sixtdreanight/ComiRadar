import json
import subprocess
import sys
from pathlib import Path


class BilibiliScraper:
    platform = "bilibili"

    async def scrape(self) -> list[dict]:
        script = Path(__file__).parent.parent.parent / "_bilibili_worker.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=300,
            cwd=Path(__file__).parent.parent.parent,
        )
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(line, file=sys.stderr)
        if result.returncode != 0:
            print(f"  [bilibili] worker failed (exit {result.returncode})", file=sys.stderr)
            return []
        try:
            data = json.loads(result.stdout.strip().split("\n")[-1])
            print(f"  [bilibili] {len(data)} events", file=sys.stderr)
            return data
        except (json.JSONDecodeError, IndexError):
            return []
