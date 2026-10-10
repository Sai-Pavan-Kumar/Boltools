import os
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()

        csp_errors = []
        page_errors = []
        
        page.on("console", lambda msg: (
            csp_errors.append(msg.text) if ("Content-Security-Policy" in msg.text or "violates" in msg.text)
            else page_errors.append(msg.text) if msg.type == "error"
            else None
        ))
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        index_path = os.path.abspath("software/ui/index.html")
        file_url = f"file:///{index_path.replace(os.sep, '/')}?mock=1"
        print(f"Loading {file_url} ...")

        page.goto(file_url)
        # Wait 500ms for initApp to render
        page.wait_for_timeout(500)

        # 1. Verify Page Title
        title = page.title()
        print(f"Title: {title}")

        # 2. Test Delegated Navigation to Tool Hub
        print("Testing delegated navigation to Tool Hub...")
        page.click('[data-action="nav"][data-view="tool_hub"]')
        page.wait_for_timeout(300)
        h2 = page.inner_text("h2")
        print(f"Current View H2: {h2}")
        assert "Tool Hub" in h2, "Navigation to Tool Hub failed"

        # 3. Test Delegated Hub Search Input
        print("Testing delegated hub search...")
        page.fill('#hub-search-input', 'PDF')
        page.wait_for_timeout(200)

        # 4. Test Delegated Command Palette
        print("Testing Command Palette trigger...")
        page.click('[data-action="open-cmd-palette"]')
        page.wait_for_timeout(200)
        assert page.is_visible('#modal-command-palette'), "Command palette should be visible"

        print("Testing Command Palette close...")
        page.click('[data-action="close-cmd"]')
        page.wait_for_timeout(200)
        assert not page.is_visible('#modal-command-palette'), "Command palette should be hidden"

        # 5. Test Delegated Theme Switcher
        print("Testing Theme Switcher...")
        html_theme_before = page.get_attribute("html", "data-theme")
        page.click('[data-action="toggle-theme"]')
        page.wait_for_timeout(200)
        html_theme_after = page.get_attribute("html", "data-theme")
        print(f"Theme toggle: {html_theme_before} -> {html_theme_after}")
        assert html_theme_before != html_theme_after, "Theme did not toggle"

        # 6. Audit CSP & Console
        print("\n--- CSP & CONSOLE AUDIT ---")
        print(f"CSP Violations: {len(csp_errors)}")
        for e in csp_errors:
            print(f"  [CSP ERROR] {e}")

        print(f"Script/Page Errors: {len(page_errors)}")
        for e in page_errors:
            print(f"  [ERROR] {e}")

        assert len(csp_errors) == 0, f"CSP errors found: {csp_errors}"
        assert len(page_errors) == 0, f"Page errors found: {page_errors}"

        print("\nAll Fix 2 tests PASSED successfully with script-src 'self' and zero inline handlers!")
        browser.close()

if __name__ == "__main__":
    main()
