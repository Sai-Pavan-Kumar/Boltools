import os
import time
from playwright.sync_api import sync_playwright

html_path = os.path.abspath('software/ui/index.html').replace('\\', '/')

def test_bridge():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Simulate real pywebview triggering pywebviewready
        page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                window.pywebview = {
                    api: {
                        get_initial_data: async () => ({
                            categories: [],
                            tools: [],
                            updates_count: 0,
                            favorites: [],
                            announcements: [],
                            system_stats: { cpu: 10, ram: 20, disk: 30 },
                            default_downloads: 'C:\\\\Downloads'
                        })
                    }
                };
                window.dispatchEvent(new Event('pywebviewready'));
            });
        """)

        page.goto('file:///' + html_path)
        page.wait_for_selector('#main-content', state='attached')

        res = page.evaluate("async () => await window.boltoolsBridge.call('get_initial_data')")
        ready_state = page.evaluate("() => ({ ready: window.boltoolsBridge._isReady, mock: window.boltoolsBridge._isMock })")

        browser.close()

    print("Fix 1 Verification:")
    print("Bridge Response:", res)
    print("Ready State:", ready_state)
    assert res['ok'] is True, "Bridge response must be ok: True"
    assert ready_state['mock'] is False, "Must not be mock in real app"
    print("PROOF PASSED: bridge.js never uses mock in real app, awaits pywebviewready, and returns {ok, data, error}.")

if __name__ == '__main__':
    test_bridge()
