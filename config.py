from pathlib import Path
import os
from cn_scraper_utils import UA_POOL

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
