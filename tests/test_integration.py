import json
import os
import tempfile

import pytest

from db.schema import Base, EventModel, create_engine


@pytest.fixture
def temp_db(monkeypatch):
    """Create an isolated temp DB for integration tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr("config.DB_PATH", type("P", (), {"__fspath__": lambda s=path: s, "__str__": lambda s=path: s})())

    engine = create_engine(f"sqlite:///{path}", echo=False)
    Base.metadata.create_all(engine)

    import db.store as store_mod
    original_engine = store_mod.engine
    store_mod.engine = engine
    yield engine
    store_mod.engine = original_engine
    engine.dispose()
    os.unlink(path)


def test_full_pipeline_dedup_and_persist(temp_db):
    """Events go through normalize -> upsert -> dedup -> query."""
    from db.store import get_all_events, get_session, upsert_event
    from pipeline.dedup import deduplicate, make_fingerprint
    from pipeline.normalizer import normalize

    raw_bili = [{"id": 123, "name": "CP2026", "city": "上海市", "tlabel": "2026.06.01 - 06.02"}]
    raw_damai = [{"itemId": 456, "name": "CP2026漫展", "cityName": "上海", "showTime": "2026-06-01"}]

    bili_events = normalize("bilibili", raw_bili)
    damai_events = normalize("damai", raw_damai)

    assert len(bili_events) == 1
    assert len(damai_events) == 1

    session = get_session()
    try:
        for e in bili_events + damai_events:
            e.fingerprint = make_fingerprint(e)
            upsert_event(session, e)
        session.commit()

        all_events = get_all_events(session)
        assert len(all_events) == 2

        merged = deduplicate(all_events)
        assert len(merged) == 1
        assert "bilibili" in merged[0].source_name
        assert "damai" in merged[0].source_name
    finally:
        session.close()


def test_upsert_new_then_update(temp_db):
    from db.store import get_all_events, get_session, upsert_event

    event = EventModel(
        id="int-1", source_type="ticketing", source_name="bilibili",
        title="Original", city="上海", start_date="2026-06-01",
    )
    session = get_session()
    try:
        assert upsert_event(session, event)
        session.commit()

        event.title = "Updated"
        assert not upsert_event(session, event)
        session.commit()

        all_events = get_all_events(session)
        found = [e for e in all_events if e.id == "int-1"]
        assert len(found) == 1
        assert found[0].title == "Updated"
    finally:
        session.close()


def test_fingerprint_determinism_across_sessions(temp_db):
    from pipeline.dedup import make_fingerprint
    a = EventModel(id="a", title="CP2026", city="上海", start_date="2026-06-01", source_type="ticketing", source_name="bilibili")
    b = EventModel(id="b", title="CP2026", city="上海市", start_date="2026-06-01", source_type="ticketing", source_name="damai")
    assert make_fingerprint(a) == make_fingerprint(b)


def test_event_export_json_format(temp_db, tmp_path):
    """Simulate the full export flow: persist events, export to JSON, verify format."""
    from db.store import get_all_events, get_session, upsert_event
    from main import _event_to_dict, _sanitize_event

    event = EventModel(
        id="export-1", source_type="ticketing", source_name="bilibili",
        title="Test Event", category="漫展", city="上海", venue="会展中心",
        start_date="2026-06-01", end_date="2026-06-02",
        price_range="¥88-188", status="售票中", confidence=1.0,
    )
    session = get_session()
    try:
        upsert_event(session, event)
        session.commit()
        all_events = get_all_events(session)
        assert len(all_events) == 1

        data = [_sanitize_event(_event_to_dict(e)) for e in all_events]
        export_path = tmp_path / "events.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        loaded = json.loads(export_path.read_text(encoding="utf-8"))
        assert len(loaded) == 1
        assert loaded[0]["id"] == "export-1"
        assert loaded[0]["title"] == "Test Event"
        assert loaded[0]["sourceType"] == "ticketing"
    finally:
        session.close()
