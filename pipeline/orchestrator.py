import asyncio
from datetime import datetime
from db.store import get_session, upsert_event, get_all_events
from scrapers.base import AbstractScraper, TicketingScraper, SocialScraper
from pipeline.dedup import deduplicate, make_fingerprint


class Orchestrator:
    def __init__(self):
        self.session = get_session()

    async def scrape_all(self):
        await self.scrape_ticketing()
        await self.scrape_social()
        self._dedup_all()
        self.session.commit()

    async def scrape_ticketing(self):
        scrapers = [
            s for s in AbstractScraper._registry.values()
            if issubclass(s, TicketingScraper)
        ]
        await self._run_ticketing(scrapers)

    async def scrape_social(self):
        scrapers = [
            s for s in AbstractScraper._registry.values()
            if issubclass(s, SocialScraper)
        ]
        await self._run_social(scrapers)

    async def _run_ticketing(self, scraper_classes):
        from pipeline.normalizer import normalize
        for cls in scraper_classes:
            try:
                scraper = cls()
                raw = await scraper.scrape()
                events = normalize(cls.platform, raw)
                for e in events:
                    e.fingerprint = make_fingerprint(e)
                    upsert_event(self.session, e)
                print(f"[{cls.platform}] {len(events)} events")
            except Exception as exc:
                print(f"[{cls.platform}] failed: {exc}")
            finally:
                await asyncio.sleep(1)

    async def _run_social(self, scraper_classes):
        from pipeline.extractor import extract_events
        for cls in scraper_classes:
            try:
                scraper = cls()
                raw = await scraper.scrape()
                events = extract_events(cls.platform, raw)
                for e in events:
                    e.fingerprint = make_fingerprint(e)
                    upsert_event(self.session, e)
                print(f"[{cls.platform}] {len(events)} events")
            except Exception as exc:
                print(f"[{cls.platform}] failed: {exc}")
            finally:
                await asyncio.sleep(1)

    def _dedup_all(self):
        events = get_all_events(self.session)
        merged = deduplicate(events)
        for e in merged:
            upsert_event(self.session, e)
        self.session.commit()
        print(f"Dedup: {len(events)} -> {len(merged)}")

    async def check_and_notify(self):
        events = get_all_events(self.session)
        upcoming = [e for e in events if e.start_date >= datetime.now().strftime("%Y-%m-%d")]
        new_events = [e for e in upcoming if e.status in ("售票中", "即将开票")]
        if not new_events:
            return
        msg = "\n".join(
            f"• {e.title} | {e.city} | {e.start_date} | {e.price_range or '待定'}"
            for e in new_events[:5]
        )
        await self._notify_all(msg)

    async def _notify_all(self, message: str):
        from notifiers.serverchan import send as sc_send
        from notifiers.bark import send as bk_send
        await sc_send(message)
        await bk_send(message)
