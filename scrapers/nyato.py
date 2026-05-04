import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


class NyatoScraper:
    platform = "nyato"

    async def scrape(self) -> list[dict]:
        result = subprocess.run(
            [sys.executable, str(ROOT / "_playwright_worker.py"), "nyato"],
            capture_output=True, text=True, timeout=180, cwd=ROOT,
        )
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(line, file=sys.stderr)
        if result.returncode != 0:
            return []
        try:
            return json.loads(result.stdout.strip())
        except (json.JSONDecodeError, IndexError):
            return []
