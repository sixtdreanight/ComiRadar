import asyncio
import json
import sys
from scrapers.base import TicketingScraper
from config import BILIBILI_COOKIES


class BilibiliScraper(TicketingScraper):
    platform = "bilibili"
    base_url = "https://show.bilibili.com"
    rate_limit = 1.5
    cookies = BILIBILI_COOKIES

    async def scrape(self) -> list[dict]:
        results = []
        for project_type in (1, 2, 3, 4):
            page = 1
            while page <= 10:
                raw = await self.fetch(
                    "/api/ticket/project/listV2",
                    params={
                        "version": "134", "page": page, "pagesize": 50,
                        "project_type": project_type, "platform": "web",
                        "area": "0", "p_type": str(project_type),
                    },
                )
                data = self.parse(raw)
                if page == 1:
                    print(f"  [bilibili] type={project_type}: {len(data)} events", file=sys.stderr)
                if not data:
                    break
                results.extend(data)
                if len(data) < 50:
                    break
                page += 1
        return await self._enrich(results)

    async def _enrich(self, items: list[dict]) -> list[dict]:
        enriched = []
        for item in items:
            pid = item.get("id")
            if not pid:
                continue
            try:
                detail = await self._get_detail(pid)
                if detail:
                    item["_detail"] = detail
                else:
                    item["_detail"] = {}
            except Exception:
                item["_detail"] = {}
            enriched.append(item)
            await asyncio.sleep(0.5)
        return enriched

    async def _get_detail(self, pid: int) -> dict | None:
        try:
            raw = await self.fetch(
                "/api/ticket/project/get",
                params={"version": "134", "id": pid, "platform": "web"},
            )
            obj = json.loads(raw)
            if obj.get("errno") == 0:
                return obj.get("data", {})
        except Exception:
            pass
        return None

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            if obj.get("errno") != 0:
                print(f"  [bilibili] errno={obj.get('errno')} msg={obj.get('msg','')}", file=sys.stderr)
                return []
            return obj.get("data", {}).get("result", []) or []
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [bilibili] parse error: {e}", file=sys.stderr)
            return []
