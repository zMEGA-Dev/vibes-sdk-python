"""
solution_geo_rotator.py — Automatic GEO-targeting smart-link creator

Use case: You have different affiliate offers per country.
This script creates ONE smart-link that automatically redirects
visitors to the correct offer based on their country.

Run: python solution_geo_rotator.py
"""

import sys
from vibes_client import VibesAPI, VibesAPIError

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY = "YOUR_API_KEY_HERE"

# GEO routing table: ISO 3166-1 alpha-2 code → destination URL
GEO_CONFIG = {
    "RU": "https://ru-offer.example.com/landing",
    "BY": "https://by-offer.example.com/landing",
    "KZ": "https://kz-offer.example.com/landing",
    "UA": "https://ua-offer.example.com/landing",
    "US": "https://us-offer.example.com/landing",
    "DE": "https://de-offer.example.com/landing",
    "GB": "https://gb-offer.example.com/landing",
    "FR": "https://fr-offer.example.com/landing",
    "BR": "https://br-offer.example.com/landing",
    "IN": "https://in-offer.example.com/landing",
}

# Fallback URL for all countries not listed above
DEFAULT_URL = "https://default-offer.example.com/landing"

# Optional: custom short alias (leave empty for auto-generated)
CUSTOM_ALIAS = ""

# Optional: project ID to assign the link to (0 = no project)
PROJECT_ID = 0

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("🌍  vibes.su GEO Traffic Rotator (Python SDK)")
    print("=" * 46 + "\n")

    if not GEO_CONFIG:
        print("❌  GEO_CONFIG is empty. Add at least one country → URL mapping.")
        sys.exit(1)

    print(f"📋  Routing table ({len(GEO_CONFIG)} countries):")
    for code, url in GEO_CONFIG.items():
        print(f"    {code}  →  {url}")
    print(f"    ** (default)  →  {DEFAULT_URL}\n")

    with VibesAPI(API_KEY) as api:
        print("⏳  Creating smart-link on vibes.su...")

        kwargs = {
            "targeting_type": "country_code",
            "targeting_country_code_key": list(GEO_CONFIG.keys()),
            "targeting_country_code_value": list(GEO_CONFIG.values()),
            "is_enabled": 1,
        }
        if CUSTOM_ALIAS:
            kwargs["url"] = CUSTOM_ALIAS
        if PROJECT_ID:
            kwargs["project_id"] = PROJECT_ID

        link = api.create_link(DEFAULT_URL, **kwargs)

    print("\n✅  Smart-link created successfully!\n")
    print(f"   Link ID   : {link['id']}")
    print(f"   Short URL : https://vibes.su/{link['url']}")
    print(f"   Default   : {link['location_url']}")

    settings = link.get("settings") or {}
    rules = settings.get("targeting_country_code") or []
    if rules:
        print("\n   Active routing rules:")
        for r in rules:
            print(f"     {r['key']}  →  {r['value']}")

    print("\n📌  Share this single link — vibes.su handles GEO-routing automatically.\n")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌  Please set your API_KEY at the top of this file.")
        print("    Get it at: https://vibes.su/account/api")
        sys.exit(1)
    try:
        main()
    except VibesAPIError as e:
        print(f"\n❌  API Error [HTTP {e.status}]: {e}")
        if e.status == 401:
            print("    → Check your API key and plan.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌  Unexpected error: {e}")
        sys.exit(1)
