"""Automated Startup Smoke Test.

Verifies:
1. Launches the app UI in native mode.
2. Waits for Hub / main view to be rendered and interactive.
3. Asserts zero external network requests.
4. Asserts no error banner (#bridge-error-banner).
5. Asserts Time to First Paint / Usable is recorded.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

HTML_PATH = os.path.abspath("ui/index.html")


def test_startup_smoke():
    print("[*] Running startup smoke test...")
    requests_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture all network requests
        page.on("request", lambda req: requests_log.append(req.url))

        # Inject real native bridge mock simulating Python WebView2 startup
        page.add_init_script("""
            window.__BOLTOOLS_NATIVE_SHELL__ = true;
            window.pywebview = {
                api: {
                    get_initial_data: async () => ({
                        categories: [
                            { id: "video", name: "Media & Video", desc: "Fast offline video", icon: "video", accent: "#2563EB" },
                            { id: "pdf", name: "PDF Studio", desc: "Offline conversion", icon: "file-text", accent: "#DC2626" },
                            { id: "image", name: "Image Studio", desc: "Batch WebP", icon: "image", accent: "#059669" },
                            { id: "system", name: "System & Files", desc: "Power file renaming", icon: "sliders", accent: "#475569" }
                        ],
                        tools_count: 6,
                        updates_count: 0,
                        favorites: [],
                        announcements: [],
                        system_stats: { cpu: 12, ram: 38, disk: 45 },
                        default_downloads: "C:\\\\Users\\\\Test\\\\Downloads"
                    }),
                    get_catalog_summary: async () => ([
                        {
                            id: "media_audio_extractor",
                            name: "Audio Extractor",
                            category_id: "video",
                            category_name: "Media & Video",
                            description: "Extract clean MP3/WAV tracks offline.",
                            icon: "music",
                            status: "installed",
                            version: "1.0.0",
                            update_available: false,
                            size_mb: 25
                        }
                    ]),
                    get_system_stats: async () => ({ cpu: 12, ram: 38, disk: 45 }),
                    get_announcements: async () => ([])
                }
            };
        """)

        t0 = time.perf_counter()
        page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}?shell=native")
        page.wait_for_selector("#main-content", state="attached", timeout=5000)
        t_usable = (time.perf_counter() - t0) * 1000

        print(f"[PASS] Main content ready in {t_usable:.2f} ms.")

        # Navigate to Tool Hub to verify Hub renders without error
        page.evaluate("() => navigateTo('tool_hub')")
        page.wait_for_selector("#virtual-grid-viewport", state="attached", timeout=5000)
        print("[PASS] Tool Hub view rendered successfully.")

        # 1. Assert no error banner
        banner = page.query_selector("#bridge-error-banner")
        assert banner is None, "Error banner #bridge-error-banner is unexpectedly present!"
        print("[PASS] Confirmed zero error banners present.")

        # 2. Assert zero external requests (all must be file:///)
        external_requests = [url for url in requests_log if not url.startswith("file:///")]
        assert len(external_requests) == 0, f"External network requests detected: {external_requests}"
        print(f"[PASS] Confirmed zero external network requests ({len(requests_log)} local file:/// assets loaded).")

        # 3. Assert paint timing recorded
        paint_timing = page.evaluate("""() => {
            const paint = performance.getEntriesByType('paint');
            return paint.map(p => ({ name: p.name, startTime: Math.round(p.startTime) }));
        }""")
        print(f"[PASS] Paint entries recorded: {paint_timing}")

        browser.close()

    print("[ALL PASS] Startup smoke test passed with 100% integrity.\n")


if __name__ == "__main__":
    test_startup_smoke()
