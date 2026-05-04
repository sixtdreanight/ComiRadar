"""Playwright worker for platforms with anti-bot JS protections."""
import asyncio
import json
import sys
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


async def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["weibo"]
    all_results = []
    for platform in args:
        if platform == "weibo":
            items = await scrape_weibo()
            all_results.extend(items)
        elif platform == "showstart":
            items = await scrape_showstart()
            all_results.extend(items)
    print(json.dumps(all_results, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
