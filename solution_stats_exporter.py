"""
solution_stats_exporter.py — Analytics CSV exporter

Use case: Pull click statistics for a specific link (or all links)
and export them to an Excel-friendly CSV report.

Features:
  • UTF-8 BOM header — Cyrillic characters display correctly in Excel
  • Semicolon delimiter — standard for Russian/European Excel locale
  • Multiple report types in one run
  • Configurable date range

Run: python solution_stats_exporter.py
"""

import csv
import os
import sys
from datetime import datetime
from vibes_client import VibesAPI, VibesAPIError

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY = "YOUR_API_KEY_HERE"

# Link ID to export. Set to None to export aggregated stats for ALL links.
LINK_ID = None  # e.g. 42

# Output directory for CSV files
OUTPUT_DIR = "./reports"

# Date range (None = API default, last 30 days)
START_DATE = None  # e.g. "2025-01-01 00:00:00"
END_DATE   = None  # e.g. "2025-01-31 23:59:59"

# Which report types to generate
REPORT_TYPES = [
    "overview",
    "country_code",
    "device_type",
    "os_name",
    "browser_name",
    "referrer_host",
    "utm_source",
    "hour",
]

# ─── Column labels (Russian names for Excel) ──────────────────────────────────

COLUMN_LABELS = {
    "overview":       {"formatted_date": "Дата",           "pageviews": "Просмотры", "visitors": "Посетители"},
    "country_code":   {"country_code":   "Код страны",     "pageviews": "Просмотры"},
    "city_name":      {"country_code":   "Код страны",     "country_name": "Страна", "city_name": "Город",   "pageviews": "Просмотры"},
    "continent_code": {"continent_code": "Континент",      "pageviews": "Просмотры"},
    "os_name":        {"os_name":        "ОС",             "pageviews": "Просмотры"},
    "browser_name":   {"browser_name":   "Браузер",        "pageviews": "Просмотры"},
    "device_type":    {"device_type":    "Тип устройства", "pageviews": "Просмотры"},
    "browser_language": {"browser_language": "Язык",       "pageviews": "Просмотры"},
    "referrer_host":  {"referrer_host":  "Источник",       "pageviews": "Просмотры"},
    "utm_source":     {"utm_source":     "UTM Source",     "pageviews": "Просмотры"},
    "utm_medium":     {"utm_source":     "UTM Source",     "utm_medium": "UTM Medium",    "pageviews": "Просмотры"},
    "utm_campaign":   {"utm_source":     "UTM Source",     "utm_medium": "UTM Medium", "utm_campaign": "UTM Campaign", "pageviews": "Просмотры"},
    "hour":           {"hour":           "Час",            "pageviews": "Просмотры"},
}

DELIMITER = ";"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def localize_rows(rows: list, report_type: str) -> list:
    labels = COLUMN_LABELS.get(report_type)
    if not labels:
        return rows
    result = []
    for row in rows:
        result.append({label: row.get(key, "") for key, label in labels.items()})
    return result

def write_csv(filepath: str, rows: list) -> None:
    if not rows:
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write("No data\n")
        return
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=DELIMITER)
        writer.writeheader()
        writer.writerows(rows)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("📊  vibes.su Analytics CSV Exporter (Python SDK)")
    print("=" * 50 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁  Output directory: {os.path.abspath(OUTPUT_DIR)}\n")

    with VibesAPI(API_KEY) as api:
        user = api.get_user()
        print(f"✅  Authenticated as: {user['name']} ({user['email']})\n")

        link_label = "all links (aggregated)"
        if LINK_ID:
            link = api.get_link(LINK_ID)
            link_label = f"link #{link['id']} ({link['url']} → {link['location_url']})"
        print(f"🔗  Reporting on: {link_label}")

        date_params = {}
        if START_DATE:
            date_params["start_date"] = START_DATE
        if END_DATE:
            date_params["end_date"] = END_DATE
        if date_params:
            print(f"📅  Date range: {START_DATE or 'beginning'} → {END_DATE or 'now'}")

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        generated = []

        for report_type in REPORT_TYPES:
            print(f"\n⏳  Fetching \"{report_type}\" ...", end=" ", flush=True)

            try:
                if LINK_ID:
                    rows = api.get_link_statistics(LINK_ID, report_type, **date_params)
                else:
                    rows = api.get_all_statistics(report_type, **date_params)

                if not rows:
                    print("⚠   no data, skipping.")
                    continue

                localized = localize_rows(rows, report_type)
                link_suffix = f"_link{LINK_ID}" if LINK_ID else "_all"
                filename = f"report_{report_type}{link_suffix}_{timestamp}.csv"
                filepath = os.path.join(OUTPUT_DIR, filename)
                write_csv(filepath, localized)

                print(f"✅  {len(rows)} rows → {filename}")
                generated.append({"type": report_type, "filename": filename, "rows": len(rows)})

            except VibesAPIError as e:
                print(f"❌  API error [{e.status}]: {e}")
            except Exception as e:
                print(f"❌  Error: {e}")

    print("\n" + "=" * 40)
    print("📊  Export complete!")
    print(f"    📁  Output: {os.path.abspath(OUTPUT_DIR)}\n")

    if generated:
        print("    Generated reports:")
        for r in generated:
            print(f"    • {r['filename']}  ({r['rows']} rows, type: {r['type']})")
    else:
        print("    ⚠   No reports generated — no data for the selected period.")

    print("\n💡  Open CSV in Excel: Data → From Text/CSV → UTF-8 + semicolon delimiter.\n")


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
