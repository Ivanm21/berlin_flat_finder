from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class ListingSummary(BaseModel):
    external_id: str
    title: str
    price_eur: int
    rooms: float | None = None
    size_sqm: float | None = None
    district: str | None = None
    detail_url: HttpUrl
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


_PRICE_PATTERN = re.compile(r"([0-9][0-9\.\s]*)")
_FLOAT_PATTERN = re.compile(r"([0-9]+(?:[.,][0-9]+)?)")
_ID_PATTERN = re.compile(r"(\d+)$")


def parse_listing_summaries(html: str, *, base_url: str = "https://www.immobilienscout24.de") -> List[ListingSummary]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-is24-expose-id], article[data-obid]")
    results: List[ListingSummary] = []

    for card in cards:
        external_id = _normalize_id(
            card.get("data-is24-expose-id") or card.get("data-obid") or card.get("id")
        )
        if not external_id:
            continue

        title = _extract_text(
            card,
            ".result-list-entry__brand-title, .result-list-entry__data h5, h2, h3",
        )
        price = _extract_price(card)
        detail_url = _extract_detail_url(card, base_url)
        if not (title and price is not None and detail_url):
            continue

        payload = {
            "external_id": external_id,
            "title": title,
            "price_eur": price,
            "rooms": _extract_float(card, "[data-qa='rooms'], .result-list-entry__primary-criterion:contains('Zimmer')"),
            "size_sqm": _extract_float(card, "[data-qa='livingSpace'], .result-list-entry__primary-criterion:contains('m²')"),
            "district": _extract_text(card, ".result-list-entry__address, address, [data-qa='district']"),
            "detail_url": detail_url,
        }

        try:
            results.append(ListingSummary(**payload))
        except ValidationError:
            continue

    return results


def _normalize_id(raw_id: Optional[str]) -> Optional[str]:
    if not raw_id:
        return None
    match = _ID_PATTERN.search(raw_id.strip())
    return match.group(1) if match else raw_id.strip()


def _extract_text(card, selector: str) -> Optional[str]:
    element = card.select_one(selector)
    if not element:
        return None
    text = element.get_text(strip=True)
    return text or None


def _extract_price(card) -> Optional[int]:
    text = _extract_text(
        card,
        "[data-qa='cold-rent'], .result-list-entry__primary-criterion strong, .result-list-entry__finance strong",
    )
    if not text:
        return None
    match = _PRICE_PATTERN.search(text.replace(",", "."))
    if not match:
        return None
    return int(match.group(1).replace(".", "").replace(" ", ""))


def _extract_float(card, selector: str) -> Optional[float]:
    element = card.select_one(selector)
    if not element:
        return None
    match = _FLOAT_PATTERN.search(element.get_text())
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _extract_detail_url(card, base_url: str) -> Optional[str]:
    link = card.select_one("a")
    if not link:
        return None
    href = link.get("href")
    if not href:
        return None
    if href.startswith("http"):
        return href
    return base_url.rstrip("/") + "/" + href.lstrip("/")
