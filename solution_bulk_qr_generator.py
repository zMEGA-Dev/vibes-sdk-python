"""
solution_bulk_qr_generator.py — Bulk dynamic QR code generator

Use case: Generate a unique QR code SVG file for each item in a list
(restaurant menu, product catalog, event stands, business cards).
Each QR code is DYNAMIC — you can update the destination URL later
without reprinting.

Output: ./qr_output/<name>.svg  for every item in the list.

Run: python solution_bulk_qr_generator.py
"""

import os
import re
import sys
import time
import urllib.request
from vibes_client import VibesAPI, VibesAPIError

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY    = "YOUR_API_KEY_HERE"
OUTPUT_DIR = "./qr_output"

# Your items list — each entry: {"name": str, "url": str}
# You can also load this from a CSV file (see helper at the bottom).
ITEMS = [
    {"name": "Homepage",        "url": "https://example.com"},
    {"name": "Menu - Starters", "url": "https://example.com/menu/starters"},
    {"name": "Menu - Main",     "url": "https://example.com/menu/main"},
    {"name": "Menu - Desserts", "url": "https://example.com/menu/desserts"},
    {"name": "Menu - Drinks",   "url": "https://example.com/menu/drinks"},
    {"name": "WiFi Password",   "url": "https://example.com/wifi"},
    {"name": "Feedback Form",   "url": "https://example.com/feedback"},
    {"name": "Instagram",       "url": "https://instagram.com/yourhandle"},
    {"name": "Telegram",        "url": "https://t.me/yourchannel"},
    {"name": "Loyalty Program", "url": "https://example.com/loyalty"},
]

# QR code visual settings (applied to all items)
QR_STYLE = {
    "style":            "square",
    "inner_eye_style":  "square",
    "outer_eye_style":  "square",
    "foreground_type":  "color",
    "foreground_color": "#1a1a2e",
    "background_color": "#ffffff",
    "size":             600,
    "margin":           2,
    "ecc":              "M",
}

# Delay between API calls (seconds) — stay under 60 req/min
DELAY_SEC = 1.2

# ─── Helpers ─────────────────────────────────────────────────────────────────

def to_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    safe = re.sub(r'[^\w\s\-]', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', '_', safe)[:80]

def load_from_csv(filepath: str) -> list:
    """
    Optional CSV loader.
    Expected format (no header): "Item Name","https://url.com"
    """
    import csv
    items = []
    with open(filepath, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                items.append({"name": row[0].strip(), "url": row[1].strip()})
    return items

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("🔲  vibes.su Bulk QR Code Generator (Python SDK)")
    print("=" * 50 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁  Output directory: {os.path.abspath(OUTPUT_DIR)}\n")

    success, failed = [], []

    with VibesAPI(API_KEY) as api:
        user = api.get_user()
        limit = user.get("plan_settings", {}).get("qr_codes_limit", "?")
        print(f"✅  Authenticated as: {user['name']} ({user['email']})")
        print(f"    QR codes limit: {'unlimited' if limit == -1 else limit}\n")
        print(f"⏳  Processing {len(ITEMS)} items...\n")

        for i, item in enumerate(ITEMS, 1):
            label = f"[{i}/{len(ITEMS)}] \"{item['name']}\" ..."
            print(label, end=" ", flush=True)

            try:
                # Validate URL
                from urllib.parse import urlparse
                parsed = urlparse(item["url"])
                if parsed.scheme not in ("http", "https"):
                    raise ValueError(f"Invalid URL: {item['url']!r}")

                qr = api.create_qr_code(
                    type="url",
                    name=item["name"],
                    url=item["url"],
                    url_dynamic=1,
                    **QR_STYLE,
                )

                svg_url = qr["qr_code"]
                with urllib.request.urlopen(svg_url, timeout=15) as resp:
                    svg_content = resp.read()

                filename = f"{to_filename(item['name'])}.svg"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(svg_content)

                print(f"✅  saved → {filename}  (QR ID: {qr['id']})")
                success.append({"item": item, "qr": qr, "filename": filename})

            except VibesAPIError as e:
                reason = f"API error [{e.status}]: {e}"
                print(f"❌  FAILED — {reason}")
                failed.append({"item": item, "reason": reason})
            except Exception as e:
                print(f"❌  FAILED — {e}")
                failed.append({"item": item, "reason": str(e)})

            if i < len(ITEMS):
                time.sleep(DELAY_SEC)

    print("\n" + "=" * 40)
    print("📊  Batch complete!")
    print(f"    ✅  Success : {len(success)}")
    print(f"    ❌  Failed  : {len(failed)}")
    print(f"    📁  Output  : {os.path.abspath(OUTPUT_DIR)}")

    if failed:
        print("\n⚠   Failed items:")
        for f in failed:
            print(f"    • \"{f['item']['name']}\" — {f['reason']}")

    if success:
        print("\n📋  Generated files:")
        for s in success:
            print(f"    • {s['filename']}  →  {s['qr']['qr_code']}")
    print()


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌  Please set your API_KEY at the top of this file.")
        print("    Get it at: https://vibes.su/account/api")
        sys.exit(1)
    try:
        main()
    except VibesAPIError as e:
        print(f"\n❌  Fatal API Error [HTTP {e.status}]: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌  Fatal error: {e}")
        sys.exit(1)
