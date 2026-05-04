from pathlib import Path
from pydantic import BaseModel as PydanticBase

import os

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "events.db"
EXPORT_PATH = Path(os.environ.get("COMI_EXPORT_PATH", BASE_DIR / "events.json"))
DAYS_AHEAD = 90
SCRAPE_TIMEOUT = 30
MAX_RETRIES = 3
RATE_LIMIT = 2.0

NOTIFIERS: dict[str, dict] = {
    "serverchan": {"key": ""},
    "bark": {"url": ""},
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]
