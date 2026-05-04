import json
import sys
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
                if page == 1:
                    print(f"  [bilibili] type={project_type}: {len(data)} events (page 1)", file=sys.stderr)
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
            errno = obj.get("errno", -1)
            if errno != 0:
                print(f"  [bilibili] API errno={errno} msg={obj.get('msg','')}", file=sys.stderr)
                return []
            result = obj.get("data", {}).get("result", []) or []
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [bilibili] parse error: {e}, raw[:100]={raw[:100]}", file=sys.stderr)
            return []
