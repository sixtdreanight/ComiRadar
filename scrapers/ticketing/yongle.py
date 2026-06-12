from parsel import Selector

from scrapers.base import TicketingScraper


class YongleScraper(TicketingScraper):
    platform = "yongle"
    base_url = "https://www.228.com.cn"
    rate_limit = 3.0

    async def scrape(self) -> list[dict]:
        results = []
        for page in range(1, 6):
            raw = await self.fetch("/search", params={"keyword": "漫展", "page": page})
            data = self.parse(raw)
            if not data:
                break
            results.extend(data)
        return results

    def parse(self, raw: str) -> list[dict]:
        sel = Selector(text=raw)
        return [
            {
                "title": (el.css(".title::text, .name::text").get() or "").strip(),
                "url": el.css("a::attr(href)").get() or "",
            }
            for el in sel.css(".search-item, .product-item, .ticket-item")
        ]
