import json

from scrapers.base import TicketingScraper


class ShowstartScraper(TicketingScraper):
    platform = "showstart"
    base_url = "https://www.showstart.com"
    rate_limit = 3.0

    async def scrape(self) -> list[dict]:
        results = []
        for page in range(1, 10):
            raw = await self.fetch(
                "/api/search/search",
                params={"keyword": "漫展", "pageNo": page, "pageSize": 20},
            )
            data = self.parse(raw)
            if not data:
                break
            results.extend(data)
        return results

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            if obj.get("code") != 200:
                return []
            return obj.get("data", {}).get("items", []) or []
        except (json.JSONDecodeError, KeyError):
            return []
