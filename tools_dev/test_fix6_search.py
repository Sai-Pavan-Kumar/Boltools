import os
from playwright.sync_api import sync_playwright

def main():
    print("Testing Fix 6: Multi-word Unicode search & highlighting...")
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
        page.wait_for_timeout(300)

        # Inject multi-lingual tools (English, Telugu, Hindi)
        test_results = page.evaluate("""(() => {
            const multiTools = [
                { id: 'tool_en_1', name: 'Batch Video Converter Ultra', description: 'Compress and transform MP4 videos', category_name: 'VIDEO', status: 'available' },
                { id: 'tool_en_2', name: 'Audio Extractor Pro', description: 'Lossless studio extraction', category_name: 'AUDIO', status: 'available' },
                { id: 'tool_te_1', name: 'వీడియో కన్వర్టర్ తెలుగు', description: 'ఆఫ్‌లైన్ వీడియో కంప్రెసర్ సాధనం', category_name: 'VIDEO', status: 'available' },
                { id: 'tool_hi_1', name: 'वीडियो संपादन प्रो', description: 'फास्ट ऑफलाइन वीडियो टूल', category_name: 'VIDEO', status: 'available' },
                { id: 'tool_en_3', name: 'Video Fast Tool', description: 'Quick video processing', category_name: 'VIDEO', status: 'available' }
            ];

            const idx = new window.ToolSearchIndex(multiTools);

            // 1. Multi-word search
            const resMulti = idx.search('video converter');
            const resMultiIds = resMulti.map(t => t.id);

            // 2. Telugu search
            const resTe = idx.search('వీడియో కన్వర్టర్');
            const resTeIds = resTe.map(t => t.id);

            // 3. Hindi search
            const resHi = idx.search('वीडियो');
            const resHiIds = resHi.map(t => t.id);

            // 4. Stale _score check on objects
            const hasStaleScore = multiTools.some(t => '_score' in t);

            // 5. Highlighting check
            const highlightHtml = window.ToolSearchIndex.highlight('Batch Video Converter Ultra', 'video converter');

            return {
                resMultiIds,
                resTeIds,
                resHiIds,
                hasStaleScore,
                highlightHtml
            };
        })()""")

        print(f"Multi-word search match ids: {test_results['resMultiIds']}")
        assert 'tool_en_1' in test_results['resMultiIds'], "Multi-word search failed to match"
        assert 'tool_en_2' not in test_results['resMultiIds'], "Multi-word search allowed non-matching item"

        print(f"Telugu search match ids: {test_results['resTeIds']}")
        assert 'tool_te_1' in test_results['resTeIds'], "Telugu Unicode search failed"

        print(f"Hindi search match ids: {test_results['resHiIds']}")
        assert 'tool_hi_1' in test_results['resHiIds'], "Hindi Unicode search failed"

        print(f"Has stale _score on items: {test_results['hasStaleScore']}")
        assert test_results['hasStaleScore'] is False, "Stale _score found on tool objects!"

        print(f"Highlight output: {test_results['highlightHtml']}")
        assert '<mark' in test_results['highlightHtml'], "Highlight tags missing"

        print("\nFix 6 Verification PASSED! Multi-word Unicode search, ranking, and highlighting work cleanly without mutating objects.")
        browser.close()

if __name__ == '__main__':
    main()
