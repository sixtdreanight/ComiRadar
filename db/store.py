from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.schema import engine, EventRecord, EventModel


def get_session() -> Session:
    return Session(engine)


def upsert_event(session: Session, event: EventModel) -> bool:
    """Returns True if new, False if updated."""
    existing = session.get(EventRecord, event.id)
    record = EventRecord(**event.model_dump())
    if existing:
        if existing.scraped_at and record.scraped_at and datetime.fromisoformat(record.scraped_at) <= existing.scraped_at:
            session.merge(existing)
            return False
        record_dict = event.model_dump()
        for key, value in record_dict.items():
            setattr(existing, key, value)
        session.merge(existing)
        return False
    session.add(record)
    return True


def get_all_events(session: Session) -> list[EventModel]:
    stmt = select(EventRecord).order_by(EventRecord.start_date.asc())
    rows = session.execute(stmt).scalars().all()
    return [_row_to_model(r) for r in rows]


def get_events_by_fingerprint(session: Session, fp: str) -> list[EventModel]:
    stmt = select(EventRecord).where(EventRecord.fingerprint == fp)
    rows = session.execute(stmt).scalars().all()
    return [_row_to_model(r) for r in rows]


def _row_to_model(row: EventRecord) -> EventModel:
    return EventModel(
        id=row.id,
        source_type=row.source_type,
        source_name=row.source_name,
        source_id=row.source_id,
        title=row.title,
        category=row.category,
        city=row.city,
        venue=row.venue,
        start_date=row.start_date,
        end_date=row.end_date,
        price_range=row.price_range,
        ticket_url=row.ticket_url,
        image_url=row.image_url,
        status=row.status,
        confidence=row.confidence,
        fingerprint=row.fingerprint,
        canonical_id=row.canonical_id,
        scraped_at=row.scraped_at.isoformat() if row.scraped_at else None,
    )
