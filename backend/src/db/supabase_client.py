from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence, List

import httpx

from backend.src.config import Settings, get_settings


class SupabaseClientError(RuntimeError):
    """Raised when Supabase REST API returns an error response."""


class SupabaseClient:
    """Async-friendly wrapper around Supabase REST endpoints."""

    def __init__(self, *, settings: Settings | None = None, timeout: float = 15.0, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings or get_settings()
        self._rest_base_url = f"{self._settings.supabase_url.rstrip('/')}/rest/v1"
        default_headers = {
            "apikey": self._settings.supabase_service_key,
            "Authorization": f"Bearer {self._settings.supabase_service_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(base_url=self._rest_base_url, timeout=timeout, headers=default_headers)

    async def __aenter__(self) -> "SupabaseClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def upsert_listing(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        response = await self._client.post(
            "/listings",
            params={"on_conflict": "external_id", "return": "representation"},
            json=dict(payload),
        )
        return self._parse_single(response, "upsert_listing")

    async def record_seen_listing(self, external_id: str, *, metadata: MutableMapping[str, Any] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"external_id": external_id, "last_seen_at": datetime.now(timezone.utc).isoformat()}
        if metadata:
            body.update(metadata)

        response = await self._client.post(
            "/seen_listings",
            params={"on_conflict": "external_id", "return": "representation"},
            json=body,
        )
        return self._parse_single(response, "record_seen_listing")

    async def fetch_active_preferences(self, *, columns: str = "*") -> Sequence[dict[str, Any]]:
        response = await self._client.get(
            "/user_preferences",
            params={
                "select": columns,
                "is_active": "eq.true",
                "order": "updated_at.desc.nullslast",
            },
        )
        data = self._parse_json(response, "fetch_active_preferences")
        if not isinstance(data, list):
            raise SupabaseClientError("Unexpected payload when fetching preferences.")
        return data

    async def fetch_seen_listing_ids(self, *, chunk_size: int = 500) -> Sequence[str]:
        results: List[str] = []
        offset = 0

        while True:
            headers = {"Range": f"items={offset}-{offset + chunk_size - 1}"}
            response = await self._client.get(
                "/seen_listings",
                params={"select": "external_id"},
                headers=headers,
            )
            payload = self._parse_json(response, "fetch_seen_listing_ids")

            if not isinstance(payload, list):
                raise SupabaseClientError("Unexpected payload when fetching seen listing IDs.")

            batch_ids = [item.get("external_id") for item in payload if isinstance(item, dict) and item.get("external_id")]
            results.extend(batch_ids)

            if len(payload) < chunk_size:
                break

            offset += chunk_size

        return tuple(results)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = await self._client.request(method, path, **kwargs)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SupabaseClientError(f"Supabase request failed ({exc.response.status_code}): {exc.response.text}") from exc
        return response

    def _parse_json(self, response: httpx.Response, context: str) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise SupabaseClientError(f"Supabase returned non-JSON payload for {context}.") from exc

    def _parse_single(self, response: httpx.Response, context: str) -> dict[str, Any]:
        payload = self._parse_json(response, context)
        if isinstance(payload, list):
            return payload[0] if payload else {}
        if isinstance(payload, dict):
            return payload
        raise SupabaseClientError(f"Unexpected payload shape for {context}.")
