from scrapers.base import TicketingScraper
from parsel import Selector


class PiaoXingQiuScraper(TicketingScraper):
    platform = "piaoxingqiu"
    base_url = "https://www.piaoxingqiu.com"
    rate_limit = 3.0

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "二次元", "同人展"]
        for kw in keywords:
            raw = await self.fetch("/search", params={"keyword": kw})
            data = self.parse(raw)
            results.extend(data)
        return results

    def parse(self, raw: str) -> list[dict]:
        sel = Selector(text=raw)
        return [
            {
                "title": (el.css(".name::text, .title::text").get() or "").strip(),
                "url": el.css("a::attr(href)").get() or "",
            }
            for el in sel.css(".event-item, .show-item, .search-result-item")
        ]
