import httpx
from config import NOTIFIERS


async def send(message: str) -> bool:
    key = NOTIFIERS.get("serverchan", {}).get("key", "")
    if not key:
        return False
    try:
        async with httpx.AsyncClient(verify=True) as client:
            resp = await client.post(
                "https://sctapi.ftqq.com/send",
                data={"sendkey": key, "title": "演出更新", "desp": message},
            )
            return resp.status_code == 200
    except Exception:
        return False
