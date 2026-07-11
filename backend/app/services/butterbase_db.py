# Thin client for Butterbase's auto-generated data API, which persists
# operational state (plans, sessions, uploads, events) across backend
# restarts. Every call is best-effort with a short timeout: a Butterbase
# outage degrades to in-memory-only behavior and must never block gameplay.
# The data API shares the app-scoped base URL and key with the AI gateway.
import logging
from typing import Optional

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_TIMEOUT = 5.0


def _url(table: str, row_id: str = "") -> str:
    base = settings.BUTTERBASE_AI_BASE_URL.rstrip("/")
    return f"{base}/{table}/{row_id}" if row_id else f"{base}/{table}"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.BUTTERBASE_API_KEY}"}


def _enabled() -> bool:
    return bool(settings.BUTTERBASE_API_KEY)


def upsert(table: str, key: str, row: dict) -> bool:
    """Insert `row`; if the primary key already exists, update it instead."""
    if not _enabled():
        return False
    try:
        resp = httpx.post(_url(table), json=row, headers=_headers(), timeout=_TIMEOUT)
        if resp.is_success:
            return True
        # Duplicate primary key (e.g. demo plan re-seeded on restart) -> update.
        resp = httpx.patch(_url(table, key), json=row, headers=_headers(), timeout=_TIMEOUT)
        if resp.is_success:
            return True
        log.warning("Butterbase upsert %s/%s failed: %s %s", table, key, resp.status_code, resp.text[:200])
    except Exception as exc:
        log.warning("Butterbase upsert %s/%s failed: %s", table, key, exc)
    return False


def insert(table: str, row: dict) -> bool:
    if not _enabled():
        return False
    try:
        resp = httpx.post(_url(table), json=row, headers=_headers(), timeout=_TIMEOUT)
        if resp.is_success:
            return True
        log.warning("Butterbase insert into %s failed: %s %s", table, resp.status_code, resp.text[:200])
    except Exception as exc:
        log.warning("Butterbase insert into %s failed: %s", table, exc)
    return False


def fetch(table: str, row_id: str) -> Optional[dict]:
    """Fetch one row by primary key. None if missing or Butterbase unreachable."""
    if not _enabled():
        return None
    try:
        resp = httpx.get(_url(table, row_id), headers=_headers(), timeout=_TIMEOUT)
        if resp.is_success:
            return resp.json()
        if resp.status_code != 404:
            log.warning("Butterbase fetch %s/%s failed: %s", table, row_id, resp.status_code)
    except Exception as exc:
        log.warning("Butterbase fetch %s/%s failed: %s", table, row_id, exc)
    return None


def fetch_all(table: str, filters: dict, order: str = "created_at.asc") -> Optional[list]:
    """List rows matching `filters` (data-API operator syntax, e.g. "eq.x").
    None means Butterbase was unreachable — distinct from an empty list."""
    if not _enabled():
        return None
    try:
        params = {**filters, "order": order}
        resp = httpx.get(_url(table), params=params, headers=_headers(), timeout=_TIMEOUT)
        if resp.is_success:
            return resp.json()
        log.warning("Butterbase list %s failed: %s", table, resp.status_code)
    except Exception as exc:
        log.warning("Butterbase list %s failed: %s", table, exc)
    return None
