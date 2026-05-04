import time
from collections import defaultdict

_failures: dict[str, list[float]] = defaultdict(list)
_disabled_until: dict[str, float] = {}

MAX_FAILURES = 3
COOLDOWN_HOURS = 24


def record_success(platform: str):
    _failures[platform].clear()


def record_failure(platform: str) -> bool:
    """Returns True if the scraper should be disabled."""
    now = time.time()
    _failures[platform] = [t for t in _failures[platform] if now - t < COOLDOWN_HOURS * 3600]
    _failures[platform].append(now)
    if len(_failures[platform]) >= MAX_FAILURES:
        _disabled_until[platform] = now + COOLDOWN_HOURS * 3600
        return True
    return False


def is_enabled(platform: str) -> bool:
    if platform not in _disabled_until:
        return True
    if time.time() > _disabled_until[platform]:
        del _disabled_until[platform]
        _failures[platform].clear()
        return True
    return False


def stats() -> dict:
    return {
        "disabled": dict(_disabled_until),
        "failures": {k: len(v) for k, v in _failures.items()},
    }
