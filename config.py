from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

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

# B站 Cookie 用于绕过风控。在浏览器登录 show.bilibili.com 后，
# F12 → Application → Cookies → 复制 buvid3, SESSDATA, bili_jct
BILIBILI_COOKIES: dict[str, str] = {
    "buvid3": os.environ.get("BILI_BUVID3", ""),
    "SESSDATA": os.environ.get("BILI_SESSDATA", ""),
    "bili_jct": os.environ.get("BILI_BILI_JCT", ""),
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]
