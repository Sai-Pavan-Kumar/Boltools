# Boltools Performance Baseline & Final Verification Report

**Date:** 2026-10-11  
**Hardware/OS:** Windows 11 Desktop (Edge WebView2 Chromium Engine)  
**Test Suite:** Playwright Automated Scale Benchmark (`tools_dev/run_baseline_benchmark.py`)  

---

## 1. Startup & Network Integrity (Offline Guarantee)

| Metric | Budget | Status | Measured Post-Fixes | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **External Network Requests** | **0** | **0 requests** | 0 requests (Strict CSP `script-src 'self'`) | **PASSED** |
| **First Contentful Paint (FCP)**| **≤ 300 ms** | **152 ms** | 152.00 ms | **PASSED** |
| **Time to Usable (Interactive)**| **≤ 1.00 s** | **158.79 ms** | 158.79 ms | **PASSED** |
| **Tailwind CSS Minified Size** | **≤ 40 KB** | **23.8 KB** | 23.8 KB (`ui/css/tailwind.min.css`) | **PASSED** |
| **Local Fonts** | **WOFF2 only** | **3 WOFF2 files** | Instrument Sans Variable + DM Mono (Local) | **PASSED** |

*All 16 internal startup assets loaded strictly via `file:///` local protocol with zero network roundtrips.*

---

## 2. Scale Benchmark: Tool Hub Virtualization

Measured across 100, 1,000, and 10,000 tools with on-demand multi-language Unicode titles (English, Telugu, Hindi):

| Scale | DOM Elements (Budget ≤ 1,500) | Rendered Cards in DOM | JS Heap (Budget ≤ 150 MB) | Max Scroll Frame (Budget ≤ 50 ms) | Frame Rate (Budget 60 FPS) | Search Algorithm Latency (Budget ≤ 50 ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **100 Tools** | **564 nodes** | 18 cards | **9.54 MB** | **17.70 ms** | **60.0 FPS** | **0.18 ms** (Max: 0.40 ms) |
| **1,000 Tools** | **564 nodes** | 18 cards | **9.54 MB** | **34.20 ms** | **56.3 FPS** | **1.52 ms** (Max: 6.00 ms) |
| **10,000 Tools** | **564 nodes** | 18 cards | **16.31 MB** | **32.80 ms** | **58.1 FPS** | **6.15 ms** (Max: 8.30 ms) |

---

## 3. Architecture & Security Invariants Verified

1. **Native Shell Handshake & Antivirus Timeout Protection (`bridge.js` & `main.py`)**:
   - `main.py` launches WebView2 with `?shell=native`.
   - `bridge.js` strictly forbids falling back to mock mode if running in native shell.
   - If antivirus or Windows process delay exceeds 10s, a clean error screen is presented with a "Retry Connection" action instead of silently corrupting state with mock data.
2. **Strict HTML & Attribute Sanitization (`app.js`)**:
   - All 13 previous raw `${t.name}`, `${t.description}`, and `${t.category_name}` interpolations across Recent Rows, Bento Grid, Hub cards, Favorites view, and Command Palette are strictly escaped via `escapeHtml()`.
3. **SHA256 Integrity Verification on Downloads (`src/core/tool_store.py`)**:
   - When an engine is downloaded over-the-air, its SHA256 hash is computed and verified against `meta['sha256']` before atomic installation.
4. **Search Engine Benchmark Validity**:
   - Direct synchronous search algorithm throughput on the active index (`activeSearchIndex.search`) accurately clocks in at **6.15 ms** for 10,000 multi-lingual tools.
   - Scroll frame duration is measured inside `#virtual-grid-viewport`.
5. **Clean Repository (Zero Synthetic Data Bloat)**:
   - Synthetic catalogs (`catalog_*.json`) are generated in-memory on demand and added to `.gitignore`.
