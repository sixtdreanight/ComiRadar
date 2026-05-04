import json
from scrapers.base import TicketingScraper
from config import BILIBILI_COOKIES


class BilibiliScraper(TicketingScraper):
    platform = "bilibili"
    base_url = "https://show.bilibili.com"
    rate_limit = 2.0
    cookies = BILIBILI_COOKIES

    async def scrape(self) -> list[dict]:
        results = []
        for project_type in (1, 2, 3, 4):
            page = 1
            while page <= 10:
                raw = await self.fetch(
                    "/api/ticket/project/list",
                    params={
                        "version": "134", "page": page, "pagesize": 50,
                        "project_type": project_type, "platform": "web",
                        "area": "0", "p_type": str(project_type),
                    },
                )
                data = self.parse(raw)
                if not data:
                    break
                results.extend(data)
                if len(data) < 50:
                    break
                page += 1
        return results

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            if obj.get("errno") != 0:
                return []
            return obj.get("data", {}).get("result", []) or []
        except (json.JSONDecodeError, KeyError):
            return []
