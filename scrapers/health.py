import json
import time
from collections import defaultdict

from config import HEALTH_PATH

_failures: dict[str, list[float]] = defaultdict(list)
_disabled_until: dict[str, float] = {}

MAX_FAILURES = 3
COOLDOWN_HOURS = 24


def _load_state() -> None:
    """Restore health state from disk on module load."""
    global _failures, _disabled_until
    try:
        if HEALTH_PATH.exists():
            data = json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
            _failures = defaultdict(list, {k: v for k, v in data.get("failures", {}).items()})
            _disabled_until = data.get("disabled", {})
            # Purge expired entries on load
            _purge_expired()
    except (json.JSONDecodeError, OSError):
        pass


def _save_state() -> None:
    """Persist health state to disk (best-effort)."""
    try:
        HEALTH_PATH.write_text(
            json.dumps({"failures": dict(_failures), "disabled": _disabled_until}),
            encoding="utf-8",
        )
    except OSError:
        pass


def _purge_expired() -> None:
    now = time.time()
    for platform in list(_disabled_until):
        if now > _disabled_until[platform]:
            del _disabled_until[platform]
            _failures[platform].clear()
    for platform in list(_failures):
        _failures[platform] = [t for t in _failures[platform] if now - t < COOLDOWN_HOURS * 3600]
        if not _failures[platform]:
            del _failures[platform]


def record_success(platform: str):
    _failures[platform].clear()
    _save_state()


def record_failure(platform: str) -> bool:
    """Returns True if the scraper should be disabled."""
    now = time.time()
    _failures[platform] = [t for t in _failures[platform] if now - t < COOLDOWN_HOURS * 3600]
    _failures[platform].append(now)
    if len(_failures[platform]) >= MAX_FAILURES:
        _disabled_until[platform] = now + COOLDOWN_HOURS * 3600
        _save_state()
        return True
    _save_state()
    return False


def is_enabled(platform: str) -> bool:
    if platform not in _disabled_until:
        return True
    if time.time() > _disabled_until[platform]:
        del _disabled_until[platform]
        _failures[platform].clear()
        _save_state()
        return True
    return False


def stats() -> dict:
    return {
        "disabled": dict(_disabled_until),
        "failures": {k: len(v) for k, v in _failures.items()},
    }


# Restore state when the module is first imported
_load_state()
