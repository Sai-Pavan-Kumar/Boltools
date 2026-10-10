import os
from playwright.sync_api import sync_playwright

def main():
    print("Testing VirtualGrid with 10,000 synthetic tools...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()

        candidates = [
            os.path.abspath("ui/index.html"),
            os.path.abspath("software/ui/index.html"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../software/ui/index.html"))
        ]
        index_path = next((p for p in candidates if os.path.exists(p)), candidates[0])
        file_url = f"file:///{index_path.replace(os.sep, '/')}?mock=1"
        page.goto(file_url)
        page.wait_for_timeout(500)

        # Generate 10,000 synthetic tools into state.tools & re-render Tool Hub
        eval_setup = page.evaluate("""(() => {
            const categories = ['video', 'pdf', 'image', 'system'];
            const names = ['Converter', 'Compressor', 'Optimizer', 'Harvester', 'Extractor', 'Studio', 'Utility', 'Engine'];
            const synthetic = [];
            for (let i = 1; i <= 10000; i++) {
                const cat = categories[i % categories.length];
                const baseName = names[i % names.length];
                synthetic.push({
                    id: `tool_${i}`,
                    name: `${baseName} Ultra #${i}`,
                    category_id: cat,
                    category_name: cat.toUpperCase(),
                    description: `High performance offline tool number ${i} for creator power workflows.`,
                    icon: 'sliders',
                    status: (i % 3 === 0) ? 'installed' : 'available',
                    version: '1.0.0',
                    remote_version: '1.0.0',
                    size_mb: 25,
                    update_available: false
                });
            }
            window.state.tools = synthetic;
            window.activeSearchIndex = new ToolSearchIndex(synthetic);
            window.navigateTo('tool_hub');
            return synthetic.length;
        })()""")

        print(f"Loaded synthetic tools count: {eval_setup}")
        page.wait_for_timeout(500)

        # 1. Measure DOM Node count
        dom_node_count = page.evaluate("() => document.querySelectorAll('*').length")
        cards_count = page.evaluate("() => document.querySelectorAll('[data-card-idx]').length")
        print(f"Total DOM Nodes with 10,000 tools: {dom_node_count} (Budget: <= 1,500)")
        print(f"Visible Rendered Cards: {cards_count}")
        assert dom_node_count <= 1500, f"DOM node count exceeded budget: {dom_node_count}"

        # 2. Test Scroll & Virtual Re-slicing
        print("Testing fast scroll down to row 500...")
        page.evaluate("() => { const v = document.getElementById('virtual-grid-viewport'); v.scrollTop = 50000; }")
        page.wait_for_timeout(300)

        new_cards_count = page.evaluate("() => document.querySelectorAll('[data-card-idx]').length")
        new_dom_node_count = page.evaluate("() => document.querySelectorAll('*').length")
        first_card_idx = page.evaluate("() => parseInt(document.querySelector('[data-card-idx]').getAttribute('data-card-idx'), 10)")
        print(f"Scrolled Viewport - First Visible Card Index: {first_card_idx}")
        print(f"Scrolled Total DOM Nodes: {new_dom_node_count}")
        assert first_card_idx > 100, f"Virtual scrolling did not slice down: {first_card_idx}"
        assert new_dom_node_count <= 1500, f"DOM node count exceeded budget after scroll: {new_dom_node_count}"

        # 3. Test Keyboard Navigation (ArrowDown & ArrowRight)
        print("Testing keyboard navigation...")
        page.focus('#virtual-grid-viewport')
        page.keyboard.press('ArrowDown')
        page.wait_for_timeout(100)
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(100)
        active_card = page.evaluate("() => document.activeElement ? document.activeElement.getAttribute('data-card-idx') : null")
        print(f"Active focused card index via keyboard: {active_card}")
        assert active_card is not None, "Keyboard navigation did not focus a card"

        # 4. Test Scroll Position Restoration across view navigation
        print("Testing scroll position restoration...")
        # Save current scrollTop
        scroll_before = page.evaluate("() => document.getElementById('virtual-grid-viewport').scrollTop")
        # Navigate away to Home
        page.click('[data-action="nav"][data-view="home"]')
        page.wait_for_timeout(300)
        # Navigate back to Tool Hub
        page.click('[data-action="nav"][data-view="tool_hub"]')
        page.wait_for_timeout(300)
        scroll_restored = page.evaluate("() => document.getElementById('virtual-grid-viewport').scrollTop")
        print(f"Scroll before nav: {scroll_before}, Scroll restored: {scroll_restored}")
        assert abs(scroll_before - scroll_restored) < 50, f"Scroll position not restored properly: {scroll_before} vs {scroll_restored}"

        print("\nFix 5 Verification PASSED! VirtualGrid smoothly handles 10,000 tools with DOM count <= 1500, keyboard navigation, and scroll restoration.")
        browser.close()

if __name__ == "__main__":
    main()
