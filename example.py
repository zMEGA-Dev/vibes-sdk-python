"""
example.py — Full SDK demonstration + production test
Run: python example.py
"""

import sys
from vibes_client import VibesAPI, VibesAPIError

# ─── Replace with your real API key ──────────────────────────────────────────
API_KEY = "YOUR_API_KEY_HERE"

# ─── Helpers ─────────────────────────────────────────────────────────────────
def section(title: str) -> None:
    print(f"\n{'═' * 50}\n  {title}\n{'═' * 50}")

def run(label: str, fn):
    try:
        result = fn()
        print(f"  ✅ {label}")
        return result
    except VibesAPIError as e:
        print(f"  ❌ {label} — [{e.status}] {e}")
        return None
    except Exception as e:
        print(f"  ❌ {label} — {e}")
        return None

# ─── 1. Sync validation (no network needed) ───────────────────────────────────
def test_sync_validation() -> None:
    section("1. Sync key validation")

    try:
        VibesAPI("")
        print("  ❌ Empty key should raise")
    except TypeError as e:
        print(f"  ✅ Empty key → TypeError: {str(e)[:70]}")

    try:
        VibesAPI("мой-ключ")
        print("  ❌ Cyrillic key should raise")
    except TypeError:
        print("  ✅ Cyrillic key → TypeError")

    try:
        VibesAPI("valid-ascii-key-123")
        print("  ✅ Valid ASCII key accepted")
    except TypeError as e:
        print(f"  ❌ Valid key rejected: {e}")

# ─── 2. Live API tests ────────────────────────────────────────────────────────
def test_live() -> None:
    import time

    with VibesAPI(API_KEY) as api:

        # ── User ──────────────────────────────────────────────────────────────
        section("2. User")
        user = run("get_user()", api.get_user)
        if user:
            print(f"     → {user['name']} | plan: {user['plan_id']} | "
                  f"API: {user.get('plan_settings', {}).get('api_is_enabled')}")

        # ── Links ─────────────────────────────────────────────────────────────
        section("3. Links")
        new_link = run("create_link()", lambda: api.create_link(
            f"https://example.com/python-sdk-test-{int(time.time())}"
        ))
        if new_link:
            print(f"     → created: {new_link['url']} (id: {new_link['id']})")

        links = run("get_links()", lambda: api.get_links(results_per_page=3))
        if links:
            print(f"     → {len(links)} links returned")

        if new_link:
            run("get_link(id)", lambda: api.get_link(new_link["id"]))
            run("update_link(id)", lambda: api.update_link(
                new_link["id"], location_url="https://example.com/python-updated"
            ))
            run("delete_link(id)", lambda: api.delete_link(new_link["id"]))

        # ── Projects ──────────────────────────────────────────────────────────
        section("4. Projects")
        proj = run("create_project()", lambda: api.create_project(
            "Python SDK Test Project", color="#3776ab"
        ))
        if proj:
            print(f"     → id: {proj['id']}")
        run("get_projects()", api.get_projects)
        if proj:
            run("get_project(id)", lambda: api.get_project(proj["id"]))
            run("update_project(id)", lambda: api.update_project(
                proj["id"], name="Python SDK Project (updated)"
            ))
            run("delete_project(id)", lambda: api.delete_project(proj["id"]))

        # ── Pixels ────────────────────────────────────────────────────────────
        section("5. Pixels")
        px = run("create_pixel()", lambda: api.create_pixel(
            type="facebook", name="Python SDK Pixel", pixel="PY_TEST_123"
        ))
        if px:
            run("get_pixels()", api.get_pixels)
            run("get_pixel(id)", lambda: api.get_pixel(px["id"]))
            run("update_pixel(id)", lambda: api.update_pixel(
                px["id"], name="Python SDK Pixel (updated)"
            ))
            run("delete_pixel(id)", lambda: api.delete_pixel(px["id"]))

        # ── Domains ───────────────────────────────────────────────────────────
        section("6. Domains")
        run("get_domains()", api.get_domains)
        run("get_available_domains()", api.get_available_domains)

        # ── QR Codes ──────────────────────────────────────────────────────────
        section("7. QR Codes")
        qr = run("create_qr_code()", lambda: api.create_qr_code(
            type="url", name="Python SDK QR",
            url="https://example.com", url_dynamic=1
        ))
        if qr:
            print(f"     → id: {qr['id']} | svg: {qr['qr_code']}")
            run("get_qr_codes()", api.get_qr_codes)
            run("get_qr_code(id)", lambda: api.get_qr_code(qr["id"]))
            run("update_qr_code(id)", lambda: api.update_qr_code(
                qr["id"], name="Python SDK QR (updated)"
            ))
            run("delete_qr_code(id)", lambda: api.delete_qr_code(qr["id"]))

        # ── Statistics ────────────────────────────────────────────────────────
        section("8. Statistics")
        all_links = api.get_links(results_per_page=1) or []
        if all_links:
            lid = all_links[0]["id"]
            run(f"get_link_statistics({lid}, overview)",
                lambda: api.get_link_statistics(lid, "overview"))
            run(f"get_link_statistics({lid}, country_code)",
                lambda: api.get_link_statistics(lid, "country_code"))
        run("get_all_statistics(overview)",
            lambda: api.get_all_statistics("overview"))

        # ── Notification Handlers ─────────────────────────────────────────────
        section("9. Notification Handlers")
        run("get_notification_handlers()", api.get_notification_handlers)

        # ── Teams ─────────────────────────────────────────────────────────────
        section("10. Teams")
        team = run("create_team()", lambda: api.create_team("Python SDK Team"))
        if team:
            run("get_teams()", api.get_teams)
            run("get_team(id)", lambda: api.get_team(team["id"]))
            run("update_team(id)", lambda: api.update_team(
                team["id"], "Python SDK Team (updated)"
            ))
            member = run("create_team_member()", lambda: api.create_team_member(
                team_id=team["id"],
                user_email="sdktest+python@example.com",
                access=["read.all"],
            ))
            if member:
                run("get_team_members(team_id)",
                    lambda: api.get_team_members(team["id"]))
                run("update_team_member(id)", lambda: api.update_team_member(
                    member["id"], access=["read.all"]
                ))
                run("delete_team_member(id)",
                    lambda: api.delete_team_member(member["id"]))
            run("delete_team(id)", lambda: api.delete_team(team["id"]))

        # ── Team Memberships ──────────────────────────────────────────────────
        section("11. Team Memberships (self)")
        run("get_team_memberships()", api.get_team_memberships)

        # ── Payments ──────────────────────────────────────────────────────────
        section("12. Payments")
        payments = run("get_payments()", lambda: api.get_payments(results_per_page=3))
        if payments:
            run(f"get_payment({payments[0]['id']})",
                lambda: api.get_payment(payments[0]["id"]))

        # ── Data ──────────────────────────────────────────────────────────────
        section("13. Data")
        run("get_data()", lambda: api.get_data(results_per_page=3))

        # ── Logs ──────────────────────────────────────────────────────────────
        section("14. Logs")
        run("get_logs()", lambda: api.get_logs(results_per_page=3))

        # ── Signatures ────────────────────────────────────────────────────────
        section("15. Email Signatures")
        run("get_signatures()", api.get_signatures)

        # ── Splash Pages ──────────────────────────────────────────────────────
        section("16. Splash Pages")
        sp = run("create_splash_page()", lambda: api.create_splash_page(
            name="Python SDK Splash",
            title="Wait a moment…",
            link_unlock_seconds=5,
        ))
        if sp:
            run("get_splash_pages()", api.get_splash_pages)
            run("get_splash_page(id)", lambda: api.get_splash_page(sp["id"]))
            run("update_splash_page(id)", lambda: api.update_splash_page(
                sp["id"], title="Updated title"
            ))
            run("delete_splash_page(id)",
                lambda: api.delete_splash_page(sp["id"]))


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀  vibes-sdk-python v2 — Production Test Suite")

    test_sync_validation()

    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠  Set API_KEY in example.py to run live tests.")
        sys.exit(0)

    try:
        test_live()
        print("\n✅  All tests finished.\n")
    except VibesAPIError as e:
        print(f"\n💥  Fatal API error [{e.status}]: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥  Fatal error: {e}")
        sys.exit(1)
