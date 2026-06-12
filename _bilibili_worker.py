"""Standalone worker for B站 scraping, runs in subprocess to avoid module conflicts."""
import asyncio
import json
import random
import sys

import httpx

from config import BILIBILI_COOKIES, UA_POOL


async def main():
    cookies = {k: v for k, v in BILIBILI_COOKIES.items() if v}
    results = []
    for project_type in (1, 2, 3, 4):
        items = await _fetch_list(cookies, project_type)
        print(f"  [bilibili] type={project_type}: {len(items)} events", file=sys.stderr)
        results.extend(items)
        await asyncio.sleep(1.5)
    # Enrich first 10 with detail API for names/prices
    for item in results[:10]:
        pid = item.get("id")
        if pid:
            try:
                detail = await _fetch_detail(cookies, pid)
                item["_detail"] = detail
            except Exception:
                item["_detail"] = {}
        await asyncio.sleep(0.2)
    print(json.dumps(results, ensure_ascii=False))


async def _fetch_list(cookies: dict, project_type: int) -> list[dict]:
    items = []
    page = 1
    max_pages = 10
    while page <= max_pages:
        async with httpx.AsyncClient(
            cookies=cookies or None, timeout=30,
            headers={
                "User-Agent": random.choice(UA_POOL),
                "Accept": "application/json, text/html",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://show.bilibili.com/",
            },
            follow_redirects=True,
        ) as client:
            r = await client.get(
                "https://show.bilibili.com/api/ticket/project/listV2",
                params={
                    "version": "134", "page": page, "pagesize": 20,
                    "project_type": project_type, "platform": "web",
                    "area": "0", "p_type": str(project_type),
                },
            )
            obj = json.loads(r.text)
            if obj.get("errno") != 0:
                break
            data = obj.get("data", {})
            page_items = data.get("result", []) or []
            for it in page_items:
                if not it.get("project_type"):
                    it["project_type"] = project_type
            items.extend(page_items)
            if page == 1:
                total = data.get("total", 0) or 0
                pagesize = data.get("pagesize", 20)
                if total:
                    max_pages = min((total + pagesize - 1) // pagesize, 10)
            if len(page_items) < 20:
                break
            page += 1
        await asyncio.sleep(1)
    return items


async def _fetch_detail(cookies: dict, pid: int) -> dict:
    async with httpx.AsyncClient(
        cookies=cookies or None, timeout=15,
        headers={
            "User-Agent": random.choice(UA_POOL),
            "Referer": "https://show.bilibili.com/",
        },
        follow_redirects=True,
    ) as client:
        r = await client.get(
            "https://show.bilibili.com/api/ticket/project/get",
            params={"version": "134", "id": pid, "platform": "web"},
        )
        obj = json.loads(r.text)
        return obj.get("data", {}) if obj.get("errno") == 0 else {}


if __name__ == "__main__":
    asyncio.run(main())
