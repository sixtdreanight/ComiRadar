"""Playwright worker for platforms with anti-bot JS protections."""
import asyncio
import json
import sys
from datetime import datetime
from playwright.async_api import async_playwright

KEYWORDS = ["漫展", "同人展", "二次元音乐会", "ACG演唱会", "动漫展", "动漫音乐会", "声优见面会", "地下偶像"]


async def scrape_weibo() -> list[dict]:
    """Scrape 微博 mobile search for event-related posts."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            viewport={"width": 390, "height": 844},
            locale="zh-CN",
        )
        page = await context.new_page()
        for keyword in KEYWORDS:
            try:
                encoded = "%E6%BC%AB%E5%B1%95"  # will be overridden
                await page.goto(
                    f"https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}",
                    wait_until="networkidle",
                    timeout=30000,
                )
                await page.wait_for_timeout(2000)
                posts = await page.evaluate("""() => {
                    const cards = document.querySelectorAll('.card-wrap, .card, [class*=card]');
                    return Array.from(cards).map(c => ({
                        text: c.textContent?.trim()?.substring(0, 500) || '',
                    })).filter(c => c.text.length > 20);
                }""")
                for post in posts:
                    post["_source"] = "weibo"
                    post["_keyword"] = keyword
                results.extend(posts)
                print(f"  [weibo] keyword={keyword}: {len(posts)} posts", file=sys.stderr)
            except Exception as e:
                print(f"  [weibo] {keyword}: {e}", file=sys.stderr)
        await browser.close()
    return results


async def scrape_showstart() -> list[dict]:
    """Scrape 秀动 — requires login cookies."""
    # 秀动 API requires login, skip for now
    return []


async def scrape_nyato() -> list[dict]:
    """Scrape 喵特 manzhan listings."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto("https://www.nyato.com/manzhan/p0", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(4000)
        events = await page.evaluate("""() => {
            const container = document.querySelector('.index-expolist');
            if (!container) return [];
            const items = [];
            const allDivs = container.querySelectorAll('div');
            let current = null;
            allDivs.forEach(div => {
                const text = div.textContent?.trim() || '';
                if (/^\\d+$/.test(text) && div.nextElementSibling) {
                    return; // rating number
                }
                if (text.length > 20 && text.length < 300 && /\\d{2}\\/\\d{2}/.test(text)) {
                    items.push({
                        text: text.replace(/\\s+/g, ' '),
                    });
                }
            });
            return items;
        }""")
        for e in events:
            parsed = _parse_nyato_card(e.get("text", ""))
            if parsed:
                parsed["_source"] = "nyato"
                results.append(parsed)
        await browser.close()
    print(f"  [nyato] {len(results)} events", file=sys.stderr)
    return results


def _parse_nyato_card(text: str) -> dict | None:
    import re
    # Strip leading rating number
    text = re.sub(r"^\d+\s+", "", text.strip())
    # Format: "NAME CITY MM/DD - MM/DD 地址：PROVINCE CITY DISTRICT VENUE 综合评分："
    m = re.match(r"(.+?)\s+(\S+?市?)\s+(\d{2}/\d{2})\s*-\s*(\d{2}/\d{2})\s*地址：(.+?)\s*综合评分", text)
    if not m:
        m = re.match(r"(.+?)\s+(\S+?市?)\s+(\d{2}/\d{2})\s*-\s*(\d{2}/\d{2})\s*地址：(.+)", text)
    if not m:
        return None
    name, city, d1, d2, addr = m.groups()
    year = datetime.now().year
    return {
        "title": name.strip(),
        "city": city.strip().rstrip("市"),
        "startDate": f"{year}-{d1.replace('/', '-')}",
        "endDate": f"{year}-{d2.replace('/', '-')}",
        "venue": addr.strip()[:100],
    }


async def scrape_chinajoy() -> list[dict]:
    """Scrape ChinaJoy official site."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto("https://www.chinajoy.net/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        text = await page.evaluate("document.body.innerText")
        await browser.close()
    results = []
    import re
    # Extract: "时间：2026.7/31-8/3" and "地点：上海新国际博览中心"
    date_m = re.search(r"时间[：:]\s*(\d{4})[./](\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})", text)
    venue_m = re.search(r"地点[：:]\s*(.+?)(?:\n|$)", text)
    name_m = re.search(r"第[一二三四五六七八九十\d]+届.+?(?:展览会|博览会|展会)", text)
    if date_m:
        y, m1, d1, m2, d2 = date_m.groups()
        results.append({
            "title": name_m.group(0) if name_m else "ChinaJoy 2026",
            "city": "上海",
            "startDate": f"{y}-{int(m1):02d}-{int(d1):02d}",
            "endDate": f"{y}-{int(m2):02d}-{int(d2):02d}",
            "venue": venue_m.group(1).strip() if venue_m else "上海新国际博览中心",
            "_source": "chinajoy",
        })
    print(f"  [chinajoy] {len(results)} events", file=sys.stderr)
    return results


async def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["weibo", "nyato"]
    all_results = []
    for platform in args:
        if platform == "weibo":
            items = await scrape_weibo()
            all_results.extend(items)
        elif platform == "nyato":
            items = await scrape_nyato()
            all_results.extend(items)
        elif platform == "chinajoy":
            items = await scrape_chinajoy()
            all_results.extend(items)
        elif platform == "showstart":
            items = await scrape_showstart()
            all_results.extend(items)
    print(json.dumps(all_results, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
