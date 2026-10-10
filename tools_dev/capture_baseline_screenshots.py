import os
from playwright.sync_api import sync_playwright

HTML_PATH = os.path.abspath("software/ui/index.html")
OUT_DIR = os.path.abspath("docs/screenshots/baseline")

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 840})
        page = context.new_page()

        page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
        page.wait_for_selector("#main-content", state="attached")

        # Home Light
        page.evaluate("() => applyTheme('light')")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(OUT_DIR, "home_light.png"))

        # Home Dark
        page.evaluate("() => applyTheme('dark')")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(OUT_DIR, "home_dark.png"))

        # Tool Hub Dark
        page.evaluate("() => navigateTo('tool_hub')")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(OUT_DIR, "tool_hub_dark.png"))

        # Settings Dark
        page.evaluate("() => navigateTo('settings')")
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(OUT_DIR, "settings_dark.png"))

        browser.close()
    print("Baseline screenshots captured in docs/screenshots/baseline/")

if __name__ == "__main__":
    capture()
