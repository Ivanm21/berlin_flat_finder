from __future__ import annotations

import asyncio
import gzip
import logging
import random
import zlib
from typing import Optional

import httpx

from backend.src.config import get_settings
from backend.src.monitoring.session_manager import SessionManager, SessionManagerError

try:  # Optional Brotli support
    import brotlicffi as _brotli  # type: ignore
except ImportError:
    try:
        import brotli as _brotli  # type: ignore
    except ImportError:
        _brotli = None

logger = logging.getLogger(__name__)


async def fetch_search_page(
    url: str,
    session_manager: SessionManager,
    *,
    max_attempts: int = 3,
) -> str:
    """
    Retrieve an ImmobilienScout24 search page and return raw HTML.

    Retries on transient network failures while applying exponential backoff with jitter.
    """
    settings = get_settings()
    base_delay = max(1.0, settings.monitor_backoff_base_seconds)
    max_delay = max(base_delay * 8, 60.0)
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = await session_manager.get(url)
            response.raise_for_status()
            return _decode_body(response)
        except (SessionManagerError, httpx.HTTPError, ValueError, OSError) as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, delay * 0.3)
            sleep_for = delay + jitter
            logger.warning(
                "fetch_search_page retry %s/%s for %s due to %s; sleeping %.2fs",
                attempt,
                max_attempts,
                url,
                exc,
                sleep_for,
            )
            await asyncio.sleep(sleep_for)

    raise SessionManagerError(f"Failed to fetch {url} after {max_attempts} attempts") from last_exc


def _decode_body(response: httpx.Response) -> str:
    content = response.content
    encoding = (response.headers.get("content-encoding") or "").lower()

    if encoding == "gzip":
        content = gzip.decompress(content)
    elif encoding == "deflate":
        content = zlib.decompress(content)
    elif encoding == "br" and _brotli is not None:
        content = _brotli.decompress(content)

    text_encoding = response.encoding or "utf-8"
    return content.decode(text_encoding, errors="replace")
