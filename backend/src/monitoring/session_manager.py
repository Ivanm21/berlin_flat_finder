from __future__ import annotations

import asyncio
import logging
import random
from itertools import cycle
from typing import Any, Mapping, MutableMapping, Sequence

import httpx

from backend.src.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SessionManagerError(RuntimeError):
    """Raised when the session manager exhausts retries without success."""


class SessionManager:
    """Manage HTTP sessions with rotating headers, optional proxies, and adaptive backoff."""

    DEFAULT_USER_AGENTS: Sequence[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    )

    BASE_HEADERS: Mapping[str, str] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,de-DE;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    RETRYABLE_STATUSES: Sequence[int] = (403, 408, 409, 425, 429, 500, 502, 503, 504)

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        proxies: Sequence[str] | None = None,
        concurrency: int = 3,
        timeout: float = 20.0,
        max_attempts: int = 5,
    ) -> None:
        self._settings = settings or get_settings()
        self._timeout = timeout
        self._max_attempts = max(1, max_attempts)
        self._proxies = tuple(proxies) if proxies is not None else tuple(self._settings.proxy_list)
        num_clients = max(1, concurrency, len(self._proxies) or 0)

        self._clients: list[httpx.AsyncClient] = []
        for idx in range(num_clients):
            proxy = self._proxies[idx % len(self._proxies)] if self._proxies else None
            self._clients.append(self._create_client(proxy=proxy, tag=f"client-{idx}"))

        self._client_lock = asyncio.Lock()
        self._client_index = 0
        self._ua_cycle = cycle(self.DEFAULT_USER_AGENTS)
        self._ua_lock = asyncio.Lock()
        self._owns_clients = True
        self._max_backoff_seconds = max(30.0, self._settings.monitor_backoff_base_seconds * 6)

    async def __aenter__(self) -> "SessionManager":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if not self._owns_clients:
            return
        await asyncio.gather(*(client.aclose() for client in self._clients), return_exceptions=True)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("HEAD", url, **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        max_attempts: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts = max_attempts or self._max_attempts
        last_exc: Exception | None = None

        for attempt in range(attempts):
            client = await self._next_client()
            request_headers = await self._build_headers(headers)

            try:
                response = await client.request(
                    method,
                    url,
                    headers=request_headers,
                    timeout=kwargs.pop("timeout", self._timeout),
                    **kwargs,
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "HTTP error during %s %s (attempt %s/%s): %s",
                    method,
                    url,
                    attempt + 1,
                    attempts,
                    exc,
                )
                await self._sleep_with_backoff(attempt)
                continue

            if response.status_code in self.RETRYABLE_STATUSES:
                last_exc = SessionManagerError(
                    f"Supplied endpoint returned {response.status_code} for {method} {url}"
                )
                logger.info(
                    "Retrying %s %s due to HTTP %s (attempt %s/%s)",
                    method,
                    url,
                    response.status_code,
                    attempt + 1,
                    attempts,
                )
                await self._sleep_with_backoff(attempt)
                continue

            return response

        raise SessionManagerError(
            f"Failed to fetch {method} {url} after {attempts} attempts"
        ) from last_exc

    async def _next_client(self) -> httpx.AsyncClient:
        async with self._client_lock:
            client = self._clients[self._client_index]
            self._client_index = (self._client_index + 1) % len(self._clients)
        return client

    async def _build_headers(self, extra: Mapping[str, str] | None) -> MutableMapping[str, str]:
        async with self._ua_lock:
            user_agent = next(self._ua_cycle)

        merged: dict[str, str] = dict(self.BASE_HEADERS)
        merged["User-Agent"] = user_agent
        if extra:
            merged.update(extra)
        return merged

    async def _sleep_with_backoff(self, attempt: int) -> None:
        base = max(1.0, self._settings.monitor_backoff_base_seconds)
        delay = min(self._max_backoff_seconds, base * (2 ** attempt))
        jitter = random.uniform(0, delay * 0.25)
        await asyncio.sleep(delay + jitter)

    def _create_client(self, *, proxy: str | None, tag: str) -> httpx.AsyncClient:
        limits = httpx.Limits(max_keepalive_connections=8, max_connections=20, keepalive_expiry=60)
        return httpx.AsyncClient(
            proxies=proxy,
            timeout=self._timeout,
            follow_redirects=True,
            limits=limits,
            headers=self.BASE_HEADERS,
            transport=httpx.AsyncHTTPTransport(retries=0),
        )
