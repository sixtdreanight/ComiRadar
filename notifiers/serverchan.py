import httpx
from config import NOTIFIERS


async def send(message: str) -> bool:
    key = NOTIFIERS.get("serverchan", {}).get("key", "")
    if not key:
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://sctapi.ftqq.com/{key}.send",
                data={"title": "演出更新", "desp": message},
            )
            return resp.status_code == 200
    except Exception:
        return False
