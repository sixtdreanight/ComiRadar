"""CIEFC 漫展信息抓取 worker — Playwright 浏览器自动化"""
import asyncio
import json
import re

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto("https://www.ciefc.com/cg/zhpq/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        text = await page.evaluate("document.body.innerText")
        await browser.close()

    results = []
    for line in text.split("\n"):
        line = line.strip()
        m = re.search(
            r"(.+?博览[会展]|.+?动漫[节展].+?|.+?游戏[节展].+?|Ani[-\s]?Expo[^\t]*).*?(\d{4}-\d{1,2}-\d{1,2})",
            line,
        )
        if m:
            d = m.group(2)
            parts = d.split("-")
            if len(parts) == 3:
                d = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            results.append({
                "title": m.group(1).strip()[:100],
                "date": d,
                "city": "广州",
                "venue": "广交会展馆",
            })

    print(json.dumps(results, ensure_ascii=False))


asyncio.run(main())
