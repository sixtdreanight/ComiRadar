import pytest
from pipeline.normalizer import (
    _normalize_city,
    _parse_date,
    _guess_category,
    _parse_tlabel,
    _format_price,
)


def test_normalize_city_strips_shi():
    assert _normalize_city("上海市") == "上海"
    assert _normalize_city("北京市") == "北京"
    assert _normalize_city("广州") == "广州"


def test_normalize_city_china_aliases():
    assert _normalize_city("中国") == ""
    assert _normalize_city("全国") == ""


def test_normalize_city_strips_spaces():
    assert _normalize_city("  成都  ") == "成都"


def test_parse_date_iso():
    assert _parse_date("2026-05-20") == "2026-05-20"


def test_parse_date_slashed_falls_through():
    ret = _parse_date("2026/05/20")
    # Falls through to s[:10] when format doesn't match
    assert len(ret) == 10


def test_parse_date_dotted_falls_through():
    ret = _parse_date("2026.05.20")
    assert len(ret) == 10


def test_parse_date_with_time():
    assert _parse_date("2026-05-20 14:30:00") == "2026-05-20"


def test_parse_date_empty():
    from datetime import datetime
    assert _parse_date("") == datetime.now().strftime("%Y-%m-%d")


@pytest.mark.parametrize("title,expected", [
    ("上海COMICUP漫展", "漫展"),
    ("某同人展2026", "同人展"),
    ("初音未来演唱会", "演唱会"),
    ("xxx cosplay party", "漫展"),
    ("动漫嘉年华", "漫展"),
    ("主题咖啡馆快闪", "展览"),
    ("某音乐节2026", "演唱会"),
    ("某画展回顾", "展览"),
    ("ONLY同人祭", "同人展"),
    ("科幻展览活动", "展览"),
    ("地下偶像live", "演唱会"),
    ("不明主题", "其他"),
])
def test_guess_category(title, expected):
    assert _guess_category(title) == expected


def test_parse_tlabel_single():
    start, end = _parse_tlabel("2026.05.04")
    assert start == "2026-05-04"
    assert end is None


def test_parse_tlabel_range():
    start, end = _parse_tlabel("2026.05.03 - 05.05")
    assert start == "2026-05-03"
    assert end is not None
    assert "05-05" in end


def test_parse_tlabel_empty():
    start, end = _parse_tlabel("")
    assert start == ""
    assert end is None


def test_format_price_range():
    assert _format_price(88, 188) == "¥88-188"


def test_format_price_single_min():
    assert _format_price(88, 0) == "¥88起"


def test_format_price_single():
    assert _format_price(None, 188) == "¥188"


def test_format_price_none():
    assert _format_price(None, None) == "待定"
