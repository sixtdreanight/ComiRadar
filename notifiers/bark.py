import httpx
from config import NOTIFIERS


async def send(message: str) -> bool:
    url = NOTIFIERS.get("bark", {}).get("url", "")
    if not url:
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{url}/{message}")
            return resp.status_code == 200
    except Exception:
        return False
