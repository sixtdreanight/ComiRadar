from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBase
from sqlalchemy import Column, DateTime, Float, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase

from config import DB_PATH


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"
    id: str = Column(String, primary_key=True)
    source_type: str = Column(String, nullable=False)
    source_name: str = Column(String, nullable=False)
    source_id: str = Column(String, nullable=False)
    title: str = Column(String, nullable=False)
    category: str = Column(String, default="")
    city: str = Column(String, default="")
    venue: str = Column(String, default="")
    start_date: str = Column(String, nullable=False, index=True)
    end_date: str | None = Column(String, nullable=True)
    price_range: str | None = Column(String, nullable=True)
    ticket_url: str | None = Column(String, nullable=True)
    image_url: str | None = Column(String, nullable=True)
    status: str = Column(String, default="预告")
    confidence: float = Column(Float, default=1.0)
    fingerprint: str | None = Column(String, nullable=True, index=True)
    canonical_id: str | None = Column(String, nullable=True)
    scraped_at: datetime = Column(DateTime, default=_utcnow, index=True)


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


Base.metadata.create_all(engine)


class EventModel(PydanticBase):
    id: str
    source_type: str
    source_name: str
    source_id: str = ""
    title: str
    category: str = ""
    city: str = ""
    venue: str = ""
    start_date: str
    end_date: str | None = None
    price_range: str | None = None
    ticket_url: str | None = None
    image_url: str | None = None
    status: str = "预告"
    confidence: float = 1.0
    fingerprint: str | None = None
    canonical_id: str | None = None
    scraped_at: str | None = None
