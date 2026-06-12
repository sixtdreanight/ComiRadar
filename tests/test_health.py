import os
import tempfile
import time

import pytest


@pytest.fixture(autouse=True)
def isolated_health(monkeypatch):
    """Use a temp file for health state, reset globals after each test."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    monkeypatch.setattr("scrapers.health.HEALTH_PATH", type("P", (), {"exists": lambda: False, "write_text": lambda *a, **kw: None, "read_text": lambda *a, **kw: "{}"})())
    monkeypatch.setattr("scrapers.health._save_state", lambda: None)
    monkeypatch.setattr("scrapers.health._load_state", lambda: None)
    # Reset module state
    import scrapers.health as h
    h._failures.clear()
    h._disabled_until.clear()
    yield
    h._failures.clear()
    h._disabled_until.clear()


def test_record_success_clears_failures():
    from scrapers.health import record_failure, record_success
    record_failure("test_platform")
    record_failure("test_platform")
    assert len(record_failure.__globals__["_failures"]["test_platform"]) == 2
    record_success("test_platform")
    assert len(record_failure.__globals__["_failures"]["test_platform"]) == 0


def test_record_failure_returns_false_below_threshold():
    from scrapers.health import record_failure, record_success
    record_success("pf")
    assert not record_failure("pf")
    assert not record_failure("pf")


def test_record_failure_disables_after_max():
    from scrapers.health import MAX_FAILURES, is_enabled, record_failure, record_success
    record_success("pf2")
    for _ in range(MAX_FAILURES - 1):
        assert not record_failure("pf2")
    assert record_failure("pf2")
    assert not is_enabled("pf2")


def test_is_enabled_unknown_platform():
    from scrapers.health import is_enabled
    assert is_enabled("nonexistent")


def test_disabled_platform_auto_recovers():
    from scrapers.health import MAX_FAILURES, is_enabled, record_failure
    for _ in range(MAX_FAILURES):
        record_failure("pf3")
    assert not is_enabled("pf3")
    # Simulate cooldown expiry
    import scrapers.health as h
    h._disabled_until["pf3"] = time.time() - 1
    assert is_enabled("pf3")


def test_stats_returns_dict():
    from scrapers.health import stats
    s = stats()
    assert "disabled" in s
    assert "failures" in s
    assert isinstance(s["disabled"], dict)
    assert isinstance(s["failures"], dict)


def test_old_failures_are_pruned():
    from scrapers.health import record_failure, record_success
    record_success("pf4")
    import scrapers.health as h
    h._failures["pf4"] = [time.time() - 100000]
    assert not record_failure("pf4")  # First call prunes old ones, adds new


def test_multiple_platforms_independent():
    from scrapers.health import MAX_FAILURES, is_enabled, record_failure, record_success
    record_success("a")
    record_success("b")
    for _ in range(MAX_FAILURES):
        record_failure("a")
    assert not is_enabled("a")
    assert is_enabled("b")
