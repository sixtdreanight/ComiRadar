import asyncio
import json
import random
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from config import MAX_RETRIES, RATE_LIMIT, SCRAPE_TIMEOUT, UA_POOL
from logger import get_logger

_log = get_logger(__name__)

ROOT = Path(__file__).parent.parent


class ScraperError(Exception):
    pass


_SHELL_DANGEROUS = frozenset({";", "|", "&", "$", "`", "(", ")", "{", "}", "<", ">", "\n", "\r"})


def validate_worker_args(args: list[str]) -> None:
    """Block shell metacharacters in worker arguments."""
    for arg in args:
        if set(str(arg)) & _SHELL_DANGEROUS:
            raise ScraperError(f"Invalid worker arg: {arg}")


class AbstractScraper(ABC):
    platform: str = ""
    base_url: str = ""
    rate_limit: float = RATE_LIMIT
    cookies: dict[str, str] = {}
    _registry: dict[str, type["AbstractScraper"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.platform:
            cls._registry[cls.platform] = cls

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._last_request = 0.0

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "User-Agent": random.choice(UA_POOL),
                "Accept": "text/html,application/json,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            self._client = httpx.AsyncClient(
                timeout=SCRAPE_TIMEOUT,
                headers=headers,
                cookies={k: v for k, v in self.cookies.items() if v},
                follow_redirects=False,
                verify=True,
            )
        return self._client

    async def _rate_limit(self):
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request = asyncio.get_event_loop().time()

    async def fetch(self, path: str, params: dict | None = None) -> str:
        for attempt in range(MAX_RETRIES):
            try:
                await self._rate_limit()
                url = f"{self.base_url}{path}"
                resp = await self.client.get(url, params=params)
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503) and attempt < MAX_RETRIES - 1:
                    await asyncio.sleep((2**attempt) + random.uniform(0, 1))
                    continue
                raise ScraperError(f"{self.platform}: HTTP {e.response.status_code}") from e
            except httpx.RequestError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep((2**attempt) + random.uniform(0, 1))
                    continue
                raise ScraperError(f"{self.platform}: {e}") from e
        raise ScraperError(f"{self.platform}: max retries exceeded")

    @abstractmethod
    async def scrape(self) -> list[dict]:
        ...

    @abstractmethod
    def parse(self, raw: str) -> list[dict]:
        ...


class SubprocessScraper(AbstractScraper):
    """子进程抓取器基类 — 用于需要独立进程的抓取器（浏览器自动化等）。

    使用结构化 JSON 行协议（NDJSON）进行 IPC：
    worker 每行输出一条 JSON 消息，最后一行必须是 JSON 数组（结果）。
    """

    worker_script: str = ""
    worker_args: list[str] = []
    worker_timeout: int = 180

    async def scrape(self) -> list[dict]:
        script = ROOT / self.worker_script
        validate_worker_args(self.worker_args)
        args = [sys.executable, str(script), *self.worker_args]
        try:
            result = subprocess.run(
                args, shell=False,
                capture_output=True, text=True, timeout=self.worker_timeout, cwd=ROOT,
            )
        except subprocess.TimeoutExpired:
            _log.warning(f"[{self.platform}] worker timeout ({self.worker_timeout}s)")
            return []

        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                _log.info(line)

        if result.returncode != 0:
            _log.error(f"[{self.platform}] worker failed (exit {result.returncode})")
            return []

        # NDJSON: last non-empty line is the result array
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        if not lines:
            return []
        try:
            data = json.loads(lines[-1])
            if isinstance(data, list):
                _log.info(f"[{self.platform}] {len(data)} events")
                return data
            return []
        except (json.JSONDecodeError, IndexError):
            return []

    def parse(self, raw: str) -> list[dict]:
        return json.loads(raw) if raw else []


class TicketingScraper(AbstractScraper):
    """票务平台抓取器基类"""


class SocialScraper(AbstractScraper):
    """社媒抓取器基类"""

    @abstractmethod
    async def search(self, keyword: str) -> list[dict]:
        ...
