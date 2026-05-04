import argparse
import asyncio
import json
from config import EXPORT_PATH


async def cmd_scrape(args):
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator()
    if args.target == "all":
        await orch.scrape_all()
    elif args.target == "ticketing":
        await orch.scrape_ticketing()
    elif args.target == "social":
        await orch.scrape_social()


def cmd_export(args):
    from db.store import get_session, get_all_events
    session = get_session()
    try:
        events = get_all_events(session)
        data = [_event_to_dict(e) for e in events]
        with open(EXPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(data)} events to {EXPORT_PATH}")
    finally:
        session.close()


def cmd_notify(args):
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator()
    asyncio.run(orch.check_and_notify())


def cmd_run(args):
    asyncio.run(cmd_scrape(argparse.Namespace(target="all")))
    cmd_export(None)
    cmd_notify(None)


def _event_to_dict(event) -> dict:
    return {
        "id": event.id,
        "sourceType": event.source_type,
        "sourceName": event.source_name,
        "title": event.title,
        "category": event.category,
        "city": event.city,
        "venue": event.venue,
        "startDate": event.start_date,
        "endDate": event.end_date,
        "priceRange": event.price_range,
        "ticketUrl": event.ticket_url,
        "imageUrl": event.image_url,
        "status": event.status,
        "confidence": event.confidence,
        "canonicalId": event.canonical_id,
        "scrapedAt": event.scraped_at,
    }


def main():
    parser = argparse.ArgumentParser(prog="anime-scraper")
    sub = parser.add_subparsers(dest="command")

    scrape_p = sub.add_parser("scrape")
    scrape_p.add_argument("target", nargs="?", default="all", choices=["all", "ticketing", "social"])

    sub.add_parser("export")
    sub.add_parser("notify")
    sub.add_parser("run")

    args = parser.parse_args()
    if args.command == "scrape":
        asyncio.run(cmd_scrape(args))
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "notify":
        cmd_notify(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
