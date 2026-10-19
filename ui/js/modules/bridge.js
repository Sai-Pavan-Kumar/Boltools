/**
 * Boltools Bridge Connector
 * The ONLY file in the UI that touches window.pywebview.api.
 * 
 * Rules:
 * 1. Never use mock data in real app.
 * 2. Waits for 'pywebviewready' event, resolves a ready-promise.
 * 3. Use mock ONLY with ?mock=1 or in a standalone browser with no pywebview after 3s.
 * 4. No timeout (or 5 minutes: 300,000ms) for browse_files, browse_directory,
 *    install_or_update_tool, install_tool, and execute_tool. 5s for fast queries.
 * 5. Return {ok: true, data} or {ok: false, error}; never swallow errors.
 */

const LONG_RUNNING_METHODS = new Set([
  'browse_files',
  'browse_directory',
  'install_or_update_tool',
  'install_tool',
  'execute_tool'
]);

const DEFAULT_TIMEOUT_MS = 5000;
const LONG_TIMEOUT_MS = 300000; // 5 minutes

class Bridge {
  constructor() {
    this._isReady = false;
    this._isMock = false;
    this.ready = new Promise((resolve) => {
      this._resolveReady = resolve;
    });

    this._initReadyListener();
  }

  _initReadyListener() {
    const urlParams = new URLSearchParams(window.location.search);
    const forceMock = urlParams.get('mock') === '1';

    if (forceMock) {
      console.warn('[Bridge] Forced ?mock=1 mode active.');
      this._isMock = true;
      this._isReady = true;
      this._resolveReady({ mode: 'mock' });
      return;
    }

    // Check if pywebview is already available on window
    if (window.pywebview && window.pywebview.api) {
      this._isReady = true;
      this._resolveReady({ mode: 'real' });
      return;
    }

    // Listen for pywebviewready event from WebView2
    const onReady = () => {
      window.removeEventListener('pywebviewready', onReady);
      const existingBanner = document.getElementById('bridge-error-banner');
      if (existingBanner) existingBanner.remove();
      this._isReady = true;
      this._resolveReady({ mode: 'real' });
    };
    window.addEventListener('pywebviewready', onReady);

    const isShellNative = (urlParams.get('shell') === 'native') || Boolean(window.__BOLTOOLS_NATIVE_SHELL__);

    // Fallback handling
    setTimeout(() => {
      if (!this._isReady) {
        if (window.pywebview && window.pywebview.api) {
          onReady();
          return;
        }

        if (isShellNative) {
          // In real shell: NEVER fall back to mock data!
          console.error('[Bridge] Critical: Native desktop shell detected but pywebview API failed to bind within 10s.');
          if (!document.getElementById('bridge-error-banner')) {
            const errBanner = document.createElement('div');
            errBanner.id = 'bridge-error-banner';
            errBanner.className = 'fixed inset-0 z-50 flex flex-col items-center justify-center bg-[var(--surface-base)] text-[var(--text-primary)] p-6 text-center';
            
            const card = document.createElement('div');
            card.className = 'max-w-md p-6 rounded-2xl bg-[var(--surface-card)] border border-red-500/30 shadow-xl';
            card.innerHTML = `
              <div class="w-12 h-12 mx-auto rounded-xl bg-red-500/10 text-red-500 flex items-center justify-center mb-3">⚠️</div>
              <h3 class="text-base font-bold text-[var(--text-primary)]">Desktop Connection Timeout</h3>
              <p class="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
                The native Python engine did not respond in time (antivirus scan or process delay). Mock data has been blocked to prevent state corruption.
              </p>
            `;
            
            const retryBtn = document.createElement('button');
            retryBtn.id = 'btn-retry-connection';
            retryBtn.className = 'mt-4 px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all cursor-pointer';
            retryBtn.textContent = 'Retry Connection';
            retryBtn.addEventListener('click', () => {
              window.location.reload();
            });
            
            card.appendChild(retryBtn);
            errBanner.appendChild(card);
            document.body.appendChild(errBanner);
          }
        } else {
          // Pure external browser dev without ?shell=native
          console.warn('[Bridge] pywebview not detected in standalone browser. Entering mock mode.');
          this._isMock = true;
          this._isReady = true;
          this._resolveReady({ mode: 'mock' });
        }
      }
    }, isShellNative ? 10000 : 3000);
  }

  async call(fnName, ...args) {
    await this.ready;

    if (!this._isMock && window.pywebview && window.pywebview.api) {
      const apiMethod = window.pywebview.api[fnName];
      if (typeof apiMethod !== 'function') {
        const err = `Bridge method '${fnName}' not found on window.pywebview.api`;
        console.error(`[Bridge Error]`, err);
        return { ok: false, data: null, error: err };
      }

      const timeoutMs = LONG_RUNNING_METHODS.has(fnName) ? LONG_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;

      try {
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error(`Bridge call '${fnName}' timed out after ${timeoutMs}ms`)), timeoutMs)
        );
        const res = await Promise.race([
          apiMethod.apply(window.pywebview.api, args),
          timeoutPromise
        ]);
        return { ok: true, data: res, error: null };
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : String(err);
        console.error(`[Bridge Call Failed] ${fnName}:`, errMsg);
        return { ok: false, data: null, error: errMsg };
      }
    }

    // Explicit Mock Mode fallback
    return await this._mockCall(fnName, ...args);
  }

  async _mockCall(fnName, ...args) {
    console.debug(`[Mock Bridge] ${fnName}(${args.map(a => JSON.stringify(a)).join(', ')})`);
    switch (fnName) {
      case 'get_initial_data':
        return {
          ok: true,
          data: {
            categories: [
              { id: "pdf", name: "PDF Studio", desc: "Offline document merging, splitting, compression, and conversion", icon: "file-text", accent: "#DC2626" },
              { id: "video", name: "Media & Video", desc: "Fast offline video compression and extraction", icon: "video", accent: "#2563EB" },
              { id: "image", name: "Image Studio", desc: "Batch WebP compression and format conversion", icon: "image", accent: "#059669" },
              { id: "system", name: "System & Files", desc: "Power file renaming and organization", icon: "sliders", accent: "#475569" }
            ],
            tools: [],
            updates_count: 0,
            favorites: [],
            announcements: [],
            system_stats: { cpu: 12, ram: 42, disk: 35 },
            default_downloads: "C:\\Users\\User\\Downloads"
          },
          error: null
        };
      case 'get_catalog_summary':
        return {
          ok: true,
          data: [
            {
              id: "media_audio_extractor",
              name: "Audio Extractor",
              category_id: "video",
              category_name: "Media & Video",
              description: "Extract clean MP3, WAV, AAC, or FLAC audio tracks from video and audio files locally.",
              icon: "music",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 2,
              update_available: false
            },
            {
              id: "video_compressor",
              name: "Video Compressor",
              category_id: "video",
              category_name: "Media & Video",
              description: "Compress video files with Low, Balanced, and Maximum compression presets.",
              icon: "video",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 25,
              update_available: false
            },
            {
              id: "pdf_merge",
              name: "Merge PDF",
              category_id: "pdf",
              category_name: "PDF Studio",
              description: "Combine multiple PDF files into a single document in your chosen order.",
              icon: "merge",
              status: "installed",
              version: "0.1.0",
              remote_version: "0.1.0",
              size_mb: 4,
              update_available: false
            },
            {
              id: "pdf_split",
              name: "Split PDF",
              category_id: "pdf",
              category_name: "PDF Studio",
              description: "Extract page ranges, single pages, or split into separate PDF documents.",
              icon: "split",
              status: "installed",
              version: "0.1.0",
              remote_version: "0.1.0",
              size_mb: 4,
              update_available: false
            },
            {
              id: "pdf_compress",
              name: "Compress PDF",
              category_id: "pdf",
              category_name: "PDF Studio",
              description: "Reduce PDF file size while preserving high visual and text quality.",
              icon: "minimize-2",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 1,
              update_available: false
            },
            {
              id: "pdf_converter",
              name: "Convert PDF",
              category_id: "pdf",
              category_name: "PDF Studio",
              description: "Convert PDF pages to high-resolution images or compile photos into a PDF.",
              icon: "refresh-cw",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 1,
              update_available: false
            },
            {
              id: "image_webp_compress",
              name: "WebP Image Compressor",
              category_id: "image",
              category_name: "Image Studio",
              description: "Bulk compress photos into web-optimized WebP images with custom quality controls.",
              icon: "image",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 1,
              update_available: false
            },
            {
              id: "system_batch_rename",
              name: "Bulk File Renamer",
              category_id: "system",
              category_name: "System & Files",
              description: "Batch rename files with search & replace, numbering, and extension cleaning.",
              icon: "sliders",
              status: "installed",
              version: "1.0.0",
              remote_version: "1.0.0",
              size_mb: 1,
              update_available: false
            },
            {
              id: "subtitle_animator",
              name: "Subtitle Animation Maker",
              category_id: "video",
              category_name: "Media & Video",
              description: "Burn viral animated caption styles directly into videos with word-level highlights.",
              icon: "subtitles",
              status: "installed",
              version: "1.0.1",
              remote_version: "1.0.1",
              size_mb: 2,
              update_available: false
            }
          ],
          error: null
        };
      case 'get_system_stats':
        return { ok: true, data: { cpu: 15, ram: 44, disk: 36 }, error: null };
      case 'get_announcements':
        return { ok: true, data: [], error: null };
      case 'toggle_favorite':
        return { ok: true, data: [], error: null };
      case 'browse_files':
        return { ok: true, data: [], error: null };
      case 'browse_directory':
        return { ok: true, data: "", error: null };
      case 'clean_cache':
        return { ok: true, data: { success: true, cleaned_files: 0 }, error: null };
      case 'open_file':
      case 'reveal_file':
      case 'open_path':
      case 'open_url':
        return { ok: true, data: true, error: null };
      case 'read_text_file':
        return { ok: true, data: "", error: null };
      case 'cancel_tool':
        return { ok: true, data: true, error: null };
      case 'install_tool':
        return { ok: true, data: true, error: null };
      case 'install_or_update_tool':
        return { ok: true, data: { success: true }, error: null };
      case 'uninstall_tool':
        return { ok: true, data: true, error: null };
      case 'get_tool_details':
        return { ok: true, data: null, error: null };
      default:
        return { ok: false, data: null, error: `Mock method '${fnName}' not implemented` };
    }
  }

  // ── Existing Bridge Contract Signatures returning {ok, data, error} ──
  async getInitialData() { return await this.call('get_initial_data'); }
  async getCatalogSummary() { return await this.call('get_catalog_summary'); }
  async getSystemStats() { return await this.call('get_system_stats'); }
  async getAnnouncements() { return await this.call('get_announcements'); }
  async toggleFavorite(toolId) { return await this.call('toggle_favorite', toolId); }
  async browseFiles(fileTypes) { return await this.call('browse_files', fileTypes); }
  async browseDirectory() { return await this.call('browse_directory'); }
  async openFile(path) { return await this.call('open_file', path); }
  async openUrl(url) { return await this.call('open_url', url); }
  async revealFile(path) { return await this.call('reveal_file', path); }
  async openPath(path) { return await this.call('open_path', path); }
  async readTextFile(path) { return await this.call('read_text_file', path); }
  async cleanCache() { return await this.call('clean_cache'); }
  async installTool(toolId) { return await this.call('install_tool', toolId); }
  async installOrUpdateTool(toolId) { return await this.call('install_or_update_tool', toolId); }
  async uninstallTool(toolId, purgeData = false) { return await this.call('uninstall_tool', toolId, purgeData); }
  async executeTool(toolId, files, options, outDir) { return await this.call('execute_tool', toolId, files, options, outDir); }
  async cancelTool() { return await this.call('cancel_tool'); }
  async getToolDetails(toolId) { return await this.call('get_tool_details', toolId); }
}

const bridge = new Bridge();
window.boltoolsBridge = bridge;
