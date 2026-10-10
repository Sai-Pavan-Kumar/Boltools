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
      this._isReady = true;
      this._resolveReady({ mode: 'real' });
    };
    window.addEventListener('pywebviewready', onReady);

    // Fallback ONLY in browser after 3 seconds if pywebview never shows up
    setTimeout(() => {
      if (!this._isReady) {
        if (!window.pywebview) {
          console.warn('[Bridge] pywebview not detected after 3s. Entering browser mock mode.');
          this._isMock = true;
          this._isReady = true;
          this._resolveReady({ mode: 'mock' });
        }
      }
    }, 3000);
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
              { id: "video", name: "Media & Video", desc: "Fast offline video compression and extraction", icon: "video", accent: "#2563EB" },
              { id: "pdf", name: "PDF Studio", desc: "Offline conversion, splitting, and merging", icon: "file-text", accent: "#DC2626" },
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
        return { ok: true, data: [], error: null };
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
