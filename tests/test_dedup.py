from db.schema import EventModel
from pipeline.dedup import _normalize_title, deduplicate, make_fingerprint


def make_event(**kwargs) -> EventModel:
    defaults = {
        "id": "test-1",
        "source_type": "ticketing",
        "source_name": "bilibili",
        "title": "测试漫展",
        "category": "漫展",
        "city": "上海",
        "venue": "上海会展中心",
        "start_date": "2026-06-01",
    }
    defaults.update(kwargs)
    return EventModel(**defaults)


def test_normalize_title_removes_special_chars():
    t = _normalize_title("【CP2026】同人展！- 上海站")
    # brackets, ！, spaces, dashes all stripped
    assert "！" not in t
    assert "【" not in t
    assert "-" not in t


def test_normalize_title_aliases():
    t = _normalize_title("cp2026")
    assert "comicup" in t


def test_make_fingerprint_deterministic():
    a = make_event(id="a", title="CP2026", city="上海", start_date="2026-06-01")
    b = make_event(id="b", title="CP2026", city="上海", start_date="2026-06-01")
    assert make_fingerprint(a) == make_fingerprint(b)


def test_make_fingerprint_city_normalized():
    a = make_event(id="a", city="上海市")
    b = make_event(id="b", city="上海")
    assert make_fingerprint(a) == make_fingerprint(b)


def test_make_fingerprint_different_dates():
    a = make_event(id="a", start_date="2026-06-01")
    b = make_event(id="b", start_date="2026-06-02")
    assert make_fingerprint(a) != make_fingerprint(b)


def test_deduplicate_exact_match():
    a = make_event(id="bilibili_1", title="CP2026", city="上海", start_date="2026-06-01", confidence=1.0)
    b = make_event(id="damai_2", title="CP2026", city="上海", start_date="2026-06-01", confidence=0.8)
    result = deduplicate([a, b])
    assert len(result) == 1
    assert result[0].id == "bilibili_1"  # higher confidence kept


def test_deduplicate_different_cities():
    a = make_event(id="a", city="上海", start_date="2026-06-01")
    b = make_event(id="b", city="北京", start_date="2026-06-01")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_different_events():
    a = make_event(id="a", title="CP2026", city="上海", start_date="2026-06-01")
    b = make_event(id="b", title="BW2026", city="北京", start_date="2026-08-15")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_merges_source_names():
    a = make_event(id="bilibili_1", title="CP2026", city="上海", start_date="2026-06-01",
                   source_name="bilibili", confidence=1.0)
    b = make_event(id="damai_2", title="CP2026", city="上海", start_date="2026-06-01",
                   source_name="damai", confidence=0.9)
    result = deduplicate([a, b])
    assert len(result) == 1
    assert "bilibili" in result[0].source_name
    assert "damai" in result[0].source_name


def test_deduplicate_no_false_positive_different_titles_same_city():
    """确保完全不同的事件不会被误合并。"""
    a = make_event(id="a", title="BW2026", city="上海", start_date="2026-07-01")
    b = make_event(id="b", title="ChinaJoy2026", city="上海", start_date="2026-07-31")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_fuzzy_merge_within_3_days():
    """同一城市、相似标题、日期相差≤3天应被合并。"""
    a = make_event(id="bilibili", title="CP2026 同人展", city="上海", start_date="2026-06-01", confidence=1.0)
    b = make_event(id="damai", title="CP2026 漫展", city="上海", start_date="2026-06-03", confidence=0.8)
    result = deduplicate([a, b])
    assert len(result) == 1


def test_deduplicate_no_merge_outside_3_days():
    """日期相差>3天不合并。"""
    a = make_event(id="a", title="CP2026", city="上海", start_date="2026-06-01")
    b = make_event(id="b", title="CP2026", city="上海", start_date="2026-06-10")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_single_event_unchanged():
    result = deduplicate([make_event()])
    assert len(result) == 1


def test_deduplicate_empty_list():
    result = deduplicate([])
    assert result == []


def test_deduplicate_merge_fills_missing_fields():
    a = make_event(id="a", title="CP2026", city="上海", start_date="2026-06-01",
                   venue="", price_range=None, confidence=1.0)
    b = make_event(id="b", title="CP2026", city="上海", start_date="2026-06-01",
                   venue="上海会展中心", price_range="¥88-188", confidence=0.9)
    result = deduplicate([a, b])
    assert len(result) == 1
    assert result[0].venue == "上海会展中心"
    assert result[0].price_range == "¥88-188"
