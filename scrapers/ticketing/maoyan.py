import json
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
        # Try JSON first (API may return structured data)
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "data" in data:
                items = []
                for film in (data.get("data", {}).get("films") or data.get("data", {}).get("movies") or []):
                    items.append({
                        "title": str(film.get("nm") or film.get("name") or "").strip(),
                        "url": f"{self.base_url}/film/{film.get('id', '')}" if film.get("id") else "",
                        "image": str(film.get("img") or ""),
                        "category": str(film.get("cat") or ""),
                        "venue": str(film.get("venueName") or film.get("addr") or ""),
                        "city": str(film.get("cityName") or film.get("city") or ""),
                        "startDate": str(film.get("rt") or film.get("showDate") or ""),
                        "priceRange": str(film.get("priceRange") or film.get("sells") or ""),
                    })
                return items
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: HTML parse
        sel = Selector(text=raw)
        items = []
        for el in sel.css(".movie-item, .film-item, .event-item, .movie-item-hover, .movie-card"):
            title = el.css(".movie-title::text, .film-title::text, .title::text, .name::text").get()
            link = el.css("a::attr(href)").get()
            img = el.css("img::attr(src)").get()
            venue = el.css(".venue::text, .addr::text, .cinema-name::text").get()
            city = el.css(".city::text, .area::text").get()
            date = el.css(".date::text, .show-date::text, .release-date::text").get()
            price = el.css(".price::text, .score::text").get()
            if title:
                items.append({
                    "title": title.strip(),
                    "url": f"{self.base_url}{link}" if link else "",
                    "image": img or "",
                    "venue": venue.strip() if venue else "",
                    "city": city.strip() if city else "",
                    "startDate": date.strip() if date else "",
                    "priceRange": price.strip() if price else "",
                })
        return items
