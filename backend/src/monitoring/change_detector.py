from __future__ import annotations

import asyncio
import logging
from typing import Iterable, List, Sequence, Set

from backend.src.db.supabase_client import SupabaseClient, SupabaseClientError
from backend.src.monitoring.listing_parser import ListingSummary

logger = logging.getLogger(__name__)


class ChangeDetectorError(RuntimeError):
    """Raised when persistence of seen listings fails."""


class ChangeDetector:
    """Tracks seen listings locally and within Supabase."""
    def __init__(
        self,
        *,
        supabase_client: SupabaseClient | None = None,
        preload_existing: bool = True,
    ) -> None:
        self._supabase_client = supabase_client or SupabaseClient()
        self._owns_client = supabase_client is None
        self._preload_existing = preload_existing
        self._seen_ids: Set[str] = set()
        self._loaded = False
        self._load_lock = asyncio.Lock()

    async def __aenter__(self) -> "ChangeDetector":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._supabase_client.close()

    async def filter_new_listings(self, listings: Sequence[ListingSummary]) -> List[ListingSummary]:
        await self._ensure_loaded()

        new_listings: List[ListingSummary] = []
        to_persist: List[ListingSummary] = []

        for listing in listings:
            if listing.external_id in self._seen_ids:
                continue
            self._seen_ids.add(listing.external_id)
            new_listings.append(listing)
            to_persist.append(listing)

        if to_persist:
            await self._persist_seen(to_persist)

        return new_listings

    async def _ensure_loaded(self) -> None:
        if self._loaded or not self._preload_existing:
            return

        async with self._load_lock:
            if self._loaded or not self._preload_existing:
                return
            try:
                existing = await self._supabase_client.fetch_seen_listing_ids()
            except SupabaseClientError as exc:
                logger.warning("Unable to preload seen listings from Supabase: %s", exc)
                existing = ()
            self._seen_ids.update(existing)
            self._loaded = True

    async def _persist_seen(self, listings: Iterable[ListingSummary]) -> None:
        tasks = [
            self._supabase_client.record_seen_listing(listing.external_id)
            for listing in listings
        ]
        try:
            await asyncio.gather(*tasks)
        except (SupabaseClientError, Exception) as exc:
            for listing in listings:
                self._seen_ids.discard(listing.external_id)
            raise ChangeDetectorError("Failed to persist seen listings.") from exc
