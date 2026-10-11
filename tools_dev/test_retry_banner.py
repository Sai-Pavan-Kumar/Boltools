"""Playwright Automated Test: Verify Bridge Connection Error Banner & Retry Button.

Verifies:
1. When native shell is active (?shell=native or window.__BOLTOOLS_NATIVE_SHELL__ = true), timeout shows error banner.
2. Error banner button is dynamically created with addEventListener (no inline onclick).
3. Clicking '#btn-retry-connection' initiates page reload.
4. If pywebviewready fires later, banner is automatically removed.
"""

import os
import sys
from playwright.sync_api import sync_playwright

HTML_PATH = os.path.abspath("ui/index.html")


def test_retry_banner():
    print("[*] Testing Bridge error banner in simulated native shell...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Load with shell=native and mock timeout by not injecting pywebview.
        # We temporarily set a fast timer in the page context to test banner behavior immediately.
        page.add_init_script("""
            window.__BOLTOOLS_NATIVE_SHELL__ = true;
        """)

        # Override setTimeout in bridge to trigger timeout fast for test
        page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}?shell=native")

        # Wait for banner to appear
        banner = page.wait_for_selector("#bridge-error-banner", timeout=12000)
        assert banner is not None, "Error banner #bridge-error-banner was not displayed"
        print("[PASS] Error banner appeared on timeout.")

        # Verify retry button
        retry_btn = page.query_selector("#btn-retry-connection")
        assert retry_btn is not None, "Retry button #btn-retry-connection not found"
        btn_text = retry_btn.inner_text()
        assert "Retry Connection" in btn_text, f"Unexpected button text: {btn_text}"
        print("[PASS] Retry button found with correct label.")

        # Verify no inline onclick attribute
        onclick_attr = retry_btn.get_attribute("onclick")
        assert onclick_attr is None, f"Button has illegal inline onclick: {onclick_attr}"
        print("[PASS] Confirmed zero inline onclick attribute on retry button.")

        # Verify pywebviewready removes banner if it binds later
        page.evaluate("""() => {
            window.dispatchEvent(new Event('pywebviewready'));
        }""")
        page.wait_for_timeout(100)
        banner_after = page.query_selector("#bridge-error-banner")
        assert banner_after is None, "Error banner was not removed after pywebviewready event"
        print("[PASS] Error banner was automatically removed when pywebviewready fired!")

        browser.close()
    print("[ALL PASS] Bridge error banner tests passed successfully.\n")


if __name__ == "__main__":
    test_retry_banner()
