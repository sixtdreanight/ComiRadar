from scrapers.base import TicketingScraper
from parsel import Selector


class MaoyanScraper(TicketingScraper):
    platform = "maoyan"
    base_url = "https://www.maoyan.com"
    rate_limit = 3.0

    async def scrape(self) -> list[dict]:
        results = []
        for show_type in (3,):  # 3 = 展览/演出
            for page in range(0, 5):
                raw = await self.fetch(
                    "/filtermain/films",
                    params={"showType": show_type, "offset": page * 30, "limit": 30},
                )
                data = self.parse(raw)
                if not data:
                    break
                results.extend(data)
        return results

    def parse(self, raw: str) -> list[dict]:
        sel = Selector(text=raw)
        items = []
        for el in sel.css(".movie-item, .film-item, .event-item"):
            title = el.css(".movie-title::text, .film-title::text, .title::text").get()
            link = el.css("a::attr(href)").get()
            img = el.css("img::attr(src)").get()
            if title:
                items.append({
                    "title": title.strip(),
                    "url": f"{self.base_url}{link}" if link else "",
                    "image": img or "",
                })
        return items
