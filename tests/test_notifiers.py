from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notifiers.bark import send as bark_send
from notifiers.serverchan import send as sc_send


@pytest.mark.asyncio
async def test_bark_sends_when_url_configured(monkeypatch):
    monkeypatch.setattr("notifiers.bark.NOTIFIERS", {"bark": {"url": "https://bark.example.com/token"}})
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response
    mock_ac = MagicMock()
    mock_ac.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ac.__aexit__ = AsyncMock(return_value=None)
    with patch("notifiers.bark.httpx.AsyncClient", return_value=mock_ac):
        result = await bark_send("hello")
        assert result is True


@pytest.mark.asyncio
async def test_bark_returns_false_when_url_empty(monkeypatch):
    monkeypatch.setattr("notifiers.bark.NOTIFIERS", {"bark": {"url": ""}})
    result = await bark_send("hello")
    assert result is False


@pytest.mark.asyncio
async def test_bark_returns_false_on_exception(monkeypatch):
    monkeypatch.setattr("notifiers.bark.NOTIFIERS", {"bark": {"url": "https://bark.example.com/token"}})
    with patch("notifiers.bark.httpx.AsyncClient", side_effect=Exception("network error")):
        result = await bark_send("hello")
        assert result is False


@pytest.mark.asyncio
async def test_serverchan_sends_when_key_configured(monkeypatch):
    monkeypatch.setattr("notifiers.serverchan.NOTIFIERS", {"serverchan": {"key": "SCKEY123"}})
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response
    mock_ac = MagicMock()
    mock_ac.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ac.__aexit__ = AsyncMock(return_value=None)
    with patch("notifiers.serverchan.httpx.AsyncClient", return_value=mock_ac):
        result = await sc_send("hello")
        assert result is True


@pytest.mark.asyncio
async def test_serverchan_returns_false_when_key_empty(monkeypatch):
    monkeypatch.setattr("notifiers.serverchan.NOTIFIERS", {"serverchan": {"key": ""}})
    result = await sc_send("hello")
    assert result is False


@pytest.mark.asyncio
async def test_serverchan_returns_false_on_exception(monkeypatch):
    monkeypatch.setattr("notifiers.serverchan.NOTIFIERS", {"serverchan": {"key": "SCKEY123"}})
    with patch("notifiers.serverchan.httpx.AsyncClient", side_effect=Exception("network error")):
        result = await sc_send("hello")
        assert result is False
