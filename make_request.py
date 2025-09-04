import httpx
from config import API_BASE_URL


async def api_request(
    method: str,
    endpoint: str,
    params: dict | None = None,
    data: dict | None = None,
    timeout: float = 10.0
) -> tuple[int, dict | list | None] | None:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            res = await client.request(method, f"{API_BASE_URL}{endpoint}", params=params, json=data)
            return res.status_code, res.json()
        except httpx.RequestError as e:
            print(f"[api_request] ❌ Request error: {e}")
        except httpx.HTTPStatusError as e:
            print(f"[api_request] ❌ HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"[api_request] ❌ Unexpected error: {e}")
        return None