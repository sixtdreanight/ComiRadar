import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent

class ChinajoyScraper:
    platform = "chinajoy"
    async def scrape(self) -> list[dict]:
        result = subprocess.run([sys.executable, str(ROOT / "_playwright_worker.py"), "chinajoy"],
            capture_output=True, text=True, timeout=120, cwd=ROOT)
        if result.stderr:
            for line in result.stderr.strip().split("\n"): print(line, file=sys.stderr)
        try: return json.loads(result.stdout.strip())
        except: return []
