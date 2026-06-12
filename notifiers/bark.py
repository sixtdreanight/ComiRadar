from urllib.parse import quote

import httpx

from config import NOTIFIERS


async def send(message: str) -> bool:
    url = NOTIFIERS.get("bark", {}).get("url", "")
    if not url:
        return False
    try:
        async with httpx.AsyncClient(verify=True) as client:
            resp = await client.get(f"{url}/{quote(message, safe='')}")
            return resp.status_code == 200
    except Exception:
        return False
