from datetime import datetime, timezone
from pydantic import BaseModel as PydanticBase
from sqlalchemy import Column, String, Float, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from config import DB_PATH


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    start_date: str = Column(String, nullable=False)
    end_date: str | None = Column(String, nullable=True)
    price_range: str | None = Column(String, nullable=True)
    ticket_url: str | None = Column(String, nullable=True)
    image_url: str | None = Column(String, nullable=True)
    status: str = Column(String, default="预告")
    confidence: float = Column(Float, default=1.0)
    fingerprint: str | None = Column(String, nullable=True)
    canonical_id: str | None = Column(String, nullable=True)
    scraped_at: datetime = Column(DateTime, default=_utcnow)


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
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
