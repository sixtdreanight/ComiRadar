from scrapers.base import SocialScraper


class XiaohongshuScraper(SocialScraper):
    platform = "xiaohongshu"
    base_url = "https://www.xiaohongshu.com"
    rate_limit = 5.0

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "同人展", "二次元展会"]
        for kw in keywords:
            data = await self.search(kw)
            results.extend(data)
        return results

    async def search(self, keyword: str) -> list[dict]:
        # 小红书反爬较强，需要 Cookie 和代理
        # Web 版搜索接口
        raw = await self.fetch(
            "/api/search/notes",
            params={"keyword": keyword, "page": 1, "page_size": 20},
            headers={
                "Referer": "https://www.xiaohongshu.com/",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        return self.parse(raw)

    def parse(self, raw: str) -> list[dict]:
        import json
        try:
            obj = json.loads(raw)
            notes = obj.get("data", {}).get("notes", [])
            return [
                {
                    "text": n.get("display_title", ""),
                    "url": f"https://www.xiaohongshu.com/explore/{n.get('id', '')}",
                }
                for n in notes
            ]
        except (json.JSONDecodeError, KeyError):
            return []
