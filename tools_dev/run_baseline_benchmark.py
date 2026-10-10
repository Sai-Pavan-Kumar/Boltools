"""Baseline Measurement Runner using Playwright (Chromium Headless).

Simulates the WebView2 environment loading c:/Projects/boltools/software/ui/index.html.
Measures:
- Network requests made at startup
- Time to First Paint (FCP)
- Time to Usable (DOM ready / initial sync)
- DOM Node count at 100, 1,000, and 10,000 tools
- JS Heap size at 100, 1,000, and 10,000 tools
- Frame duration during scroll at 100, 1,000, and 10,000 tools
- Search latency per keystroke
"""

import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

candidates = [
    os.path.abspath("ui/index.html"),
    os.path.abspath("software/ui/index.html"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../ui/index.html"))
]
HTML_PATH = next((p for p in candidates if os.path.exists(p)), candidates[0])


def measure_startup_and_network():
    print("--- 1. Measuring Startup & Network Requests ---")
    requests_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.on("request", lambda req: requests_log.append({
            "url": req.url,
            "resource_type": req.resource_type,
            "method": req.method
        }))

        t0 = time.perf_counter()
        page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
        page.wait_for_selector("#main-content", state="attached")
        t_usable = (time.perf_counter() - t0) * 1000

        # Retrieve performance timing
        metrics = page.evaluate("""() => {
            const paintEntries = performance.getEntriesByType('paint');
            const fcp = paintEntries.find(e => e.name === 'first-contentful-paint');
            const fp = paintEntries.find(e => e.name === 'first-paint');
            return {
                fp: fp ? fp.startTime : null,
                fcp: fcp ? fcp.startTime : null,
                domNodes: document.getElementsByTagName('*').length,
                heapMb: performance.memory ? (performance.memory.usedJSHeapSize / (1024 * 1024)) : null
            };
        }""")

        browser.close()

    return {
        "time_to_usable_ms": t_usable,
        "first_paint_ms": metrics.get("fp") or metrics.get("fcp"),
        "first_contentful_paint_ms": metrics.get("fcp"),
        "initial_dom_nodes": metrics.get("domNodes"),
        "initial_heap_mb": metrics.get("heapMb"),
        "network_requests": requests_log
    }


def measure_tool_hub_scale(count: int):
    catalog_path = os.path.abspath(f"tools_dev/catalog_{count}.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        tools_data = json.load(f)["tools"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Inject pywebview bridge simulation BEFORE page scripts run
        page.add_init_script(f"""
            window.pywebview = {{
                api: {{
                    get_initial_data: async () => {{
                        return {{
                            categories: [
                                {{ id: "video", name: "Media & Video", desc: "Fast offline video", icon: "video", accent: "#2563EB" }},
                                {{ id: "pdf", name: "PDF Studio", desc: "Offline conversion", icon: "file-text", accent: "#DC2626" }},
                                {{ id: "image", name: "Image Studio", desc: "Batch WebP", icon: "image", accent: "#059669" }},
                                {{ id: "system", name: "System & Files", desc: "Power file renaming", icon: "sliders", accent: "#475569" }}
                            ],
                            tools: {json.dumps(tools_data)},
                            updates_count: 5,
                            favorites: [],
                            announcements: [],
                            system_stats: {{ cpu: 15, ram: 42, disk: 30 }},
                            default_downloads: "C:\\\\Users\\\\Test\\\\Downloads"
                        }};
                    }},
                    get_system_stats: async () => ({{ cpu: 15, ram: 42, disk: 30 }}),
                    get_announcements: async () => ([])
                }}
            }};
        """)

        page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
        page.wait_for_selector("#main-content", state="attached")

        # Navigate to Tool Hub view
        t_nav0 = time.perf_counter()
        page.evaluate("() => navigateTo('tool_hub')")
        page.wait_for_selector(".grid", state="attached")
        t_render_hub = (time.perf_counter() - t_nav0) * 1000

        # Measure DOM Nodes and Heap
        stats = page.evaluate("""() => {
            return {
                domNodes: document.getElementsByTagName('*').length,
                heapMb: performance.memory ? (performance.memory.usedJSHeapSize / (1024 * 1024)) : null
            };
        }""")

        # Measure Scroll Frame Timings
        scroll_stats = page.evaluate("""async () => {
            const container = document.getElementById('main-content');
            const frameDurations = [];
            let lastTime = performance.now();
            let framesOver50 = 0;

            const measureFrames = () => {
                const now = performance.now();
                const delta = now - lastTime;
                frameDurations.push(delta);
                if (delta > 50) framesOver50++;
                lastTime = now;
            };

            // Scroll down in steps while measuring rAF
            for (let step = 0; step < 20; step++) {
                container.scrollTop += 500;
                await new Promise(r => requestAnimationFrame(r));
                measureFrames();
            }

            const maxDelta = Math.max(...frameDurations);
            const avgDelta = frameDurations.reduce((a, b) => a + b, 0) / frameDurations.length;
            const approxFps = Math.min(60, 1000 / avgDelta);

            return {
                maxFrameMs: maxDelta,
                avgFrameMs: avgDelta,
                approxFps: approxFps,
                framesOver50: framesOver50
            };
        }""")

        # Measure Search Latency
        search_stats = page.evaluate("""() => {
            const input = document.getElementById('hub-search-input');
            const queries = ['Comp', 'PDF', 'ఆడియో', 'ఫోటో', 'టూల్', 'वीडियो'];
            const latencies = [];

            queries.forEach(q => {
                const t0 = performance.now();
                if (input) {
                    input.value = q;
                    handleHubSearch(q);
                }
                const t1 = performance.now();
                latencies.push(t1 - t0);
            });

            return {
                avgSearchMs: latencies.reduce((a, b) => a + b, 0) / latencies.length,
                maxSearchMs: Math.max(...latencies)
            };
        }""")

        browser.close()

    return {
        "count": count,
        "render_hub_ms": t_render_hub,
        "dom_nodes": stats["domNodes"],
        "heap_mb": stats["heapMb"],
        "max_frame_ms": scroll_stats["maxFrameMs"],
        "approx_fps": scroll_stats["approxFps"],
        "frames_over_50ms": scroll_stats["framesOver50"],
        "avg_search_ms": search_stats["avgSearchMs"],
        "max_search_ms": search_stats["maxSearchMs"]
    }


def main():
    print("==================================================")
    print("BOLTOOLS PERFORMANCE BASELINE BENCHMARK (MILESTONE 0)")
    print("==================================================")

    startup = measure_startup_and_network()
    print(f"Startup Time to Usable: {startup['time_to_usable_ms']:.2f} ms")
    print(f"First Paint: {startup['first_paint_ms']} ms")
    print(f"Network Requests on Startup: {len(startup['network_requests'])}")
    for r in startup["network_requests"]:
        print(f"  -> [{r['resource_type']}] {r['url']}")

    results = []
    for count in [100, 1000, 10000]:
        print(f"\n--- Measuring Scale: {count} Tools in Tool Hub ---")
        res = measure_tool_hub_scale(count)
        results.append(res)
        print(f"  DOM Nodes: {res['dom_nodes']:,}")
        print(f"  JS Heap: {res['heap_mb']:.2f} MB")
        print(f"  Render Hub Time: {res['render_hub_ms']:.2f} ms")
        print(f"  Max Scroll Frame: {res['max_frame_ms']:.2f} ms | Approx FPS: {res['approx_fps']:.1f}")
        print(f"  Frames > 50ms: {res['frames_over_50ms']}")
        print(f"  Avg Search Latency: {res['avg_search_ms']:.2f} ms | Max: {res['max_search_ms']:.2f} ms")

    summary_file = "docs/perf/baseline_raw.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({"startup": startup, "scale": results}, f, indent=2)
    print(f"\nRaw results saved to {summary_file}")


if __name__ == "__main__":
    main()
