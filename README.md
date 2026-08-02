# vibes-sdk-python · Official Python SDK

> Python client for the [vibes.su](https://vibes.su/en) link management API.

[![Python ≥3.9](https://img.shields.io/badge/python-%3E%3D3.9-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Platform: vibes.su](https://img.shields.io/badge/platform-vibes.su-orange)](https://vibes.su/en)

> ⚠️ **Availability notice:** vibes.su is currently available for Russian users only.
> Payments are processed in RUB via Russian payment systems.
> API access is available on paid plans.
> 🌐 English version of the website: [vibes.su/en](https://vibes.su/en)

---

## What is vibes.su?

**vibes.su** is a professional link management platform for marketers, webmasters, and traffic arbitrageurs:

- 🔗 **Smart short links** — GEO-targeting, device targeting, cloaking, UTM tags, click limits, scheduling
- 🔲 **Dynamic QR codes** — change the destination URL without reprinting
- 📊 **Deep analytics** — country, city, device, browser, referrer, UTM, hourly breakdowns
- 🎯 **Splash pages** — interstitial micro-landings before redirect
- 🌐 **Custom domains** — branded short domains
- 🔔 **Notification handlers** — Telegram, email, Slack, Discord, WhatsApp alerts
- 👥 **Teams** — multi-user access with role-based permissions

---

## Requirements

- Python **3.9+**
- [`httpx`](https://www.python-httpx.org/) ≥ 0.27.0
- A vibes.su account with API access (paid plan)

---

## Installation

```bash
pip install httpx
# then copy vibes_client.py into your project, or clone the repo:
git clone https://github.com/vibes-su/vibes-sdk-python.git
cd vibes-sdk-python
pip install -r requirements.txt
```

---

## Getting your API key

1. Log in at [vibes.su](https://vibes.su/en)
2. Go to **Account → API** (`https://vibes.su/account/api`)
3. Copy your Bearer token (32 hex characters)

> Keep your key secret. Never commit it to version control.

---

## Quick start

### Synchronous

```python
from vibes_client import VibesAPI, VibesAPIError

api = VibesAPI("YOUR_API_KEY_HERE")

# Get your profile
user = api.get_user()
print("Hello,", user["name"])

# Create a short link
link = api.create_link("https://your-long-url.com/page", url="my-alias")
print("Short link:", f"https://vibes.su/{link['url']}")

api.close()  # or use as a context manager (see below)
```

### Context manager (recommended)

```python
with VibesAPI("YOUR_API_KEY_HERE") as api:
    user = api.get_user()
    link = api.create_link("https://example.com")
```

### Async

```python
import asyncio
from vibes_client import AsyncVibesAPI

async def main():
    async with AsyncVibesAPI("YOUR_API_KEY_HERE") as api:
        user = await api.get_user()
        link = await api.create_link("https://example.com")
        print(link["url"])

asyncio.run(main())
```

---

## Error handling

```python
from vibes_client import VibesAPIError

try:
    link = api.create_link("https://example.com")
except VibesAPIError as e:
    print(f"[{e.status}] {e}")
    # e.body — raw response dict
```

`VibesAPIError` is raised on HTTP 4xx / 5xx.
Status `429` means you hit the **60 req/min** rate limit.

---

## API reference

### Constructor

```python
VibesAPI(api_key, base_url="https://vibes.su", timeout=30.0)
AsyncVibesAPI(api_key, base_url="https://vibes.su", timeout=30.0)
```

Raises `TypeError` immediately (before any network call) if the key is empty
or contains non-ASCII characters (e.g. Cyrillic).

---

### Methods

#### User
| Method | Description |
|--------|-------------|
| `get_user()` | Authenticated user profile and plan settings |

#### Links
| Method | Description |
|--------|-------------|
| `get_links(**params)` | List links (paginated) |
| `get_link(link_id)` | Get a single link |
| `create_link(location_url, **kwargs)` | Create a link |
| `update_link(link_id, **kwargs)` | Update a link |
| `delete_link(link_id)` | Delete a link |

**Key `create_link` kwargs:**

| Kwarg | Type | Description |
|-------|------|-------------|
| `url` | str | Custom alias (auto-generated if omitted) |
| `targeting_type` | str | `country_code` · `device_type` · `os_name` · `rotation` · ... |
| `targeting_country_code_key` | list | Country codes for GEO routing |
| `targeting_country_code_value` | list | Destination URLs per country |
| `cloaking_is_enabled` | 0\|1 | URL cloaking |
| `http_status_code` | int | 301 / 302 / 307 / 308 |
| `password` | str | Password-protect the link |
| `clicks_limit` | int | Max clicks before expiry |
| `start_date` / `end_date` | str | Schedule `YYYY-MM-DD HH:MM:SS` |
| `is_bulk` | 0\|1 | Bulk mode |
| `location_urls` | str | Newline-separated URLs for bulk mode |

**GEO-targeting example:**

```python
link = api.create_link(
    "https://default-offer.com",
    targeting_type="country_code",
    targeting_country_code_key=["RU", "US", "DE"],
    targeting_country_code_value=[
        "https://ru-offer.com",
        "https://us-offer.com",
        "https://de-offer.com",
    ],
)
```

#### QR Codes
| Method | Description |
|--------|-------------|
| `get_qr_codes(**params)` | List QR codes |
| `get_qr_code(id)` | Get a single QR code |
| `create_qr_code(type, name, **kwargs)` | Create a QR code |
| `update_qr_code(id, **kwargs)` | Update a QR code |
| `delete_qr_code(id)` | Delete a QR code |

**Supported QR types:** `text` · `url` · `phone` · `sms` · `email` · `whatsapp` · `facetime` · `location` · `wifi` · `event` · `crypto` · `vcard` · `paypal` · `upi` · `epc` · `pix`

```python
# Dynamic URL QR code
qr = api.create_qr_code("url", "My QR", url="https://example.com", url_dynamic=1)
print(qr["qr_code"])  # SVG URL
```

#### Statistics
| Method | Description |
|--------|-------------|
| `get_link_statistics(link_id, type, **params)` | Stats for a specific link |
| `get_all_statistics(type, **params)` | Aggregated stats across all links |

**Stat types:** `overview` · `country_code` · `city_name` · `continent_code` · `os_name` · `browser_name` · `device_type` · `browser_language` · `referrer_host` · `referrer_path` · `utm_source` · `utm_medium` · `utm_campaign` · `hour`

#### Other resources

| Group | Methods |
|-------|---------|
| Projects | `get_projects` · `get_project` · `create_project` · `update_project` · `delete_project` |
| Pixels | `get_pixels` · `get_pixel` · `create_pixel` · `update_pixel` · `delete_pixel` |
| Domains | `get_domains` · `get_domain` · `get_available_domains` · `create_domain` · `update_domain` · `delete_domain` |
| Splash Pages | `get_splash_pages` · `get_splash_page` · `create_splash_page` · `update_splash_page` · `delete_splash_page` |
| Notification Handlers | `get_notification_handlers` · `get_notification_handler` · `create_notification_handler` · `update_notification_handler` · `delete_notification_handler` |
| Teams (owner) | `get_teams` · `get_team` · `create_team` · `update_team` · `delete_team` |
| Team Members (owner) | `get_team_members` · `create_team_member` · `update_team_member` · `delete_team_member` |
| Team Memberships (self) | `get_team_memberships` · `get_team_membership` · `update_team_membership` · `delete_team_membership` |
| Payments | `get_payments` · `get_payment` |
| Data | `get_data` · `get_datum` · `delete_data` |
| Logs | `get_logs` |
| Signatures | `get_signatures` · `get_signature` · `create_signature` · `update_signature` · `delete_signature` |

---

## Automation solutions

### 🌍 GEO Traffic Rotator — `solution_geo_rotator.py`

One smart-link that routes visitors to different URLs based on their country.
Edit `GEO_CONFIG` and `DEFAULT_URL`, then:

```bash
python solution_geo_rotator.py
```

### 🔲 Bulk QR Code Generator — `solution_bulk_qr_generator.py`

Generate dynamic QR code SVG files in bulk from a list of items.
Edit the `ITEMS` list (or load from CSV), then:

```bash
python solution_bulk_qr_generator.py
# Output: ./qr_output/<name>.svg
```

### 📊 Analytics CSV Exporter — `solution_stats_exporter.py`

Export click statistics to UTF-8 CSV files (semicolon-delimited, Excel-compatible).
Edit `LINK_ID`, `START_DATE`, `END_DATE`, then:

```bash
python solution_stats_exporter.py
# Output: ./reports/report_<type>_<timestamp>.csv
```

---

## Rate limits

**60 requests per minute** per API key.
The SDK raises `VibesAPIError` with `status=429` when the limit is exceeded.

---

## License

MIT © vibes.su

---

## Support

- 📖 API docs: [vibes.su/api-documentation](https://vibes.su/api-documentation)
- 📧 Contact: [vibes.su/contact](https://vibes.su/contact)
- 💬 Telegram: [@vibes_su](https://t.me/vibes_su)
