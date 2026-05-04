import json
from scrapers.base import SocialScraper


class BilibiliDynamicScraper(SocialScraper):
    platform = "bilibili_dynamic"
    base_url = "https://api.bilibili.com"
    rate_limit = 2.0

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "同人展", "ComiCup", "CP展", "二次元展会"]
        for kw in keywords:
            data = await self.search(kw)
            results.extend(data)
        return results

    async def search(self, keyword: str) -> list[dict]:
        raw = await self.fetch(
            "/x/web-interface/search/type",
            params={"search_type": "dynamic", "keyword": keyword, "page": 1},
            headers={"Referer": "https://www.bilibili.com/"},
        )
        return self.parse(raw)

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            if obj.get("code") != 0:
                return []
            result = obj.get("data", {}).get("result", [])
            items = []
            for r in result:
                desc = r.get("description") or r.get("content") or ""
                items.append({
                    "text": desc,
                    "date": r.get("pubdate", ""),
                    "user": r.get("author", {}).get("name", ""),
                    "url": f"https://t.bilibili.com/{r.get('dynamic_id', '')}",
                })
            return items
        except (json.JSONDecodeError, KeyError):
            return []
