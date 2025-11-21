import httpx
import time
from typing import Optional


def fetch_url(client: httpx.Client, url: str) -> tuple[Optional[float], Optional[str]]:
    """
    Executes a request. Returns (latency, None) on success,
    or (None, error_message) on failure.
    """
    start = time.perf_counter()
    try:
        response = client.get(url)
        response.raise_for_status()
        return (time.perf_counter() - start, None)
    except httpx.TimeoutException:
        return (None, "Timeout")
    except httpx.HTTPStatusError as e:
        return (None, f"HTTP {e.response.status_code}")
    except Exception as e:
        return (None, str(e))
