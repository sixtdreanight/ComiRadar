import json
from scrapers.base import TicketingScraper
from parsel import Selector


class DamaiScraper(TicketingScraper):
    platform = "damai"
    base_url = "https://search.damai.cn"
    rate_limit = 5.0

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "二次元", "同人展", "Cosplay", "动漫"]
        for kw in keywords:
            raw = await self.fetch(
                "/search",
                params={"keyword": kw, "pageIndex": 1, "pageSize": 30},
                headers={
                    "Referer": "https://www.damai.cn/",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            data = self.parse(raw)
            if not data:
                break
            results.extend(data)
        return results

    def parse(self, raw: str) -> list[dict]:
        # Try JSON embedded in HTML first
        sel = Selector(text=raw)
        script = sel.css("script#__NEXT_DATA__::text").get()
        if script:
            try:
                obj = json.loads(script)
                items = obj.get("props", {}).get("pageProps", {}).get("items", [])
                return items
            except (json.JSONDecodeError, KeyError):
                pass
        # Fallback: CSS extraction
        items = []
        for el in sel.css(".search-item, .item-card, .event-card"):
            title = el.css(".title::text, .name::text").get()
            link = el.css("a::attr(href)").get()
            if title:
                items.append({"title": title.strip(), "url": link or ""})
        return items
