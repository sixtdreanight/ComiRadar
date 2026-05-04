import json
from scrapers.base import SocialScraper


class WeiboScraper(SocialScraper):
    platform = "weibo"
    base_url = "https://m.weibo.cn"
    rate_limit = 3.0

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "同人展", "ComiCup", "CP展", "二次元展会"]
        for kw in keywords:
            data = await self.search(kw)
            results.extend(data)
        return results

    async def search(self, keyword: str) -> list[dict]:
        raw = await self.fetch(
            "/api/container/getIndex",
            params={"containerid": f"100103type=1&q={keyword}", "page": 1},
            headers={"Referer": "https://m.weibo.cn/"},
        )
        return self.parse(raw)

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            cards = obj.get("data", {}).get("cards", [])
            items = []
            for card in cards:
                if card.get("card_type") != 9:
                    continue
                mblog = card.get("mblog", {})
                text = mblog.get("text", "")
                created = mblog.get("created_at", "")
                user = mblog.get("user", {})
                items.append({
                    "text": _strip_html(text),
                    "date": created,
                    "user": user.get("screen_name", ""),
                    "url": f"https://m.weibo.cn/detail/{mblog.get('id', '')}",
                    "images": [p.get("url", "") for p in mblog.get("pics", [])],
                })
            return items
        except (json.JSONDecodeError, KeyError):
            return []


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text)
