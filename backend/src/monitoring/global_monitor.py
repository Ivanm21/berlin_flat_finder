from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Iterable, Sequence

from backend.src.config import get_settings
from backend.src.db.supabase_client import SupabaseClient
from backend.src.monitoring.change_detector import ChangeDetector
from backend.src.monitoring.html_fetcher import fetch_search_page
from backend.src.monitoring.listing_parser import ListingSummary, parse_listing_summaries
from backend.src.monitoring.session_manager import SessionManager

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_ENDPOINTS: Sequence[str] = (
    "https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten",
    "https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten?pricetype=rent&sorting=2",
)


async def monitor_all_listings(
    *,
    search_endpoints: Sequence[str] | None = None,
    session_manager: SessionManager | None = None,
    supabase_client: SupabaseClient | None = None,
    change_detector: ChangeDetector | None = None,
) -> AsyncIterator[ListingSummary]:
    """
    Continuously poll ImmobilienScout24 search endpoints, yielding new listings.

    Tracks latency and success metrics per cycle while persisting seen listings via Supabase.
    """
    settings = get_settings()
    poll_interval = max(5.0, settings.monitor_poll_interval_seconds)
    endpoints = search_endpoints or DEFAULT_SEARCH_ENDPOINTS

    own_session_manager = session_manager is None
    own_supabase_client = supabase_client is None
    own_change_detector = change_detector is None

    session_manager = session_manager or SessionManager()
    supabase_client = supabase_client or SupabaseClient()
    change_detector = change_detector or ChangeDetector(supabase_client=supabase_client)

    try:
        while True:
            cycle_started = time.perf_counter()
            total = len(endpoints)
            successes = 0
            new_count = 0
            latencies: list[float] = []

            for url in endpoints:
                request_started = time.perf_counter()
                try:
                    html = await fetch_search_page(url, session_manager)
                    listings = parse_listing_summaries(html)
                    new_listings = await change_detector.filter_new_listings(listings)
                    for listing in new_listings:
                        yield listing
                    new_count += len(new_listings)
                    successes += 1
                    latencies.append(time.perf_counter() - request_started)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Monitor failed for %s: %s", url, exc)
                    continue

            success_rate = successes / total if total else 0.0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            cycle_latency = time.perf_counter() - cycle_started

            logger.info(
                "Monitor cycle complete: endpoints=%s success_rate=%.2f new_listings=%s "
                "avg_latency=%.2fs total_latency=%.2fs",
                total,
                success_rate,
                new_count,
                avg_latency,
                cycle_latency,
            )

            await asyncio.sleep(poll_interval)
    finally:
        if own_change_detector:
            await change_detector.close()
        if own_supabase_client:
            await supabase_client.close()
        if own_session_manager:
            await session_manager.close()
