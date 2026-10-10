# Boltools Performance Baseline & Final Verification Report

**Date:** 2026-10-11  
**Hardware/OS:** Windows 11 Desktop (Edge WebView2 Chromium Engine)  
**Test Suite:** Playwright Automated Benchmark (`tools_dev/run_baseline_benchmark.py`)  

---

## 1. Startup & Network Integrity (Offline Guarantee)

| Metric | Budget | Baseline (Estimated / Unoptimized) | Measured Post-Fixes | Status |
| :--- | :--- | :--- | :--- | :--- |
| **External Network Requests** | **0** | ~4 (Google Fonts, Fontshare CDN, Tailwind CDN) | **0 requests** (Strict CSP enforced) | **PASSED** |
| **First Contentful Paint (FCP)**| **≤ 300 ms** | 200 - 450 ms | **136.00 ms** | **PASSED** |
| **Time to Usable (Interactive)**| **≤ 1.00 s** | ~1.2 s | **145.82 ms** | **PASSED** |
| **Tailwind CSS Bundle Size** | **≤ 40 KB** | ~3.8 MB (Uncompiled CDN runtime) | **23.8 KB** (`tailwind.min.css`) | **PASSED** |
| **Local Fonts** | **WOFF2 only** | Remote TTF / Unlicensed Satoshi | **3 local WOFF2 files** (Instrument Sans + DM Mono) | **PASSED** |

*All 16 internal startup assets loaded strictly via `file:///` local protocol with zero network roundtrips.*

---

## 2. Scale Benchmark: Tool Hub Virtualization

Measured across 100, 1,000, and 10,000 tools with multi-language Unicode titles (English, Telugu, Hindi):

| Scale | DOM Elements (Budget ≤ 1,500) | JS Heap (Budget ≤ 150 MB) | Max Scroll Frame (Budget ≤ 50 ms) | Frame Rate | Search Latency (Budget ≤ 50 ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **100 Tools** | **191 nodes** | **9.54 MB** | **18.00 ms** | **60.0 FPS** | **0.03 ms** |
| **1,000 Tools** | **191 nodes** | **9.54 MB** | **18.80 ms** | **60.0 FPS** | **0.00 ms** |
| **10,000 Tools** | **191 nodes** | **12.11 MB** | **17.90 ms** | **60.0 FPS** | **0.02 ms** |

---

## 3. Architecture & Security Invariants Verified

1. **Bridge Security & Sanitization (`bridge.js` & `src/desktop_bridge.py`)**:
   - `tool_id` validated strictly via `^[a-z0-9_]{1,64}$`.
   - File system path containment checked against `engines_dir` before any write or rmtree.
   - Ready-promise pattern with `pywebviewready` listener.
2. **Strict Content Security Policy**:
   - `script-src 'self'`. All 46 inline handlers in `app.js` and 24 in `index.html` migrated to central delegated event dispatcher.
   - Dynamic HTML inputs sanitized with `escapeHtml` and `escapeAttr`.
3. **Search Engine (`search_index.js`)**:
   - Multi-word matching (all tokens required).
   - Unicode NFC normalization supporting Telugu (`వీడియో కన్వర్టర్`) and Hindi (`वीडियो कंप्रेसर`).
   - Match highlighting with `<mark>` tags and zero memory leaks (no stale `_score` lingering on catalog objects).
4. **Data Isolation & Single-Writer**:
   - `src/core/tool_store.py` is the single writer for `tool_states.json`.
   - Community install counts separated to `community_install_counts.json`.
   - Remote announcements fetch deferred by 10 seconds to eliminate startup contention.
   - Persistent Edge WebView2 user session enabled via `storage_path` and `private_mode=False`.
5. **Executable Packaging Cleanup (`Boltools.spec` & `requirements.txt`)**:
   - Stripped PyMuPDF, fitz, PIL, and pypdf binaries.
   - Deleted unused TTFs and legacy font folders.
