from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
for candidate in (BACKEND_ROOT / ".env", BACKEND_ROOT / ".env.local"):
    load_dotenv(candidate, override=False)


def _parse_proxy_list(raw: str | None) -> Tuple[str, ...]:
    if not raw:
        return ()
    raw = raw.strip()
    if not raw:
        return ()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return tuple(str(item).strip() for item in parsed if str(item).strip())
    except json.JSONDecodeError:
        pass
    return tuple(token.strip() for token in raw.split(",") if token.strip())


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_key: str
    proxy_list: Tuple[str, ...]
    monitor_poll_interval_seconds: float
    monitor_backoff_base_seconds: float

    @property
    def has_proxies(self) -> bool:
        return bool(self.proxy_list)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    supabase_url = _get_env("SUPABASE_URL", "http://localhost:54321")
    supabase_service_key = _get_env("SUPABASE_SERVICE_KEY", "service-role-key-placeholder")
    proxy_list = _parse_proxy_list(_get_env("PROXY_LIST"))
    monitor_poll_interval = float(_get_env("MONITOR_POLL_INTERVAL_SECONDS", "30"))
    monitor_backoff_base = float(_get_env("MONITOR_BACKOFF_BASE_SECONDS", "120"))

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL must be configured.")
    if not supabase_service_key:
        raise RuntimeError("SUPABASE_SERVICE_KEY must be configured.")

    return Settings(
        supabase_url=supabase_url,
        supabase_service_key=supabase_service_key,
        proxy_list=proxy_list,
        monitor_poll_interval_seconds=monitor_poll_interval,
        monitor_backoff_base_seconds=monitor_backoff_base,
    )
