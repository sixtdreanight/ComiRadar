import tempfile
import os
import pytest
from db.schema import EventModel, EventRecord, Base, create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield engine, session
    session.close()
    engine.dispose()
    os.unlink(path)


def test_event_model_creation():
    event = EventModel(
        id="test-1",
        source_type="ticketing",
        source_name="bilibili",
        title="CP2026",
        start_date="2026-06-01",
    )
    assert event.id == "test-1"
    assert event.source_type == "ticketing"


def test_event_model_defaults():
    event = EventModel(
        id="test-1",
        source_type="social",
        source_name="weibo",
        title="某活动",
        start_date="2026-06-01",
    )
    assert event.category == ""
    assert event.city == ""
    assert event.status == "预告"
    assert event.confidence == 1.0


def test_event_record_persist(tmp_db):
    engine, session = tmp_db
    record = EventRecord(
        id="persist-1",
        source_type="ticketing",
        source_name="bilibili",
        source_id="123",
        title="CP2026",
        city="上海",
        start_date="2026-06-01",
    )
    session.add(record)
    session.commit()

    fetched = session.get(EventRecord, "persist-1")
    assert fetched is not None
    assert fetched.title == "CP2026"
    assert fetched.city == "上海"


def test_event_upsert_new(tmp_db):
    from db.store import upsert_event
    engine, session = tmp_db
    event = EventModel(
        id="upsert-1",
        source_type="ticketing",
        source_name="bilibili",
        title="New Event",
        start_date="2026-07-01",
    )
    is_new = upsert_event(session, event)
    session.commit()
    assert is_new


def test_event_upsert_update(tmp_db):
    from db.store import upsert_event
    engine, session = tmp_db
    event = EventModel(
        id="upsert-2",
        source_type="ticketing",
        source_name="bilibili",
        title="Original Title",
        start_date="2026-07-01",
    )
    upsert_event(session, event)
    session.commit()

    event.title = "Updated Title"
    event.venue = "New Venue"
    is_new = upsert_event(session, event)
    session.commit()
    assert not is_new

    fetched = session.get(EventRecord, "upsert-2")
    assert fetched.title == "Updated Title"
    assert fetched.venue == "New Venue"
