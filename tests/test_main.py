import json
from unittest.mock import MagicMock, patch


def test_sanitize_str_removes_scripts():
    from main import _sanitize_str
    assert "<script>" not in _sanitize_str('<script>alert("x")</script>hello')
    assert "hello" in _sanitize_str('<script>alert("x")</script>hello')


def test_sanitize_str_removes_html_tags():
    from main import _sanitize_str
    assert "<b>" not in _sanitize_str("<b>bold</b>text")
    assert "boldtext" in _sanitize_str("<b>bold</b>text")


def test_sanitize_event_cleans_fields():
    from main import _sanitize_event
    event = {
        "title": '<script>evil</script>漫展',
        "venue": "<b>上海</b>",
        "category": "<i>漫展</i>",
        "city": "<span>北京</span>",
        "other": "<keep>this</keep>",
    }
    cleaned = _sanitize_event(event)
    assert "<script>" not in cleaned["title"]
    assert cleaned["title"] == "漫展"
    assert cleaned["venue"] == "上海"
    assert cleaned["category"] == "漫展"
    assert cleaned["city"] == "北京"


def test_event_to_dict():
    from db.schema import EventModel
    from main import _event_to_dict
    event = EventModel(
        id="ev-1", source_type="ticketing", source_name="bilibili",
        title="Test", start_date="2026-06-01", confidence=1.0,
    )
    d = _event_to_dict(event)
    assert d["id"] == "ev-1"
    assert d["title"] == "Test"
    assert d["sourceType"] == "ticketing"
    assert d["sourceName"] == "bilibili"
    assert d["confidence"] == 1.0
    assert d["canonicalId"] is None


def test_cmd_export_filters_expired_events(tmp_path, monkeypatch):
    from datetime import date, timedelta

    from db.schema import EventModel
    from main import cmd_export

    past = (date.today() - timedelta(days=30)).isoformat()
    future = (date.today() + timedelta(days=30)).isoformat()

    active_event = EventModel(
        id="active", source_type="ticketing", source_name="bilibili",
        title="Active Event", city="上海", start_date=future,
        end_date=future, status="售票中", confidence=1.0,
    )
    past_event = EventModel(
        id="past", source_type="ticketing", source_name="bilibili",
        title="Past Event", city="上海", start_date=past,
        end_date=past, status="已结束", confidence=1.0,
    )

    export_file = tmp_path / "events.json"
    monkeypatch.setattr("main.EXPORT_PATH", export_file)
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)

    with patch("db.store.get_session", return_value=mock_session), \
         patch("db.store.get_all_events", return_value=[active_event, past_event]):
        cmd_export(None)
        data = json.loads(export_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["id"] == "active"


def test_cmd_export_assumes_7_day_run_for_missing_end_date(tmp_path, monkeypatch):
    from datetime import date

    from db.schema import EventModel
    from main import cmd_export

    today = date.today().isoformat()
    event = EventModel(
        id="noend", source_type="ticketing", source_name="bilibili",
        title="No End Date", city="上海", start_date=today,
        status="售票中", confidence=1.0,
    )
    export_file = tmp_path / "events.json"
    monkeypatch.setattr("main.EXPORT_PATH", export_file)
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)

    with patch("db.store.get_session", return_value=mock_session), \
         patch("db.store.get_all_events", return_value=[event]):
        cmd_export(None)
        data = json.loads(export_file.read_text(encoding="utf-8"))
        assert len(data) == 1


def test_cmd_stats_prints(monkeypatch):
    from main import cmd_stats

    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)

    with patch("db.store.get_session", return_value=mock_session), \
         patch("db.store.get_all_events", return_value=[]), \
         patch("pipeline.orchestrator.health_stats", return_value={"disabled": {}, "failures": {}}):
        cmd_stats(None)
        # Should complete without error


def test_cmd_export_skips_empty_start_date():
    from db.schema import EventModel
    from main import cmd_export

    event = EventModel(
        id="nostart", source_type="ticketing", source_name="bilibili",
        title="No Start Date", city="上海", start_date="", status="售票中",
    )
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)

    with patch("db.store.get_session", return_value=mock_session), \
         patch("db.store.get_all_events", return_value=[event]):
        cmd_export(None)
        # Event with no start_date is skipped


def test_cli_help(capsys):
    from main import main as main_fn
    with patch("sys.argv", ["anime-scraper"]):
        try:
            main_fn()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "scrape" in captured.out or "scrape" in captured.err
