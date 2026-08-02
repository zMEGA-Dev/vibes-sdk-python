"""
vibes_client.py — Official Python SDK for vibes.su
Supports both synchronous and asynchronous usage.

Requires: httpx>=0.27.0  (pip install httpx)
Python:   3.9+
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx

__version__ = "2.0.0"
__all__ = ["VibesAPIError", "VibesAPI", "AsyncVibesAPI"]


# ─── Custom exception ────────────────────────────────────────────────────────

class VibesAPIError(Exception):
    """Raised for any non-2xx response from the vibes.su API."""

    def __init__(self, message: str, status: int, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body

    def __repr__(self) -> str:  # pragma: no cover
        return f"VibesAPIError(status={self.status}, message={self!s})"


# ─── Helpers ─────────────────────────────────────────────────────────────────

_NON_ASCII = re.compile(r"[^\x00-\x7F]")


def _validate_key(api_key: str) -> str:
    if not isinstance(api_key, str) or not api_key.strip():
        raise TypeError(
            "[VibesAPI] api_key must be a non-empty string. "
            "Get yours at https://vibes.su/account/api"
        )
    if _NON_ASCII.search(api_key):
        raise TypeError(
            "[VibesAPI] api_key contains non-ASCII characters (e.g. Cyrillic). "
            "Please copy the key exactly from https://vibes.su/account/api"
        )
    return api_key.strip()


def _build_qs(params: Optional[Dict]) -> str:
    """Return '?k=v&...' or '' if params is empty/None."""
    if not params:
        return ""
    filtered = {k: v for k, v in params.items() if v is not None}
    return ("?" + urlencode(filtered, doseq=True)) if filtered else ""


def _unwrap(body: Any) -> Any:
    """Extract `data` from a JSON:API envelope, or return raw body."""
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        body = response.json()
    except Exception:
        body = None
    title = (
        (body or {}).get("errors", [{}])[0].get("title")
        or (body or {}).get("message")
        or f"HTTP {response.status_code}"
    )
    status = response.status_code
    if status == 401:
        raise VibesAPIError(f"[VibesAPI] Unauthorized — {title}. Check your API key.", status, body)
    if status == 404:
        raise VibesAPIError(f"[VibesAPI] Not found — {title}", status, body)
    if status == 429:
        raise VibesAPIError("[VibesAPI] Rate limit exceeded (60 req/min). Please slow down.", status, body)
    raise VibesAPIError(f"[VibesAPI] Request failed ({status}): {title}", status, body)


def _parse(response: httpx.Response) -> Any:
    """Parse a successful response: return None on 204, else unwrap JSON."""
    if response.status_code == 204 or (
        response.status_code == 200 and response.headers.get("content-length") == "0"
    ):
        return None
    return _unwrap(response.json())


# ─── Synchronous client ───────────────────────────────────────────────────────

class VibesAPI:
    """
    Synchronous Python SDK for vibes.su.

    Usage::

        from vibes_client import VibesAPI, VibesAPIError

        api = VibesAPI("YOUR_API_KEY_HERE")
        user = api.get_user()
        print(user["name"])

    All methods return plain Python dicts/lists (parsed from JSON:API envelope).
    Errors raise :class:`VibesAPIError`.
    """

    BASE_URL = "https://vibes.su"

    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 30.0) -> None:
        self._api_key = _validate_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/vnd.api+json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "VibesAPI":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Low-level ─────────────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        r = self._client.get(path + _build_qs(params))
        _raise_for_status(r)
        return _parse(r)

    def _post_form(self, path: str, data: Optional[Dict] = None) -> Any:
        encoded = _encode_form(data or {})
        r = self._client.post(
            path,
            content=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        _raise_for_status(r)
        return _parse(r)

    def _delete(self, path: str) -> None:
        r = self._client.delete(path)
        _raise_for_status(r)
        return _parse(r)

    # ══════════════════════════════════════════════════════════════════════════
    # USER
    # ══════════════════════════════════════════════════════════════════════════

    def get_user(self) -> Dict:
        """GET /api/user — authenticated user profile and plan settings."""
        return self._get("/api/user")

    # ══════════════════════════════════════════════════════════════════════════
    # LINKS
    # ══════════════════════════════════════════════════════════════════════════

    def get_links(self, **params) -> List[Dict]:
        """GET /api/links — list links (paginated).

        Params: page, results_per_page, is_enabled, type, project_id, domain_id
        """
        return self._get("/api/links", params or None)

    def get_link(self, link_id: int) -> Dict:
        """GET /api/links/{id}"""
        return self._get(f"/api/links/{link_id}")

    def create_link(self, location_url: str, **kwargs) -> Dict:
        """POST /api/links — create a short link.

        Args:
            location_url: destination URL (required)
            url: custom alias
            targeting_type: 'country_code' | 'device_type' | 'rotation' | ...
            targeting_country_code_key: list of ISO country codes
            targeting_country_code_value: list of destination URLs (same order)
            cloaking_is_enabled: 0|1
            http_status_code: 301|302|307|308
            password: protect the link
            clicks_limit: max clicks before expiry
            start_date / end_date: 'YYYY-MM-DD HH:MM:SS'
            is_bulk: 0|1
            location_urls: newline-separated URLs for bulk mode
        """
        return self._post_form("/api/links", {"location_url": location_url, **kwargs})

    def update_link(self, link_id: int, **kwargs) -> Dict:
        """POST /api/links/{id}"""
        return self._post_form(f"/api/links/{link_id}", kwargs)

    def delete_link(self, link_id: int) -> None:
        """DELETE /api/links/{id}"""
        return self._delete(f"/api/links/{link_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # QR CODES
    # ══════════════════════════════════════════════════════════════════════════

    def get_qr_codes(self, **params) -> List[Dict]:
        """GET /api/qr-codes"""
        return self._get("/api/qr-codes", params or None)

    def get_qr_code(self, qr_code_id: int) -> Dict:
        """GET /api/qr-codes/{id}"""
        return self._get(f"/api/qr-codes/{qr_code_id}")

    def create_qr_code(self, type: str, name: str, **kwargs) -> Dict:
        """POST /api/qr-codes — create a QR code.

        Types: text | url | phone | sms | email | whatsapp | facetime |
               location | wifi | event | crypto | vcard | paypal | upi | epc | pix

        Dynamic URL example::

            api.create_qr_code("url", "My QR", url="https://example.com", url_dynamic=1)
        """
        return self._post_form("/api/qr-codes", {"type": type, "name": name, **kwargs})

    def update_qr_code(self, qr_code_id: int, **kwargs) -> Dict:
        """POST /api/qr-codes/{id}"""
        return self._post_form(f"/api/qr-codes/{qr_code_id}", kwargs)

    def delete_qr_code(self, qr_code_id: int) -> None:
        """DELETE /api/qr-codes/{id}"""
        return self._delete(f"/api/qr-codes/{qr_code_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ══════════════════════════════════════════════════════════════════════════

    def get_link_statistics(self, link_id: int, type: str = "overview", **params) -> List[Dict]:
        """GET /api/statistics/{linkId}?type=...

        Types: overview | country_code | city_name | continent_code | os_name |
               browser_name | device_type | browser_language | referrer_host |
               referrer_path | utm_source | utm_medium | utm_campaign | hour
        """
        return self._get(f"/api/statistics/{link_id}", {"type": type, **params})

    def get_all_statistics(self, type: str = "overview", **params) -> List[Dict]:
        """GET /api/statistics?type=... — aggregated across all links."""
        return self._get("/api/statistics", {"type": type, **params})

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECTS
    # ══════════════════════════════════════════════════════════════════════════

    def get_projects(self, **params) -> List[Dict]:
        """GET /api/projects"""
        return self._get("/api/projects", params or None)

    def get_project(self, project_id: int) -> Dict:
        """GET /api/projects/{id}"""
        return self._get(f"/api/projects/{project_id}")

    def create_project(self, name: str, color: str = "#000000", **kwargs) -> Dict:
        """POST /api/projects"""
        return self._post_form("/api/projects", {"name": name, "color": color, **kwargs})

    def update_project(self, project_id: int, **kwargs) -> Dict:
        """POST /api/projects/{id}"""
        return self._post_form(f"/api/projects/{project_id}", kwargs)

    def delete_project(self, project_id: int) -> None:
        """DELETE /api/projects/{id}"""
        return self._delete(f"/api/projects/{project_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # PIXELS
    # ══════════════════════════════════════════════════════════════════════════

    def get_pixels(self, **params) -> List[Dict]:
        """GET /api/pixels"""
        return self._get("/api/pixels", params or None)

    def get_pixel(self, pixel_id: int) -> Dict:
        """GET /api/pixels/{id}"""
        return self._get(f"/api/pixels/{pixel_id}")

    def create_pixel(self, type: str, name: str, pixel: str) -> Dict:
        """POST /api/pixels"""
        return self._post_form("/api/pixels", {"type": type, "name": name, "pixel": pixel})

    def update_pixel(self, pixel_id: int, **kwargs) -> Dict:
        """POST /api/pixels/{id}"""
        return self._post_form(f"/api/pixels/{pixel_id}", kwargs)

    def delete_pixel(self, pixel_id: int) -> None:
        """DELETE /api/pixels/{id}"""
        return self._delete(f"/api/pixels/{pixel_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # DOMAINS
    # ══════════════════════════════════════════════════════════════════════════

    def get_domains(self, **params) -> List[Dict]:
        """GET /api/domains"""
        return self._get("/api/domains", params or None)

    def get_domain(self, domain_id: int) -> Dict:
        """GET /api/domains/{id}"""
        return self._get(f"/api/domains/{domain_id}")

    def get_available_domains(self, **params) -> List[Dict]:
        """GET /api/domains/available — own + shared global domains."""
        return self._get("/api/domains/available", params or None)

    def create_domain(self, host: str, scheme: str = "https://", **kwargs) -> Dict:
        """POST /api/domains"""
        return self._post_form("/api/domains", {"host": host, "scheme": scheme, **kwargs})

    def update_domain(self, domain_id: int, **kwargs) -> Dict:
        """POST /api/domains/{id}"""
        return self._post_form(f"/api/domains/{domain_id}", kwargs)

    def delete_domain(self, domain_id: int) -> None:
        """DELETE /api/domains/{id}"""
        return self._delete(f"/api/domains/{domain_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # SPLASH PAGES
    # ══════════════════════════════════════════════════════════════════════════

    def get_splash_pages(self, **params) -> List[Dict]:
        """GET /api/splash-pages"""
        return self._get("/api/splash-pages", params or None)

    def get_splash_page(self, splash_page_id: int) -> Dict:
        """GET /api/splash-pages/{id}"""
        return self._get(f"/api/splash-pages/{splash_page_id}")

    def create_splash_page(self, name: str, **kwargs) -> Dict:
        """POST /api/splash-pages"""
        return self._post_form("/api/splash-pages", {"name": name, **kwargs})

    def update_splash_page(self, splash_page_id: int, **kwargs) -> Dict:
        """POST /api/splash-pages/{id}"""
        return self._post_form(f"/api/splash-pages/{splash_page_id}", kwargs)

    def delete_splash_page(self, splash_page_id: int) -> None:
        """DELETE /api/splash-pages/{id}"""
        return self._delete(f"/api/splash-pages/{splash_page_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # NOTIFICATION HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def get_notification_handlers(self, **params) -> List[Dict]:
        """GET /api/notification-handlers"""
        return self._get("/api/notification-handlers", params or None)

    def get_notification_handler(self, handler_id: int) -> Dict:
        """GET /api/notification-handlers/{id}"""
        return self._get(f"/api/notification-handlers/{handler_id}")

    def create_notification_handler(self, type: str, name: str, **kwargs) -> Dict:
        """POST /api/notification-handlers

        Types: email | telegram | whatsapp | slack | discord | x |
               twilio | twilio_call | sixsixtext_send_sms | sixsixtext_save_contact
        """
        return self._post_form("/api/notification-handlers", {"type": type, "name": name, **kwargs})

    def update_notification_handler(self, handler_id: int, **kwargs) -> Dict:
        """POST /api/notification-handlers/{id}"""
        return self._post_form(f"/api/notification-handlers/{handler_id}", kwargs)

    def delete_notification_handler(self, handler_id: int) -> None:
        """DELETE /api/notification-handlers/{id}"""
        return self._delete(f"/api/notification-handlers/{handler_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # TEAMS
    # ══════════════════════════════════════════════════════════════════════════

    def get_teams(self, **params) -> List[Dict]:
        """GET /api/teams"""
        return self._get("/api/teams", params or None)

    def get_team(self, team_id: int) -> Dict:
        """GET /api/teams/{id}"""
        return self._get(f"/api/teams/{team_id}")

    def create_team(self, name: str) -> Dict:
        """POST /api/teams"""
        return self._post_form("/api/teams", {"name": name})

    def update_team(self, team_id: int, name: str) -> Dict:
        """POST /api/teams/{id}"""
        return self._post_form(f"/api/teams/{team_id}", {"name": name})

    def delete_team(self, team_id: int) -> None:
        """DELETE /api/teams/{id}"""
        return self._delete(f"/api/teams/{team_id}")

    # ── Team members (owner side) ─────────────────────────────────────────────

    def get_team_members(self, team_id: int) -> List[Dict]:
        """GET /api/team-members/{teamId}"""
        return self._get(f"/api/team-members/{team_id}")

    def create_team_member(self, team_id: int, user_email: str, access: Optional[List[str]] = None) -> Dict:
        """POST /api/team-members — invite a user by email."""
        data: Dict[str, Any] = {"team_id": team_id, "user_email": user_email}
        if access:
            data["access[]"] = access
        return self._post_form("/api/team-members", data)

    def update_team_member(self, team_member_id: int, access: Optional[List[str]] = None) -> Dict:
        """POST /api/team-members/{id} — update permissions."""
        data: Dict[str, Any] = {}
        if access is not None:
            data["access[]"] = access
        return self._post_form(f"/api/team-members/{team_member_id}", data)

    def delete_team_member(self, team_member_id: int) -> None:
        """DELETE /api/team-members/{id}"""
        return self._delete(f"/api/team-members/{team_member_id}")

    # ── Team memberships (self side) ──────────────────────────────────────────

    def get_team_memberships(self, **params) -> List[Dict]:
        """GET /api/teams-member — teams you belong to."""
        return self._get("/api/teams-member", params or None)

    def get_team_membership(self, team_member_id: int) -> Dict:
        """GET /api/teams-member/{id}"""
        return self._get(f"/api/teams-member/{team_member_id}")

    def update_team_membership(self, team_member_id: int, status: int) -> Dict:
        """POST /api/teams-member/{id} — accept (1) or decline (0) invitation."""
        return self._post_form(f"/api/teams-member/{team_member_id}", {"status": status})

    def delete_team_membership(self, team_member_id: int) -> None:
        """DELETE /api/teams-member/{id} — leave a team."""
        return self._delete(f"/api/teams-member/{team_member_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # PAYMENTS  (read-only)
    # ══════════════════════════════════════════════════════════════════════════

    def get_payments(self, **params) -> List[Dict]:
        """GET /api/payments"""
        return self._get("/api/payments", params or None)

    def get_payment(self, payment_id: int) -> Dict:
        """GET /api/payments/{id}"""
        return self._get(f"/api/payments/{payment_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════════

    def get_data(self, **params) -> List[Dict]:
        """GET /api/data — form submissions etc."""
        return self._get("/api/data", params or None)

    def get_datum(self, datum_id: int) -> Dict:
        """GET /api/data/{id}"""
        return self._get(f"/api/data/{datum_id}")

    def delete_data(self, datum_id: int) -> None:
        """DELETE /api/data/{id}"""
        return self._delete(f"/api/data/{datum_id}")

    # ══════════════════════════════════════════════════════════════════════════
    # LOGS  (read-only)
    # ══════════════════════════════════════════════════════════════════════════

    def get_logs(self, **params) -> List[Dict]:
        """GET /api/logs"""
        return self._get("/api/logs", params or None)

    # ══════════════════════════════════════════════════════════════════════════
    # SIGNATURES
    # ══════════════════════════════════════════════════════════════════════════

    def get_signatures(self, **params) -> List[Dict]:
        """GET /api/signatures"""
        return self._get("/api/signatures", params or None)

    def get_signature(self, signature_id: int) -> Dict:
        """GET /api/signatures/{id}"""
        return self._get(f"/api/signatures/{signature_id}")

    def create_signature(self, name: str, **kwargs) -> Dict:
        """POST /api/signatures"""
        return self._post_form("/api/signatures", {"name": name, **kwargs})

    def update_signature(self, signature_id: int, **kwargs) -> Dict:
        """POST /api/signatures/{id}"""
        return self._post_form(f"/api/signatures/{signature_id}", kwargs)

    def delete_signature(self, signature_id: int) -> None:
        """DELETE /api/signatures/{id}"""
        return self._delete(f"/api/signatures/{signature_id}")


# ─── Array-field flattener (key[] → repeated pairs) ──────────────────────────

def _flatten(data: Dict) -> List[tuple]:
    """
    Convert a dict to a list of (key, value) pairs suitable for form encoding.
    List values are expanded as repeated 'key[]' params (PHP convention).
    """
    pairs: List[tuple] = []
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            php_key = k if k.endswith("[]") else f"{k}[]"
            for item in v:
                pairs.append((php_key, str(item)))
        else:
            pairs.append((k, str(v)))
    return pairs


def _encode_form(data: Dict) -> bytes:
    """
    Encode a dict to application/x-www-form-urlencoded bytes.
    Supports list values as repeated PHP-style key[] parameters.
    Compatible with httpx content= parameter.
    """
    parts: List[str] = []
    from urllib.parse import quote_plus
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            php_key = quote_plus(k if k.endswith("[]") else f"{k}[]")
            for item in v:
                parts.append(f"{php_key}={quote_plus(str(item))}")
        else:
            parts.append(f"{quote_plus(k)}={quote_plus(str(v))}")
    return "&".join(parts).encode("utf-8")


# ─── Async client ─────────────────────────────────────────────────────────────

class AsyncVibesAPI:
    """
    Async Python SDK for vibes.su (uses ``async/await``).

    Usage::

        import asyncio
        from vibes_client import AsyncVibesAPI

        async def main():
            async with AsyncVibesAPI("YOUR_API_KEY_HERE") as api:
                user = await api.get_user()
                print(user["name"])

        asyncio.run(main())
    """

    BASE_URL = "https://vibes.su"

    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 30.0) -> None:
        self._api_key = _validate_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/vnd.api+json",
            },
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncVibesAPI":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    # ── Low-level ─────────────────────────────────────────────────────────────

    async def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        r = await self._client.get(path + _build_qs(params))
        _raise_for_status(r)
        return _parse(r)

    async def _post_form(self, path: str, data: Optional[Dict] = None) -> Any:
        encoded = _encode_form(data or {})
        r = await self._client.post(
            path,
            content=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        _raise_for_status(r)
        return _parse(r)

    async def _delete(self, path: str) -> None:
        r = await self._client.delete(path)
        _raise_for_status(r)
        return _parse(r)

    # ── All endpoints mirror the sync client ──────────────────────────────────

    async def get_user(self) -> Dict:
        return await self._get("/api/user")

    # Links
    async def get_links(self, **params) -> List[Dict]:
        return await self._get("/api/links", params or None)

    async def get_link(self, link_id: int) -> Dict:
        return await self._get(f"/api/links/{link_id}")

    async def create_link(self, location_url: str, **kwargs) -> Dict:
        return await self._post_form("/api/links", {"location_url": location_url, **kwargs})

    async def update_link(self, link_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/links/{link_id}", kwargs)

    async def delete_link(self, link_id: int) -> None:
        return await self._delete(f"/api/links/{link_id}")

    # QR Codes
    async def get_qr_codes(self, **params) -> List[Dict]:
        return await self._get("/api/qr-codes", params or None)

    async def get_qr_code(self, qr_code_id: int) -> Dict:
        return await self._get(f"/api/qr-codes/{qr_code_id}")

    async def create_qr_code(self, type: str, name: str, **kwargs) -> Dict:
        return await self._post_form("/api/qr-codes", {"type": type, "name": name, **kwargs})

    async def update_qr_code(self, qr_code_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/qr-codes/{qr_code_id}", kwargs)

    async def delete_qr_code(self, qr_code_id: int) -> None:
        return await self._delete(f"/api/qr-codes/{qr_code_id}")

    # Statistics
    async def get_link_statistics(self, link_id: int, type: str = "overview", **params) -> List[Dict]:
        return await self._get(f"/api/statistics/{link_id}", {"type": type, **params})

    async def get_all_statistics(self, type: str = "overview", **params) -> List[Dict]:
        return await self._get("/api/statistics", {"type": type, **params})

    # Projects
    async def get_projects(self, **params) -> List[Dict]:
        return await self._get("/api/projects", params or None)

    async def get_project(self, project_id: int) -> Dict:
        return await self._get(f"/api/projects/{project_id}")

    async def create_project(self, name: str, color: str = "#000000", **kwargs) -> Dict:
        return await self._post_form("/api/projects", {"name": name, "color": color, **kwargs})

    async def update_project(self, project_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/projects/{project_id}", kwargs)

    async def delete_project(self, project_id: int) -> None:
        return await self._delete(f"/api/projects/{project_id}")

    # Pixels
    async def get_pixels(self, **params) -> List[Dict]:
        return await self._get("/api/pixels", params or None)

    async def get_pixel(self, pixel_id: int) -> Dict:
        return await self._get(f"/api/pixels/{pixel_id}")

    async def create_pixel(self, type: str, name: str, pixel: str) -> Dict:
        return await self._post_form("/api/pixels", {"type": type, "name": name, "pixel": pixel})

    async def update_pixel(self, pixel_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/pixels/{pixel_id}", kwargs)

    async def delete_pixel(self, pixel_id: int) -> None:
        return await self._delete(f"/api/pixels/{pixel_id}")

    # Domains
    async def get_domains(self, **params) -> List[Dict]:
        return await self._get("/api/domains", params or None)

    async def get_domain(self, domain_id: int) -> Dict:
        return await self._get(f"/api/domains/{domain_id}")

    async def get_available_domains(self, **params) -> List[Dict]:
        return await self._get("/api/domains/available", params or None)

    async def create_domain(self, host: str, scheme: str = "https://", **kwargs) -> Dict:
        return await self._post_form("/api/domains", {"host": host, "scheme": scheme, **kwargs})

    async def update_domain(self, domain_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/domains/{domain_id}", kwargs)

    async def delete_domain(self, domain_id: int) -> None:
        return await self._delete(f"/api/domains/{domain_id}")

    # Splash Pages
    async def get_splash_pages(self, **params) -> List[Dict]:
        return await self._get("/api/splash-pages", params or None)

    async def get_splash_page(self, splash_page_id: int) -> Dict:
        return await self._get(f"/api/splash-pages/{splash_page_id}")

    async def create_splash_page(self, name: str, **kwargs) -> Dict:
        return await self._post_form("/api/splash-pages", {"name": name, **kwargs})

    async def update_splash_page(self, splash_page_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/splash-pages/{splash_page_id}", kwargs)

    async def delete_splash_page(self, splash_page_id: int) -> None:
        return await self._delete(f"/api/splash-pages/{splash_page_id}")

    # Notification Handlers
    async def get_notification_handlers(self, **params) -> List[Dict]:
        return await self._get("/api/notification-handlers", params or None)

    async def get_notification_handler(self, handler_id: int) -> Dict:
        return await self._get(f"/api/notification-handlers/{handler_id}")

    async def create_notification_handler(self, type: str, name: str, **kwargs) -> Dict:
        return await self._post_form("/api/notification-handlers", {"type": type, "name": name, **kwargs})

    async def update_notification_handler(self, handler_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/notification-handlers/{handler_id}", kwargs)

    async def delete_notification_handler(self, handler_id: int) -> None:
        return await self._delete(f"/api/notification-handlers/{handler_id}")

    # Teams
    async def get_teams(self, **params) -> List[Dict]:
        return await self._get("/api/teams", params or None)

    async def get_team(self, team_id: int) -> Dict:
        return await self._get(f"/api/teams/{team_id}")

    async def create_team(self, name: str) -> Dict:
        return await self._post_form("/api/teams", {"name": name})

    async def update_team(self, team_id: int, name: str) -> Dict:
        return await self._post_form(f"/api/teams/{team_id}", {"name": name})

    async def delete_team(self, team_id: int) -> None:
        return await self._delete(f"/api/teams/{team_id}")

    async def get_team_members(self, team_id: int) -> List[Dict]:
        return await self._get(f"/api/team-members/{team_id}")

    async def create_team_member(self, team_id: int, user_email: str, access: Optional[List[str]] = None) -> Dict:
        data: Dict[str, Any] = {"team_id": team_id, "user_email": user_email}
        if access:
            data["access[]"] = access
        return await self._post_form("/api/team-members", data)

    async def update_team_member(self, team_member_id: int, access: Optional[List[str]] = None) -> Dict:
        data: Dict[str, Any] = {}
        if access is not None:
            data["access[]"] = access
        return await self._post_form(f"/api/team-members/{team_member_id}", data)

    async def delete_team_member(self, team_member_id: int) -> None:
        return await self._delete(f"/api/team-members/{team_member_id}")

    async def get_team_memberships(self, **params) -> List[Dict]:
        return await self._get("/api/teams-member", params or None)

    async def get_team_membership(self, team_member_id: int) -> Dict:
        return await self._get(f"/api/teams-member/{team_member_id}")

    async def update_team_membership(self, team_member_id: int, status: int) -> Dict:
        return await self._post_form(f"/api/teams-member/{team_member_id}", {"status": status})

    async def delete_team_membership(self, team_member_id: int) -> None:
        return await self._delete(f"/api/teams-member/{team_member_id}")

    # Payments
    async def get_payments(self, **params) -> List[Dict]:
        return await self._get("/api/payments", params or None)

    async def get_payment(self, payment_id: int) -> Dict:
        return await self._get(f"/api/payments/{payment_id}")

    # Data
    async def get_data(self, **params) -> List[Dict]:
        return await self._get("/api/data", params or None)

    async def get_datum(self, datum_id: int) -> Dict:
        return await self._get(f"/api/data/{datum_id}")

    async def delete_data(self, datum_id: int) -> None:
        return await self._delete(f"/api/data/{datum_id}")

    # Logs
    async def get_logs(self, **params) -> List[Dict]:
        return await self._get("/api/logs", params or None)

    # Signatures
    async def get_signatures(self, **params) -> List[Dict]:
        return await self._get("/api/signatures", params or None)

    async def get_signature(self, signature_id: int) -> Dict:
        return await self._get(f"/api/signatures/{signature_id}")

    async def create_signature(self, name: str, **kwargs) -> Dict:
        return await self._post_form("/api/signatures", {"name": name, **kwargs})

    async def update_signature(self, signature_id: int, **kwargs) -> Dict:
        return await self._post_form(f"/api/signatures/{signature_id}", kwargs)

    async def delete_signature(self, signature_id: int) -> None:
        return await self._delete(f"/api/signatures/{signature_id}")
