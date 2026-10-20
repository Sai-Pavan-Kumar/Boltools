/**
 * Boltools Desktop Client Application Controller (Option 1 Architecture)
 * 100% Offline, Pixel-Perfect Linear / Apple Standard
 */

// ── Default Fallback Categories & Tools (Immediate 0ms Offline Render) ────────
const DEFAULT_CATEGORIES = [
  { id: "pdf", name: "PDF Studio", desc: "Offline document merging, splitting, compression, and conversion", icon: "file-text", accent: "#DC2626" },
  { id: "video", name: "Media & Video", desc: "Fast offline video compression, extraction, and formatting", icon: "video", accent: "#2563EB" },
  { id: "image", name: "Image Studio", desc: "Batch WebP compression, target sizing, and format switching", icon: "image", accent: "#059669" },
  { id: "system", name: "System & Files", desc: "Power file renaming, extension repair, and organization", icon: "sliders", accent: "#475569" }
];

// Offline Default Tools for instantaneous 0ms startup
const DEFAULT_TOOLS = [
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
    description: "Combine multiple PDF documents into a single file in your desired order.",
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
    description: "Extract page ranges or split each page into independent PDF documents.",
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
];

// ── Application State ────────────────────────────────────────────────────────
const state = (window.boltoolsStore && window.boltoolsStore.state) ? window.boltoolsStore.state : {
  theme: localStorage.getItem('boltools-theme') || 'light',
  currentView: 'home',
  activeToolId: null,
  navHistory: [{ view: 'home', toolId: null }],
  categories: DEFAULT_CATEGORIES,
  tools: DEFAULT_TOOLS,
  favorites: [],
  recentTools: JSON.parse(localStorage.getItem('boltools-recent-tools') || '[]'),
  recentFiles: JSON.parse(localStorage.getItem('boltools-recent-files') || '[]'),
  lastOutputFile: null,
  customOutputDir: '',
  announcements: [],
  unreadAnnouncementsCount: 0,
  systemStats: { cpu: 12, ram: 45, disk: 38 },
  defaultDownloads: '',
  searchQuery: '',
  hubFilterTab: 'All', // 'All', 'Installed', 'Hub Catalog'
  selectedFiles: [],
  activeToolOptions: {},
  isToolRunning: false
};
if (window.boltoolsStore) {
  window.boltoolsStore.update(state);
}

function recordRecentTool(toolId) {
  if (!toolId) return;
  let list = (state.recentTools || []).filter(id => id !== toolId);
  list.unshift(toolId);
  list = list.slice(0, 5);
  state.recentTools = list;
  try {
    localStorage.setItem('boltools-recent-tools', JSON.stringify(list));
  } catch (e) {}
}

function recordRecentFile(fileInfo) {
  if (!fileInfo || !fileInfo.path) return;
  let list = (state.recentFiles || []).filter(f => f.path !== fileInfo.path);
  list.unshift(fileInfo);
  list = list.slice(0, 10);
  state.recentFiles = list;
  try {
    localStorage.setItem('boltools-recent-files', JSON.stringify(list));
  } catch (e) {}
}

// ── Bridge Communication Helpers ─────────────────────────────────────────────
async function callBridge(fnName, ...args) {
  if (window.boltoolsBridge) {
    const res = await window.boltoolsBridge.call(fnName, ...args);
    if (res && res.ok) {
      return res.data;
    }
    if (res && !res.ok) {
      console.error(`[callBridge Error] ${fnName}:`, res.error);
    }
    return null;
  }
  console.error(`[callBridge Error] boltoolsBridge not initialized on window.`);
  return null;
}

// ── Theme Management ─────────────────────────────────────────────────────────
function applyTheme(themeMode) {
  state.theme = themeMode;
  localStorage.setItem('boltools-theme', themeMode);
  document.documentElement.setAttribute('data-theme', themeMode);
  if (themeMode === 'light') {
    document.documentElement.classList.remove('dark');
  } else {
    document.documentElement.classList.add('dark');
  }

  // Update theme toggle icon
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (themeBtn) {
    themeBtn.innerHTML = themeMode === 'light' ? getIcon('moon') : getIcon('sun');
  }
}

function toggleTheme() {
  const next = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
}

// ── View Navigation ──────────────────────────────────────────────────────────
function navigateTo(viewName, toolId = null, pushHistory = true) {
  state.currentView = viewName;
  state.activeToolId = toolId;
  if (pushHistory) {
    const last = state.navHistory[state.navHistory.length - 1];
    const lastView = typeof last === 'string' ? last : (last ? last.view : null);
    const lastTool = typeof last === 'object' && last ? last.toolId : null;
    if (lastView !== viewName || lastTool !== toolId) {
      state.navHistory.push({ view: viewName, toolId });
    }
  }

  // Determine active category for sidebar highlighting
  let activeCatId = null;
  if (viewName === 'category_view') {
    activeCatId = toolId;
  } else if (viewName === 'tool_studio') {
    const tool = state.tools.find(t => t.id === toolId);
    if (tool) activeCatId = tool.category_id;
  }
  state.activeCategoryId = activeCatId;

  // Update Main Navigation Sidebar Buttons
  document.querySelectorAll('.sidebar-nav-btn').forEach(btn => {
    const key = btn.dataset.key;
    if (key === viewName || (key === 'tools' && viewName === 'tool_hub')) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update Sidebar Category Buttons
  document.querySelectorAll('.sidebar-cat-btn').forEach(btn => {
    if (activeCatId && btn.dataset.cat === activeCatId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Render View
  const container = document.getElementById('main-content');
  if (!container) return;

  if (viewName !== 'tool_hub' && activeHubVirtualGrid) {
    activeHubVirtualGrid.destroy();
    activeHubVirtualGrid = null;
  }

  if (viewName === 'home') {
    renderHome(container);
    updateBreadcrumb(['Home']);
  } else if (viewName === 'tool_hub') {
    renderToolHub(container);
    updateBreadcrumb(['Home', 'Tool Hub']);
  } else if (viewName === 'my_tools') {
    renderMyTools(container);
    updateBreadcrumb(['Home', 'My Tools']);
  } else if (viewName === 'history') {
    renderHistory(container);
    updateBreadcrumb(['Home', 'History']);
  } else if (viewName === 'favorites') {
    renderFavorites(container);
    updateBreadcrumb(['Home', 'Favorites']);
  } else if (viewName === 'settings') {
    renderSettings(container);
    updateBreadcrumb(['Home', 'Settings']);
  } else if (viewName === 'support') {
    SupportPage.render(container);
    updateBreadcrumb(['Home', 'Support the developer']);
  } else if (viewName === 'tool_studio') {
    if (toolId) recordRecentTool(toolId);
    renderToolStudio(container, toolId);
  } else if (viewName === 'category_view') {
    renderCategoryView(container, toolId);
  }
}

function navigateToCategory(categoryId, pushHistory = true) {
  navigateTo('category_view', categoryId, pushHistory);
}

function navigateBack() {
  // Pop the active view from the history stack if it's currently on top
  while (state.navHistory.length > 1) {
    const top = state.navHistory[state.navHistory.length - 1];
    const topView = typeof top === 'string' ? top : (top ? top.view : null);
    const topTool = typeof top === 'object' && top ? top.toolId : null;
    if (topView === state.currentView && topTool === state.activeToolId) {
      state.navHistory.pop();
    } else {
      break;
    }
  }

  if (state.navHistory.length > 0) {
    const prev = state.navHistory[state.navHistory.length - 1];
    const prevView = typeof prev === 'string' ? prev : (prev ? prev.view : 'home');
    const prevToolId = typeof prev === 'object' && prev ? prev.toolId : null;
    if (prevView === 'category_view') {
      navigateToCategory(prevToolId, false);
    } else {
      navigateTo(prevView || 'home', prevToolId, false);
    }
  } else {
    state.navHistory = [{ view: 'home', toolId: null }];
    navigateTo('home', null, false);
  }
}

function updateBreadcrumb(crumbs) {
  const bc = document.getElementById('header-breadcrumb');
  if (!bc) return;

  let html = '';
  crumbs.forEach((crumb, idx) => {
    const isLast = idx === crumbs.length - 1;
    if (idx > 0) {
      html += `<span class="mx-2 text-xs text-[var(--text-muted)]">/</span>`;
    }

    if (isLast) {
      html += `<span class="text-xs font-semibold text-[var(--text-primary)]">${crumb}</span>`;
    } else {
      // Find navigation target for breadcrumb item
      let actionAttr = '';
      if (crumb === 'Home') actionAttr = 'data-action="nav" data-view="home"';
      else if (crumb === 'Tool Hub') actionAttr = 'data-action="nav" data-view="tool_hub"';
      else if (crumb === 'My Tools') actionAttr = 'data-action="nav" data-view="my_tools"';
      else if (crumb === 'History') actionAttr = 'data-action="nav" data-view="history"';
      else if (crumb === 'Favorites') actionAttr = 'data-action="nav" data-view="favorites"';
      else if (crumb === 'Settings') actionAttr = 'data-action="nav" data-view="settings"';
      else {
        const cat = state.categories.find(c => c.name.toLowerCase() === crumb.toLowerCase());
        if (cat) actionAttr = `data-action="nav-category" data-cat="${escapeAttr(cat.id)}"`;
      }
      html += `<button ${actionAttr} class="text-xs font-medium text-[var(--brand-primary)] hover:underline cursor-pointer">${escapeHtml(crumb)}</button>`;
    }
  });

  bc.innerHTML = html;
}

// ── View Renderers ───────────────────────────────────────────────────────────

/// 1. Home Dashboard View (File-First Intelligent Workspace)
function renderHome(container) {
  const readyTools = state.tools.filter(t => t.status === 'installed' || t.status === 'update_available' || t.update_available);
  const installedTools = readyTools.length > 0 ? readyTools : state.tools.filter(t => ['pdf_merge', 'pdf_split', 'pdf_studio'].includes(t.id));

  // Compute Recent Files & Real User Recent Tools (do not inject default fake tools)
  const recentFilesList = (state.recentFiles || []).slice(0, 5);
  const recentToolsList = (state.recentTools || [])
    .map(id => state.tools.find(t => t.id === id))
    .filter(Boolean)
    .slice(0, 4);

  // CRITICAL USER RULE: Only render right rail if genuine recent files or used tools exist!
  const hasRecentActivity = recentFilesList.length > 0 || recentToolsList.length > 0;

  // Real Tools Cards Grid (Using authentic tools from state.tools)
  const displayTools = state.tools;
  const toolsGridHtml = displayTools.map(t => {
    const isFav = (state.favorites || []).includes(t.id);
    const isInstalled = t.status === 'installed' || t.status === 'update_available' || t.update_available;
    // Concise 2-line description mapping for ultra-clean UI
    let desc = t.description;
    if (t.id === 'pdf_merge') {
      desc = 'Combine multiple PDF documents offline in chosen sequence.';
    } else if (t.id === 'pdf_split') {
      desc = 'Extract page ranges or separate individual PDF pages.';
    } else if (t.id === 'pdf_compress') {
      desc = 'Reduce PDF file size offline with customizable DPI quality presets.';
    } else if (t.id === 'pdf_converter') {
      desc = 'Convert PDF pages to images or compile photos into a PDF.';
    } else if (t.id === 'subtitle_animator') {
      desc = 'Animate viral short-form video subtitles with custom styling.';
    } else if (t.id === 'pdf_studio') {
      desc = 'Merge, split, and compress PDF documents offline with zero quality loss.';
    } else if (desc && desc.length > 70) {
      desc = desc.substring(0, 68).trim() + '...';
    }

    return `
      <div 
        ${isInstalled ? `data-action="open-tool" data-tool-id="${escapeAttr(t.id)}"` : `data-action="install-tool" data-tool-id="${escapeAttr(t.id)}"`} 
        class="home-tool-card group rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer transition-all duration-200 flex flex-col justify-between shadow-xs hover:shadow-md overflow-hidden"
      >
        <div class="p-4 pb-3">
          <div class="flex items-center justify-between mb-2.5">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform">
              ${getIcon(t.icon, 'w-4 h-4')}
            </div>
            <button 
              type="button" 
              data-action="toggle-fav" 
              data-tool-id="${escapeAttr(t.id)}" 
              title="${isFav ? 'Remove from Favorites' : 'Add to Favorites'}"
              class="w-7 h-7 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${isFav ? 'text-red-500 bg-red-500/10' : 'text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10'}"
            >
              ${getIcon(isFav ? 'heartFilled' : 'heart', 'w-4 h-4 transition-transform active:scale-125')}
            </button>
          </div>
          <h4 class="text-xs font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors line-clamp-1">${escapeHtml(t.name)}</h4>
          <p class="text-[11px] text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed" title="${escapeAttr(t.description)}">${escapeHtml(desc)}</p>
        </div>
        <div class="px-4 py-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px]">
          ${isInstalled ? `
            <span class="font-semibold text-[var(--brand-primary)] group-hover:translate-x-0.5 transition-transform flex items-center justify-between w-full">
              <span>Open Tool</span>
              ${getIcon('arrow-right', 'w-3 h-3')}
            </span>
          ` : `
            <span class="text-[11px] font-mono text-[var(--text-muted)]">${t.size_mb || 1} MB</span>
            <button type="button" data-action="install-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-2.5 py-1 text-[11px] font-medium rounded-md bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1 shadow-xs cursor-pointer">
              ${getIcon('download', 'w-3 h-3')}
              <span>Install</span>
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');

  // Right Rail: Recent Files & Recent Tools
  let rightRailHtml = '';
  if (hasRecentActivity) {
    const recentFilesMarkup = recentFilesList.length > 0 ? recentFilesList.map(f => {
      const fileName = f.name || (f.path ? f.path.split('\\').pop().split('/').pop() : 'Document');
      const timeStr = f.time || 'Recently';
      return `
        <div class="p-2.5 rounded-lg bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] flex items-center justify-between gap-2 transition-all">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-7 h-7 rounded-md bg-red-500/10 text-red-500 flex items-center justify-center text-[9px] font-bold shrink-0 border border-red-500/20 font-mono">
              ${escapeHtml((f.ext || 'PDF').toUpperCase())}
            </div>
            <div class="min-w-0 truncate">
              <div class="text-xs font-semibold text-[var(--text-primary)] truncate" title="${escapeAttr(fileName)}">${escapeHtml(fileName)}</div>
              <div class="text-[10px] text-[var(--text-muted)] font-mono">${escapeHtml(timeStr)}</div>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button data-action="open-file" data-file-path="${escapeAttr(f.path)}" class="p-1 rounded text-[var(--text-muted)] hover:text-[var(--brand-primary)] hover:bg-[var(--surface-inset)] cursor-pointer" title="Open file">
              ${getIcon('external-link', 'w-3.5 h-3.5')}
            </button>
            <button data-action="reveal-file" data-file-path="${escapeAttr(f.path)}" class="p-1 rounded text-[var(--text-muted)] hover:text-[var(--brand-primary)] hover:bg-[var(--surface-inset)] cursor-pointer" title="Show in folder">
              ${getIcon('folder', 'w-3.5 h-3.5')}
            </button>
          </div>
        </div>
      `;
    }).join('') : '';

    const recentToolsMarkup = recentToolsList.length > 0 ? recentToolsList.map(t => {
      return `
        <div data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="p-2.5 rounded-lg bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] flex items-center justify-between gap-2.5 cursor-pointer transition-all">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-7 h-7 rounded-md bg-[var(--surface-inset)] text-[var(--brand-primary)] flex items-center justify-center shrink-0">
              ${getIcon(t.icon, 'w-3.5 h-3.5')}
            </div>
            <div class="min-w-0 truncate">
              <span class="text-xs font-semibold text-[var(--text-primary)] truncate block">${escapeHtml(t.name)}</span>
              <span class="text-[10px] text-[var(--text-muted)]">${escapeHtml(t.category_name)}</span>
            </div>
          </div>
          ${getIcon('arrow-right', 'w-3.5 h-3.5 text-[var(--text-muted)]')}
        </div>
      `;
    }).join('') : '';

    const recentFilesHeader = `
      <div class="flex items-center justify-between mb-4">
        <span class="text-xs font-bold text-[var(--text-muted)] tracking-wider uppercase">Generated Files</span>
        <button data-action="clear-recent-files" class="text-xs text-[var(--text-muted)] hover:text-red-500 cursor-pointer">Clear</button>
      </div>
    `;

    const recentToolsHeader = `
      <div class="flex items-center justify-between mb-4">
        <span class="text-xs font-bold text-[var(--text-muted)] tracking-wider uppercase">Recent Tools</span>
        <button data-action="clear-recent-tools" class="text-xs text-[var(--text-muted)] hover:text-red-500 cursor-pointer">Clear</button>
      </div>
    `;

    if (recentFilesMarkup || recentToolsMarkup) {
      rightRailHtml = `
        <div class="home-rail-divider space-y-6" style="width: 296px; flex-shrink: 0; border-left: 1px solid var(--border-subtle); padding-left: 24px;">
          ${recentFilesMarkup ? `
            <div>
              ${recentFilesHeader}
              <div class="space-y-2">
                ${recentFilesMarkup}
              </div>
            </div>
          ` : ''}

          ${recentToolsMarkup ? `
            <div>
              ${recentToolsHeader}
              <div class="space-y-2">
                ${recentToolsMarkup}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }
  }

  container.innerHTML = `
    <div class="max-w-6xl mx-auto pb-10 animate-in fade-in duration-150 home-layout-container" style="display: flex; flex-direction: column; gap: 32px;">
      <!-- 1. Hero Dropzone Section (Full Top Banner with Clean Proportions) -->
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div>
          <h1 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">What do you want to build or process?</h1>
          <p class="text-xs text-[var(--text-secondary)] mt-1">Select or drop any file directly. Boltools automatically recognizes the format and suggests instant actions.</p>
        </div>

        <!-- Interactive Global Dropzone -->
        <div 
          id="home-global-dropzone" 
          data-action="home-browse-files"
          class="p-8 rounded-xl bg-[var(--surface-card)] border-2 border-dashed border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer text-center transition-all group relative overflow-hidden shadow-xs hover:shadow-sm"
        >
          <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform mb-3 border border-[var(--border-subtle)]">
            ${getIcon('upload-cloud', 'w-6 h-6')}
          </div>
          <h3 class="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
            Drop any file here to get started
          </h3>
          <p class="text-xs text-[var(--text-secondary)] mt-1">or click to <span class="text-[var(--brand-primary)] font-medium">browse local files</span></p>
        </div>
      </div>

      <!-- 2. Main Content Stage: Utilities on Left + Generous Gap + Recent Activity Rail on Right -->
      <div class="home-stage-row" style="display: flex; align-items: flex-start; gap: 28px; width: 100%;">
        <!-- Left Column: Utilities & Tools Grid -->
        <div class="flex-1" style="min-width: 0;">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-bold text-[var(--text-muted)] tracking-wider uppercase">Utilities & Tools</span>
            <button data-action="nav" data-view="tool_hub" class="text-xs font-semibold text-[var(--brand-primary)] hover:underline flex items-center gap-1 cursor-pointer">
              <span>View Tool Hub</span>
              ${getIcon('chevron-right', 'w-3 h-3')}
            </button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            ${toolsGridHtml}
          </div>
        </div>

        <!-- Right Column: Recent Tools & Generated Files (Isolated Rail with Independent Width & Padding) -->
        ${rightRailHtml}
      </div>
    </div>
  `;

  attachHomeDropzoneEvents();
}

function attachHomeDropzoneEvents() {
  const dz = document.getElementById('home-global-dropzone');
  if (!dz || dz._bound) return;
  dz._bound = true;

  dz.addEventListener('dragover', (e) => {
    e.preventDefault();
    dz.classList.add('border-[var(--brand-primary)]', 'bg-[var(--brand-light)]');
  });

  dz.addEventListener('dragleave', (e) => {
    dz.classList.remove('border-[var(--brand-primary)]', 'bg-[var(--brand-light)]');
  });

  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('border-[var(--brand-primary)]', 'bg-[var(--brand-light)]');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const paths = Array.from(e.dataTransfer.files).map(f => f.path || f.name).filter(Boolean);
      if (paths.length > 0) {
        handleGlobalFileInput(paths);
      }
    }
  });
}

async function handleHomeBrowseFiles() {
  const files = await callBridge('browse_files', ['All Supported Files (*.pdf;*.png;*.jpg;*.mp4;*.mkv;*.mp3;*.wav)', 'All Files (*.*)']);
  if (files && files.length > 0) {
    handleGlobalFileInput(files);
  }
}

// Global File Input Smart Router
let pendingGlobalFiles = [];

function handleGlobalFileInput(files) {
  if (!files || files.length === 0) return;
  pendingGlobalFiles = files;

  const firstFile = files[0];
  const ext = firstFile.split('.').pop().toLowerCase();
  const fileName = firstFile.split('\\').pop().split('/').pop();

  if (ext === 'pdf') {
    const modal = document.getElementById('modal-file-action');
    const title = document.getElementById('file-action-title');
    const sub = document.getElementById('file-action-subtitle');
    const icon = document.getElementById('file-action-icon');
    const opts = document.getElementById('file-action-options');

    if (modal && opts) {
      if (title) title.innerText = files.length > 1 ? `${files.length} PDF Documents Detected` : `PDF Document Detected`;
      if (sub) sub.innerText = files.length > 1 ? `${fileName} + ${files.length - 1} more` : fileName;
      if (icon) {
        icon.className = 'w-8 h-8 rounded-md bg-red-500/10 text-red-500 flex items-center justify-center font-bold text-[10px] border border-red-500/20 shrink-0';
        icon.innerText = 'PDF';
      }

      opts.innerHTML = `
        <button data-action="smart-action-merge" class="w-full p-3 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] text-left flex items-center justify-between group transition-all cursor-pointer">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-md bg-[var(--brand-primary)] text-white flex items-center justify-center shrink-0">
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/><rect x="8" y="6" width="12" height="14" rx="1.5"/><path d="M12 13h4"/><path d="M14 11v4"/></svg>
            </div>
            <div>
              <div class="text-xs font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)]">Merge PDFs into One File</div>
              <div class="text-[11px] text-[var(--text-secondary)]">Combine ${files.length} document${files.length > 1 ? 's' : ''} in your chosen order</div>
            </div>
          </div>
          ${getIcon('arrow-right', 'w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand-primary)]')}
        </button>

        <button data-action="smart-action-split" class="w-full p-3 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] text-left flex items-center justify-between group transition-all cursor-pointer">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-md bg-[var(--surface-card)] border border-[var(--border-subtle)] text-[var(--brand-primary)] flex items-center justify-center shrink-0">
              <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>
            </div>
            <div>
              <div class="text-xs font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)]">Split or Extract Pages</div>
              <div class="text-[11px] text-[var(--text-secondary)]">Extract page ranges or separate individual sheets</div>
            </div>
          </div>
          ${getIcon('arrow-right', 'w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand-primary)]')}
        </button>
      `;

      modal.classList.remove('hidden');
      return;
    }
  }

  // Fallback direct open for PDF studio
  openPdfStudioWithFiles(files, 'merge');
}

function openPdfStudioWithFiles(files, mode = 'merge') {
  const modal = document.getElementById('modal-file-action');
  if (modal) modal.classList.add('hidden');

  const targetToolId = mode === 'split' ? 'pdf_split' : 'pdf_merge';
  navigateTo('tool_studio', targetToolId);
  state.selectedFiles = files.slice();
  state.activeToolOptions.mode = mode;
  updateStudioFilesUI();
  inspectSelectedPdfFiles(state.selectedFiles);
}

// 1b. My Tools View (Sidebar Navigation)
function renderMyTools(container) {
  const installedTools = state.tools.filter(t => t.status === 'installed' || t.status === 'update_available' || t.update_available);
  const toolsToDisplay = installedTools.length > 0 ? installedTools : state.tools.filter(t => ['pdf_merge', 'pdf_split', 'pdf_studio'].includes(t.id));

  const toolsHtml = toolsToDisplay.map(t => `
    <div data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="p-4 rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] flex items-center justify-between gap-3 cursor-pointer transition-all">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-10 h-10 rounded-lg bg-[var(--surface-inset)] text-[var(--brand-primary)] flex items-center justify-center shrink-0 border border-[var(--border-subtle)]">
          ${getIcon(t.icon, 'w-5 h-5')}
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <h4 class="text-xs font-bold text-[var(--text-primary)] truncate">${escapeHtml(t.name)}</h4>
            <span class="px-1.5 py-0.5 text-[9px] font-semibold rounded bg-emerald-500/10 text-emerald-600">v${escapeHtml(t.version || '0.1.0')}</span>
          </div>
          <p class="text-[11px] text-[var(--text-secondary)] truncate mt-0.5">${escapeHtml(t.description)}</p>
        </div>
      </div>
      <button class="shrink-0 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white flex items-center gap-1 cursor-pointer">
        <span>Launch</span>
        ${getIcon('arrow-right', 'w-3 h-3')}
      </button>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">My Tools</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Installed offline utilities currently active on your local drive.</p>
      </div>
      <div class="grid grid-cols-1 gap-3">
        ${toolsHtml}
      </div>
    </div>
  `;
}

// 1c. History View (Sidebar Navigation)
function renderHistory(container) {
  const recentFiles = state.recentFiles || [];
  const filesHtml = recentFiles.length > 0 ? recentFiles.map(f => {
    const fileName = f.name || (f.path ? f.path.split('\\').pop().split('/').pop() : 'Document');
    return `
      <div class="p-3 rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] flex items-center justify-between gap-3 transition-all">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-red-500/10 text-red-500 flex items-center justify-center font-bold text-[10px] shrink-0 font-mono border border-red-500/20">
            ${escapeHtml((f.ext || 'PDF').toUpperCase())}
          </div>
          <div class="min-w-0">
            <h4 class="text-xs font-semibold text-[var(--text-primary)] truncate">${escapeHtml(fileName)}</h4>
            <p class="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">${escapeHtml(f.time || 'Recently')} • ${escapeHtml(f.toolName || 'Boltools')}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button data-action="open-file" data-file-path="${escapeAttr(f.path)}" class="px-2.5 py-1 text-xs font-medium rounded-md bg-[var(--surface-inset)] hover:bg-[var(--brand-primary)] hover:text-white border border-[var(--border-subtle)] text-[var(--text-primary)] transition-all cursor-pointer">
            Open File
          </button>
          <button data-action="reveal-file" data-file-path="${escapeAttr(f.path)}" class="px-2.5 py-1 text-xs font-medium rounded-md bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-secondary)] transition-all cursor-pointer">
            Folder
          </button>
        </div>
      </div>
    `;
  }).join('') : `
    <div class="p-10 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center space-y-2">
      <div class="w-10 h-10 mx-auto rounded-lg bg-[var(--surface-inset)] text-[var(--text-muted)] flex items-center justify-center">
        ${getIcon('history', 'w-5 h-5')}
      </div>
      <h3 class="text-xs font-semibold text-[var(--text-primary)]">No Processed Files Yet</h3>
      <p class="text-[11px] text-[var(--text-secondary)] max-w-xs mx-auto">Files and documents generated by tools will show up here for fast access and review.</p>
    </div>
  `;

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Processing History</h2>
          <p class="text-xs text-[var(--text-secondary)] mt-1">Audit trail of documents and assets processed on this PC.</p>
        </div>
        ${recentFiles.length > 0 ? `
          <button data-action="clear-recent-files" class="px-3 py-1.5 text-xs font-medium rounded-lg text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer">
            Clear History
          </button>
        ` : ''}
      </div>
      <div class="space-y-2">
        ${filesHtml}
      </div>
    </div>
  `;
}

// 1b. Dedicated Category View
function renderCategoryView(container, categoryId) {
  const cat = state.categories.find(c => c.id === categoryId) || {
    id: categoryId,
    name: "Utilities",
    desc: "Offline tools for power operations",
    icon: "sliders",
    accent: "var(--brand-primary)"
  };

  updateBreadcrumb(['Home', cat.name]);

  const catTools = state.tools.filter(t => t.category_id === categoryId);

  // Responsive balanced grid layout: avoids lonely orphan cards
  const gridClass = catTools.length === 4
    ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4"
    : (catTools.length === 2
        ? "grid grid-cols-1 sm:grid-cols-2 gap-4"
        : (catTools.length === 3
            ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            : "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"));

  const toolCardsHtml = catTools.length > 0 ? catTools.map(t => {
    const isInstalled = t.status === 'installed' || t.status === 'update_available' || t.update_available;
    return `
      <div 
        ${isInstalled ? `data-action="open-tool" data-tool-id="${escapeAttr(t.id)}"` : `data-action="install-tool" data-tool-id="${escapeAttr(t.id)}"`} 
        class="group rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer transition-all duration-200 flex flex-col justify-between shadow-xs hover:shadow-md relative overflow-hidden"
      >
        <div class="p-4 pb-3">
          <div class="flex items-center justify-between gap-2 mb-2.5">
            <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] group-hover:scale-105 transition-transform" style="color: ${cat.accent};">
              ${getIcon(t.icon, 'w-4.5 h-4.5')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full ${isInstalled ? 'bg-emerald-500/10 text-emerald-500' : 'bg-[var(--surface-pill)] text-[var(--text-muted)]'}">
              ${isInstalled ? 'Ready' : 'Available'}
            </span>
          </div>
          <h4 class="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors line-clamp-1">${escapeHtml(t.name)}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1.5 line-clamp-2 leading-relaxed" title="${escapeAttr(t.description)}">${escapeHtml(t.description)}</p>
        </div>
        <div class="px-4 py-3 border-t border-[var(--border-subtle)] flex items-center justify-between gap-2">
          ${isInstalled ? `
            <span class="text-xs font-semibold text-[var(--brand-primary)] group-hover:translate-x-0.5 transition-transform flex items-center gap-1.5">
              <span>Open Tool</span>
              ${getIcon('arrow-right', 'w-3.5 h-3.5')}
            </span>
            <button data-action="uninstall-tool" data-tool-id="${escapeAttr(t.id)}" data-tool-name="${escapeAttr(t.name)}" class="px-2 py-1 text-[11px] font-normal rounded-md text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer">
              Uninstall
            </button>
          ` : `
            <span class="text-[11px] font-mono text-[var(--text-muted)]">
              ${t.size_mb || 1} MB • Offline
            </span>
            <button data-action="install-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-xs cursor-pointer">
              ${getIcon('download', 'w-3 h-3')}
              <span>Install</span>
            </button>
          `}
        </div>
      </div>
    `;
  }).join('') : `
    <div class="col-span-full p-8 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center">
      <p class="text-xs text-[var(--text-secondary)]">No tools currently in this category.</p>
    </div>
  `;

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <!-- Category Header Card -->
      <div class="p-5 rounded-2xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-[var(--surface-inset)]" style="color: ${cat.accent};">
            ${getIcon(cat.icon, 'w-6 h-6')}
          </div>
          <div>
            <h2 class="text-lg font-bold font-display text-[var(--text-primary)]">${cat.name}</h2>
            <p class="text-xs text-[var(--text-secondary)] mt-0.5">${cat.desc}</p>
          </div>
        </div>
        <span class="px-2.5 py-1 text-xs font-medium rounded-full bg-[var(--surface-pill)] text-[var(--text-secondary)]">
          ${catTools.length} Utilities
        </span>
      </div>

      <!-- Tools Grid -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Utilities in this category</span>
          <button data-action="nav" data-view="tool_hub" class="text-xs text-[var(--brand-primary)] hover:underline flex items-center gap-1 cursor-pointer">
            <span>View All Tools</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
        <div class="${gridClass}">
          ${toolCardsHtml}
        </div>
      </div>
    </div>
  `;
}

// ── Tool Hub Search & Virtual Grid Controller ───────────────────────────────
let activeHubVirtualGrid = null;
let activeSearchIndex = null;
let hubSearchDebounceTimer = null;

function renderToolHubCard(t, index) {
  const isUpdate = t.update_available || t.status === 'update_available';
  const isInstalled = t.status === 'installed' || isUpdate;
  const installedVer = t.installed_version || (t.status === 'installed' ? (t.version || '1.0.0') : null);
  const remoteVer = t.remote_version || t.version || '1.0.0';

  return `
    <div id="hub-card-${t.id}" class="hairline-card rounded-xl bg-[var(--surface-card)] border ${isUpdate ? 'border-amber-500/40 shadow-sm' : 'border-[var(--border-subtle)]'} hover:border-[var(--border-hover)] flex flex-col justify-between relative overflow-hidden">
      ${isUpdate ? `
        <div class="absolute top-0 right-0 bg-amber-500 text-white text-[9px] font-bold px-2.5 py-0.5 rounded-bl-lg tracking-wider uppercase flex items-center gap-1 z-10">
          ${getIcon('refresh-cw', 'w-2.5 h-2.5')} Update Available
        </div>
      ` : ''}
      <div class="p-4 pb-3">
        <div class="flex items-center gap-2.5 mb-2.5">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
            ${getIcon(t.icon, 'w-4 h-4')}
          </div>
          <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${escapeHtml(t.category_name)}</span>
          <span class="text-[10px] font-mono text-[var(--text-muted)]">v${installedVer || remoteVer}</span>
        </div>
        <h4 class="text-sm font-semibold text-[var(--text-primary)] truncate">${window.ToolSearchIndex ? window.ToolSearchIndex.highlight(t.name, state.searchQuery) : escapeHtml(t.name)}</h4>
        <p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">${window.ToolSearchIndex ? window.ToolSearchIndex.highlight(t.description, state.searchQuery) : escapeHtml(t.description)}</p>
      </div>
      <div class="px-4 py-3 border-t border-[var(--border-subtle)] flex items-center justify-between gap-2">
        ${isUpdate ? `
          <div class="flex items-center gap-2 w-full justify-between">
            <button id="btn-action-${escapeAttr(t.id)}" data-action="update-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-all flex items-center gap-1.5 cursor-pointer shadow-xs">
              ${getIcon('download', 'w-3 h-3')}
              <span>Update v${remoteVer}</span>
            </button>
            <button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-inset)] transition-colors cursor-pointer">
              <span>Launch</span>
            </button>
          </div>
        ` : (isInstalled ? `
          <button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 cursor-pointer shadow-xs">
            <span>Open Tool</span>
            ${getIcon('arrow-right', 'w-3 h-3')}
          </button>
          <button data-action="uninstall-tool" data-tool-id="${escapeAttr(t.id)}" data-tool-name="${escapeAttr(t.name)}" class="px-2 py-1 text-xs font-normal rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer">
            Uninstall
          </button>
        ` : `
          <button id="btn-action-${escapeAttr(t.id)}" data-action="install-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 cursor-pointer shadow-xs">
            ${getIcon('download', 'w-3 h-3')}
            <span>+ Install</span>
          </button>
        `)}
      </div>
    </div>
  `;
}

function renderToolHub(container) {
  const filterTab = state.hubFilterTab || 'All';
  const query = state.searchQuery || '';
  const updatesCount = state.updatesCount || state.tools.filter(t => t.update_available || t.status === 'update_available').length;

  if (!activeSearchIndex || activeSearchIndex.rawTools !== state.tools) {
    activeSearchIndex = new ToolSearchIndex(state.tools);
  }

  const matchingTools = activeSearchIndex.search(query, filterTab);

  const hubTabs = [
    { id: 'All', label: 'All' },
    { id: 'Installed', label: 'Installed' },
    { id: 'Updates', label: updatesCount > 0 ? `Updates (${updatesCount})` : 'Updates', badge: updatesCount > 0 },
    { id: 'Hub Catalog', label: 'Hub Catalog' }
  ];

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-5 pb-6 h-full flex flex-col">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Tool Hub</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Browse, install, and update modular offline tools directly on this PC.</p>
      </div>

      <!-- Filter Tabs & Search Bar -->
      <div class="p-2 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex flex-col sm:flex-row items-center gap-3 shrink-0">
        <!-- Segmented Tabs -->
        <div class="flex items-center gap-1 p-1 bg-[var(--surface-inset)] rounded-lg shrink-0 overflow-x-auto max-w-full">
          ${hubTabs.map(tab => `
            <button data-action="set-hub-tab" data-tab="${escapeAttr(tab.id)}" class="px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 cursor-pointer ${filterTab === tab.id ? 'bg-[var(--surface-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}">
              <span>${tab.label}</span>
              ${tab.badge && filterTab !== tab.id ? `<span class="w-2 h-2 rounded-full bg-amber-500 inline-block"></span>` : ''}
            </button>
          `).join('')}
        </div>

        <!-- Search Input -->
        <div class="relative w-full">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--text-muted)]">
            ${getIcon('search', 'w-3.5 h-3.5')}
          </div>
          <input 
            type="text" 
            id="hub-search-input"
            value="${state.searchQuery}"
            placeholder="Filter utilities by name or keyword..."
            data-action="hub-search-input"
            class="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--brand-primary)]"
          />
        </div>
      </div>

      <!-- Virtualized Scroll Viewport Container -->
      <div id="virtual-grid-viewport" class="flex-1 overflow-y-auto relative min-h-[400px]">
      </div>
    </div>
  `;

  const viewport = document.getElementById('virtual-grid-viewport');
  if (viewport) {
    if (activeHubVirtualGrid) activeHubVirtualGrid.destroy();
    activeHubVirtualGrid = new VirtualGrid({
      container: viewport,
      items: matchingTools,
      cardHeight: 190,
      gap: 14,
      bufferRows: 3,
      renderCard: renderToolHubCard
    });
    activeHubVirtualGrid.mount();
  }
}

function setHubTab(tabName) {
  state.hubFilterTab = tabName;
  const container = document.getElementById('main-content');
  if (container) renderToolHub(container);
}

function handleHubSearch(val) {
  state.searchQuery = val;
  if (hubSearchDebounceTimer) clearTimeout(hubSearchDebounceTimer);
  hubSearchDebounceTimer = setTimeout(() => {
    if (activeHubVirtualGrid && activeSearchIndex) {
      const results = activeSearchIndex.search(val, state.hubFilterTab || 'All');
      activeHubVirtualGrid.setItems(results);
    }
  }, 80);
}

async function handleInstallOrUpdateTool(toolId, isUpdate = false) {
  const btn = document.getElementById(`btn-action-${toolId}`);
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.style.opacity = '0.7';
    btn.innerHTML = `<span class="inline-block animate-spin mr-1.5">⏳</span><span>${isUpdate ? 'Updating Engine...' : 'Installing Engine...'}</span>`;
  }

  try {
    const res = await callBridge('install_or_update_tool', toolId);
    if (res && res.success) {
      const [initData, summaryData] = await Promise.all([
        callBridge('get_initial_data'),
        callBridge('get_catalog_summary')
      ]);
      if (initData) {
        if (initData.categories) state.categories = initData.categories;
        state.updatesCount = initData.updates_count || 0;
        updateBellBadge();
      }
      if (Array.isArray(summaryData)) {
        state.tools = summaryData;
      }
      showToast(res.message || `${toolId} installed successfully!`, 'success');
      const container = document.getElementById('main-content');
      if (container) {
        if (state.currentView === 'tool_hub') renderToolHub(container);
        else if (state.currentView === 'home') renderHome(container);
        else if (state.currentView === 'category_view') renderCategoryView(container, state.activeCategoryId);
      }
    } else {
      const errorMsg = (res && res.error) || 'Failed to download tool package.';
      showToast(errorMsg, 'error');
      if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.innerHTML = `<span>Retry</span>`;
      }
    }
  } catch (err) {
    console.error('Error in handleInstallOrUpdateTool:', err);
    showToast(`Installation error: ${err.message || err}`, 'error');
    if (btn) {
      btn.disabled = false;
      btn.style.opacity = '1';
      btn.innerHTML = `<span>Retry</span>`;
    }
  }
}

async function handleInstallTool(toolId) {
  return handleInstallOrUpdateTool(toolId, false);
}

const installTool = handleInstallTool;

// 3. Favorites View
function renderFavorites(container) {
  const favTools = state.tools.filter(t => state.favorites.includes(t.id));

  if (favTools.length === 0) {
    container.innerHTML = `
      <div class="max-w-2xl mx-auto py-16 text-center">
        <div class="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center bg-[var(--surface-card)] border border-[var(--border-subtle)] text-[var(--text-muted)] mb-4">
          ${getIcon('heart', 'w-6 h-6')}
        </div>
        <h3 class="text-base font-semibold text-[var(--text-primary)]">No Pinned Favorites Yet</h3>
        <p class="text-xs text-[var(--text-secondary)] max-w-sm mx-auto mt-1 mb-5">Pin frequently used utilities using the heart icon inside any tool studio for instant access.</p>
        <button data-action="nav" data-view="tool_hub" class="btn-primary px-4 py-2 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all inline-flex items-center gap-1.5 cursor-pointer">
          <span>Browse Tool Hub</span>
          ${getIcon('arrow-right', 'w-3.5 h-3.5')}
        </button>
      </div>
    `;
    return;
  }

  const cards = favTools.map(t => `
    <div class="p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] hover:border-[var(--border-hover)] transition-all flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between gap-2 mb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
              ${getIcon(t.icon, 'w-4 h-4')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${escapeHtml(t.category_name)}</span>
          </div>
          <button data-action="toggle-fav" data-tool-id="${escapeAttr(t.id)}" class="text-red-500 hover:scale-110 transition-transform">
            ${getIcon('heartFilled', 'w-4 h-4')}
          </button>
        </div>
        <h4 class="text-sm font-semibold text-[var(--text-primary)]">${escapeHtml(t.name)}</h4>
        <p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">${escapeHtml(t.description)}</p>
      </div>
      <div class="mt-4 pt-3 border-t border-[var(--border-subtle)]">
        <button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">
          <span>Launch Utility</span>
          ${getIcon('arrow-right', 'w-3 h-3')}
        </button>
      </div>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Favorites</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Quick access to your pinned utilities for fast daily workflows.</p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        ${cards}
      </div>
    </div>
  `;
}

async function handleToggleFavorite(toolId, clickedBtn = null) {
  const updated = await callBridge('toggle_favorite', toolId);
  if (updated) state.favorites = updated;
  const isFav = (state.favorites || []).includes(toolId);

  // If clicked button element was passed or found in DOM, apply pop animation immediately
  const btn = clickedBtn || document.querySelector(`button[data-action="toggle-fav"][data-tool-id="${toolId}"]`);
  if (btn) {
    btn.innerHTML = getIcon(isFav ? 'heartFilled' : 'heart', 'w-4 h-4 transition-transform');
    btn.className = `w-7 h-7 rounded-lg flex items-center justify-center transition-colors cursor-pointer heart-btn-animate ${isFav ? 'text-red-500 bg-red-500/10' : 'text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10'}`;
    btn.title = isFav ? 'Remove from Favorites' : 'Add to Favorites';
    setTimeout(() => {
      btn.classList.remove('heart-btn-animate');
    }, 400);
  }

  const container = document.getElementById('main-content');
  if (state.currentView === 'favorites' && container) {
    renderFavorites(container);
  }
}

// 4. Settings View
function renderSettings(container) {
  container.innerHTML = `
    <div class="max-w-3xl mx-auto space-y-7 pb-10">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Settings</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Preferences, appearance, and local storage management.</p>
      </div>

      <!-- Appearance -->
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Appearance</span>
        <div class="flex items-center justify-between pt-1">
          <div>
            <h4 class="text-sm font-semibold text-[var(--text-primary)]">Theme Mode</h4>
            <p class="text-xs text-[var(--text-secondary)] mt-0.5">Switch between dark and soothing eye-friendly light mode.</p>
          </div>
          <div class="flex items-center gap-1 p-1 bg-[var(--surface-inset)] rounded-lg">
            ${['dark', 'light'].map(m => `
              <button data-action="set-theme" data-theme="${escapeAttr(m)}" class="px-3 py-1 text-xs font-medium rounded-md capitalize transition-all ${state.theme === m ? 'bg-[var(--surface-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}">
                ${m}
              </button>
            `).join('')}
          </div>
        </div>
      </div>

      <!-- Storage & Directory -->
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Storage & Output</span>
        <div>
          <h4 class="text-sm font-semibold text-[var(--text-primary)]">Default Output Folder</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-0.5">Where converted and compressed files will be saved by default.</p>
          <div class="flex items-center gap-2 mt-3">
            <input type="text" id="settings-out-dir" value="${state.defaultDownloads}" readonly class="w-full px-3 py-2 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)]" />
            <button data-action="browse-default-folder" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors cursor-pointer">
              Browse...
            </button>
          </div>
        </div>
      </div>

      <!-- Maintenance -->
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Maintenance</span>
        <div class="flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-[var(--text-primary)]">Clean Local Cache</h4>
            <p class="text-xs text-[var(--text-secondary)] mt-0.5">Wipes temporary processing files without touching your presets.</p>
          </div>
          <button data-action="clean-cache" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors cursor-pointer">
            Clean Cache
          </button>
        </div>
      </div>

      <!-- About & Diagnostics -->
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-4">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">About & Diagnostics</span>
        <div>
          <h4 class="text-sm font-semibold text-[var(--text-primary)]">Boltools Desktop v1.1</h4>
          <p class="text-xs text-[var(--text-secondary)] leading-relaxed mt-0.5">Fast, private, 100% offline utilities for creators and power users. Designed and built with obsessed human craftsmanship.</p>
        </div>
        <div>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium bg-[var(--surface-inset)] text-[var(--text-muted)]">
            ${getIcon('shield', 'w-3 h-3 text-emerald-500')}
            <span>100% Local PC Engine • Zero Cloud Telemetry</span>
          </span>
        </div>

        <div class="pt-2 border-t border-[var(--border-subtle)] space-y-2">
          <span class="text-[10px] font-semibold text-[var(--text-muted)] tracking-wider uppercase">Shell Diagnostics</span>
          <div class="p-2.5 rounded-lg bg-[var(--surface-inset)] font-mono text-[11px] text-[var(--text-secondary)] space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-[var(--text-muted)]">window.location.search:</span>
              <span class="text-[var(--text-primary)] font-semibold">${escapeHtml(window.location.search || '(none)')}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[var(--text-muted)]">Native Shell Active:</span>
              <span class="${((new URLSearchParams(window.location.search).get('shell') === 'native') || Boolean(window.__BOLTOOLS_NATIVE_SHELL__)) ? 'text-emerald-500' : 'text-amber-500'} font-semibold">
                ${((new URLSearchParams(window.location.search).get('shell') === 'native') || Boolean(window.__BOLTOOLS_NATIVE_SHELL__)) ? 'YES (Native WebView2)' : 'NO (Standalone / Mock)'}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[var(--text-muted)]">Injected Global:</span>
              <span class="text-[var(--text-primary)]">${Boolean(window.__BOLTOOLS_NATIVE_SHELL__) ? 'true' : 'false'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function handleBrowseDefaultFolder() {
  const dir = await callBridge('browse_directory');
  if (dir) {
    state.defaultDownloads = dir;
    const inp = document.getElementById('settings-out-dir');
    if (inp) inp.value = dir;
  }
}

async function handleCleanCache(btn) {
  const res = await callBridge('clean_cache');
  if (res && res.success) {
    btn.innerText = `Cleaned ${res.cleaned_files} items ✓`;
    btn.classList.add('text-emerald-500');
    setTimeout(() => {
      btn.innerText = 'Clean Cache';
      btn.classList.remove('text-emerald-500');
    }, 2000);
  }
}

// 5. Universal 2-Pane Tool Studio View
function renderToolStudio(container, toolId) {
  const tool = state.tools.find(t => t.id === toolId) || state.tools[0];
  state.activeToolId = tool.id;
  state.selectedFiles = [];
  state.isToolRunning = false;
  state.activeToolOptions = getDefaultOptionsForTool(tool.id);

  updateBreadcrumb(['Home', tool.category_name, tool.name]);

  const isFav = state.favorites.includes(tool.id);

  container.innerHTML = `
    <div class="w-full space-y-4 pb-4 flex flex-col">
      <!-- Studio Header Bar -->
      <div class="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)] shrink-0">
        <div class="flex items-center gap-3">
          <button data-action="navigate-back" class="w-8 h-8 rounded-md flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors cursor-pointer">
            ${getIcon('arrow-left', 'w-4 h-4')}
          </button>
          <div class="w-8 h-8 rounded-md flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
            ${getIcon(tool.icon, 'w-4 h-4')}
          </div>
          <div>
            <h3 class="text-sm font-bold font-display text-[var(--text-primary)]">${escapeHtml(tool.name)}</h3>
            <p class="text-[11px] text-[var(--text-secondary)] line-clamp-1">${escapeHtml(tool.description)}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button data-action="studio-toggle-fav" data-tool-id="${escapeAttr(tool.id)}" class="w-8 h-8 rounded-md flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-secondary)] transition-colors cursor-pointer">
            ${isFav ? getIcon('heartFilled', 'w-4 h-4') : getIcon('heart', 'w-4 h-4')}
          </button>
        </div>
      </div>

      <!-- Studio 2-Pane Grid: Left Stage (Files & Dropzone) + Right Panel (Configuration & Actions) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-start min-h-0">
        <!-- Left Pane: File Workspace & Dropzone (7 Cols) -->
        <div id="studio-stage-left" class="lg:col-span-7 space-y-3">
          <!-- Clean Hero Dropzone -->
          <div 
            id="studio-dropzone" 
            data-action="studio-browse-files" data-tool-id="${escapeAttr(tool.id)}"
            class="p-6 rounded-md bg-[var(--surface-card)] border border-dashed border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer text-center transition-all group relative overflow-hidden"
          >
            <div class="w-10 h-10 mx-auto rounded-md flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform mb-2 border border-[var(--border-subtle)]">
              ${getIcon('upload-cloud', 'w-5 h-5')}
            </div>
            <h4 class="text-xs font-semibold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">
              Drop ${['pdf_studio', 'pdf_merge', 'pdf_split'].includes(tool.id) ? 'PDF' : ''} files here
            </h4>
            <p class="text-[11px] text-[var(--text-secondary)] mt-0.5">or click to <span class="text-[var(--brand-primary)] font-medium">browse</span></p>
            <span class="ft-limits">${escapeHtml(ToolUX.get(tool.id).limits)}</span>
            <span class="ft-before">${escapeHtml(ToolUX.get(tool.id).before)} · Ctrl+O</span>
          </div>

          <!-- Selected Files List Card -->
          <div id="studio-files-wrap" class="hidden space-y-2 p-3 rounded-md bg-[var(--surface-card)] border border-[var(--border-subtle)]">
            <div class="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)] text-xs">
              <span id="studio-files-count" class="font-semibold text-[var(--text-primary)]">0 files added</span>
              <div class="flex items-center gap-3">
                <button type="button" data-action="clear-studio-files" class="font-medium text-red-500 hover:underline flex items-center gap-1 cursor-pointer">
                  ${getIcon('trash', 'w-3 h-3')}
                  <span>Clear all</span>
                </button>
              </div>
            </div>
            <div id="studio-files-list" class="space-y-1.5 max-h-72 overflow-y-auto pr-1"></div>
            <div id="studio-preview" class="fp-preview"></div>
          </div>
        </div>

        <!-- Right Pane: Mode Options, Settings & Execution CTA (5 Cols) -->
        <div id="studio-right" class="lg:col-span-5 space-y-3 flex flex-col">
          <!-- Unified Studio Inspector Card -->
          <div id="studio-inspector" class="p-3.5 rounded-md bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3.5">
            <!-- Tool Specific Mode Options -->
            <div id="studio-options-box" class="space-y-3">
              ${renderToolSpecificOptions(tool.id)}
            </div>

            <!-- Output Settings: Filename & Destination -->
            <div class="pt-3 border-t border-[var(--border-subtle)] space-y-2.5">
              <div ${ToolUX.get(tool.id).namesOutput === false ? 'hidden' : ''}>
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Output File Name</span>
                  <span class="text-[10px] text-[var(--text-muted)] font-mono">${['pdf_studio', 'pdf_merge', 'pdf_split', 'pdf_compress'].includes(tool.id) ? '.pdf' : ''}</span>
                </div>
                <input 
                  type="text" 
                  id="studio-out-filename" 
                  value="${escapeAttr(state.activeToolOptions.custom_filename || (tool.id === 'pdf_merge' ? 'merged_document.pdf' : (tool.id === 'pdf_split' ? 'split_document' : (tool.id === 'pdf_compress' ? 'compressed_document.pdf' : (tool.id === 'pdf_studio' ? ((state.activeToolOptions.mode || 'merge') === 'merge' ? 'merged_document.pdf' : 'split_document') : 'output_result')))))}" 
                  data-action="studio-out-filename-input" 
                  placeholder="${tool.id === 'pdf_split' ? 'split_document' : (tool.id === 'pdf_compress' ? 'compressed_document.pdf' : 'merged_document.pdf')}" 
                  class="w-full px-2.5 py-1.5 text-xs rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] font-mono" 
                />
              </div>

              <div>
                <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block mb-1">Save Location</span>
                <div class="flex items-center gap-1.5">
                  <input type="text" id="studio-out-folder" value="${state.customOutputDir || state.defaultDownloads}" data-action="studio-out-folder-input" class="w-full px-2.5 py-1.5 text-xs rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] cursor-text" />
                  <button data-action="studio-browse-out-folder" class="px-3 py-1.5 text-xs font-medium rounded-md bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors cursor-pointer">
                    Browse
                  </button>
                </div>
              </div>
            </div>

            <!-- Primary Execution CTA Button -->
            <button 
              id="studio-btn-execute"
              data-action="studio-execute" data-tool-id="${escapeAttr(tool.id)}"
              class="btn-primary w-full py-2.5 text-xs font-semibold rounded-md bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span id="studio-btn-exec-label">${tool.id === 'pdf_merge' ? 'Merge Documents' : (tool.id === 'pdf_split' ? 'Split Document' : (tool.id === 'pdf_compress' ? 'Compress PDF' : (tool.id === 'pdf_studio' ? ((state.activeToolOptions.mode || 'merge') === 'merge' ? 'Merge Documents' : 'Split Document') : 'Start Processing')))}</span>
              ${getIcon('arrow-right', 'w-3.5 h-3.5')}
            </button>
            <p id="studio-start-reason"></p>

          </div>
        </div>
      </div>
    </div>
  `;

  StudioPanel.mount(document.getElementById('studio-right'), tool.id);
  StudioPanel.refreshStart(0);
  RunStage.mount(document.getElementById('studio-stage-left'), tool.id, document.getElementById('studio-btn-execute'), syncStudioPanelToRun);

  if (tool.id === 'subtitle_animator') {
    setTimeout(() => {
      initSubtitleStudio();
    }, 30);
  }
}

function getDefaultOptionsForTool(toolId) {
  if (toolId === 'pdf_merge') return { mode: 'merge' };
  if (toolId === 'pdf_split') return { mode: 'split', split_mode: 'each_page', ranges: '1-3', every_n: 2 };
  if (toolId === 'pdf_compress') return { preset: 'balanced', target_kb: 0 };
  if (toolId === 'pdf_studio') return { mode: 'merge', split_mode: 'ranges', ranges: '1-', every_n: 1 };
  if (toolId === 'media_audio_extractor') return { format: 'MP3 (320 kbps Studio Quality)' };
  if (toolId === 'video_compressor') return { mode: 'Balanced', limit_mb: 0 };
  if (toolId === 'pdf_converter') return { mode: 'PDF to Images (PNG)' };
  if (toolId === 'image_webp_compress') return { preset: 'balanced', target_kb: 0 };
  if (toolId === 'system_batch_rename') return { rule: 'Add Suffix', text1: '_v1', text2: '', op_mode: 'Save to Destination' };
  if (toolId === 'subtitle_animator') return {
    style: 'white_box',
    font_name: 'Montserrat',
    font_path: '',
    font_size: 46,
    primary_color: '#000000',
    highlight_color: '#FFE600',
    outline_color: '#FFFFFF',
    outline_width: 3,
    position: 'bottom',
    all_caps: false,
    chunk_size: 4,
    subtitles: getSampleSubtitleCues()
  };
  return {};
}

function getDropzoneHint(toolId) {
  if (toolId === 'pdf_merge') return 'Select or drop PDF documents (drag list items to reorder merge sequence)';
  if (toolId === 'pdf_split') return 'Select or drop a PDF document to split or extract pages';
  if (toolId === 'pdf_compress') return 'Select or drop PDF documents to compress and optimize file size';
  if (toolId === 'pdf_studio') return 'Select or drop PDF documents (drag list items to reorder merge sequence)';
  if (toolId === 'media_audio_extractor') return 'Supports MP4, MKV, MOV, WebM, AVI, FLV, WMV';
  if (toolId === 'video_compressor') return 'Supports MP4, MKV, MOV, WebM, AVI';
  if (toolId === 'pdf_converter') return 'Supports PDF documents and JPG/PNG images';
  if (toolId === 'image_webp_compress') return 'Supports PNG, JPG, JPEG, BMP, WebP';
  if (toolId === 'system_batch_rename') return 'Select any files or folder to batch rename';
  if (toolId === 'subtitle_animator') return 'Supports Video (MP4, MKV, MOV, WebM) + Subtitles (.srt, .vtt)';
  return 'Select or drop your files';
}

function renderToolSpecificOptions(toolId) {
  if (toolId === 'pdf_merge') {
    const mergeIconSvg = `<svg class="w-4 h-4 text-[var(--brand-primary)] shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/><rect x="8" y="6" width="12" height="14" rx="1.5"/><path d="M12 13h4"/><path d="M14 11v4"/></svg>`;
    return `
      <div class="space-y-2">
        <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">Merge Sequence</span>
        <div class="p-3 rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] space-y-1">
          <div class="font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
            ${mergeIconSvg}
            <span>Sequential File Ordering</span>
          </div>
          <p class="text-[11px] leading-relaxed">Files merge from top to bottom. Drag and reorder the files on the left list to set your desired page sequence.</p>
        </div>
      </div>
    `;
  }

  if (toolId === 'pdf_split') {
    const splitMode = state.activeToolOptions.split_mode || 'each_page';
    const ranges = state.activeToolOptions.ranges || '1-';
    const everyN = state.activeToolOptions.every_n || 1;

    return `
      <div class="space-y-2.5">
        ${OptionsUI.segmented({
          key: 'split_mode',
          label: 'Split method',
          current: splitMode,
          options: [
            { value: 'each_page', label: 'Every page' },
            { value: 'every_n', label: 'Every N pages' },
            { value: 'ranges', label: 'Page ranges' }
          ]
        })}

        ${splitMode === 'ranges' ? `
          <label class="opt-field">
            <span class="opt-label">Pages</span>
            <input type="text" value="${escapeAttr(ranges)}" data-action="pdf-ranges-input" placeholder="1-3, 5, 8-" />
            <span class="opt-hint">Commas between ranges. "8-" means page 8 to the end.</span>
          </label>
        ` : ''}

        ${splitMode === 'every_n' ? `
          <label class="opt-field">
            <span class="opt-label">Pages per file</span>
            <input type="number" min="1" max="500" value="${everyN}" data-action="pdf-every-n-input" />
          </label>
        ` : ''}

        ${splitMode === 'each_page' ? `
          <p class="opt-hint">Each page becomes its own PDF.</p>
        ` : ''}
      </div>
    `;
  }
  if (toolId === 'pdf_studio') {
    const mode = state.activeToolOptions.mode || 'merge';
    const splitMode = state.activeToolOptions.split_mode || 'ranges';
    const ranges = state.activeToolOptions.ranges || '1-';
    const everyN = state.activeToolOptions.every_n || 1;

    const mergeIconSvg = `<svg class="w-4 h-4 text-[var(--brand-primary)] shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/><rect x="8" y="6" width="12" height="14" rx="1.5"/><path d="M12 13h4"/><path d="M14 11v4"/></svg>`;
    const splitIconSvg = `<svg class="w-4 h-4 text-[var(--brand-primary)] shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>`;

    return `
      <!-- Operation Mode Tabs -->
      <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">Operation Mode</span>
      <div class="grid grid-cols-2 gap-2 pt-0.5">
        <button 
          type="button"
          data-action="set-pdf-mode" data-mode="merge"
          class="p-2.5 rounded-md border text-left text-xs transition-all cursor-pointer ${mode === 'merge' ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] font-semibold text-[var(--brand-primary)] shadow-xs' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-primary)] hover:border-[var(--border-hover)]'}"
        >
          <div class="font-bold flex items-center gap-1.5">
            ${mergeIconSvg}
            <span>Merge</span>
          </div>
          <div class="text-[10px] text-[var(--text-secondary)] mt-0.5 font-normal">Combine files in order</div>
        </button>

        <button 
          type="button"
          data-action="set-pdf-mode" data-mode="split"
          class="p-2.5 rounded-md border text-left text-xs transition-all cursor-pointer ${mode === 'split' ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] font-semibold text-[var(--brand-primary)] shadow-xs' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-primary)] hover:border-[var(--border-hover)]'}"
        >
          <div class="font-bold flex items-center gap-1.5">
            ${splitIconSvg}
            <span>Split</span>
          </div>
          <div class="text-[10px] text-[var(--text-secondary)] mt-0.5 font-normal">Extract or slice pages</div>
        </button>
      </div>

      ${mode === 'merge' ? `
        <div class="p-2.5 rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] space-y-0.5">
          <div class="font-medium text-[var(--text-primary)]">Merge Sequence</div>
          <div class="text-[10px]">Files merge in order. Drag items on the left to reorder.</div>
        </div>
      ` : `
        <div class="space-y-2.5 pt-1 border-t border-[var(--border-subtle)]">
          <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">Split Method</span>
          <div class="grid grid-cols-3 gap-1.5">
            ${[
              { id: 'ranges', label: 'Page Ranges' },
              { id: 'each_page', label: 'Single Pages' },
              { id: 'every_n', label: 'Every N Pages' }
            ].map(sm => `
              <button 
                type="button" 
                data-action="set-pdf-split-mode" data-split-mode="${escapeAttr(sm.id)}"
                class="py-1.5 px-1 rounded-md border text-center text-[11px] transition-all cursor-pointer ${splitMode === sm.id ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] font-bold text-[var(--brand-primary)]' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
              >
                ${sm.label}
              </button>
            `).join('')}
          </div>

          ${splitMode === 'ranges' ? `
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-[var(--text-secondary)]">Page Ranges (e.g. 1-3, 5, 8-)</label>
              <input 
                type="text" 
                value="${escapeAttr(ranges)}" 
                data-action="pdf-ranges-input" 
                placeholder="1-3, 5, 8-" 
                class="w-full px-2.5 py-1 text-xs rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] font-mono"
              />
              <span class="text-[10px] text-[var(--text-muted)] block">Separate ranges with commas. Use '8-' for page 8 to end.</span>
            </div>
          ` : ''}

          ${splitMode === 'every_n' ? `
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-[var(--text-secondary)]">Split Every N Pages</label>
              <input 
                type="number" 
                min="1" 
                max="500" 
                value="${everyN}" 
                data-action="pdf-every-n-input" 
                class="w-full px-2.5 py-1 text-xs rounded-md bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] font-mono"
              />
            </div>
          ` : ''}

          ${splitMode === 'each_page' ? `
            <div class="p-2 rounded-md bg-[var(--surface-inset)] text-[10px] text-[var(--text-secondary)]">
              Extracts each page as an individual zero-padded PDF (<code class="text-[var(--brand-primary)] font-mono">page_001.pdf</code>).
            </div>
          ` : ''}
        </div>
      `}
    `;
  } else if (toolId === 'media_audio_extractor') {
    return `
      <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Target Audio Format & Bitrate</span>
      ${renderCustomDropdown({
        id: 'dropdown-audio-fmt',
        currentValue: state.activeToolOptions.format || 'MP3 (320 kbps Studio Quality)',
        options: [
          { value: 'MP3 (320 kbps Studio Quality)', label: 'MP3 (320 kbps Studio Quality)' },
          { value: 'MP3 (192 kbps Standard)', label: 'MP3 (192 kbps Standard)' },
          { value: 'MP3 (128 kbps Compact)', label: 'MP3 (128 kbps Compact)' },
          { value: 'WAV (Lossless 16-bit PCM)', label: 'WAV (Lossless 16-bit PCM)' },
          { value: 'AAC (M4A High-Efficiency)', label: 'AAC (M4A High-Efficiency)' },
          { value: 'FLAC (Lossless Master)', label: 'FLAC (Lossless Master)' },
          { value: 'OGG (Vorbis Quality 6)', label: 'OGG (Vorbis Quality 6)' },
          { value: 'Direct Stream Copy (Ultra-Fast 1-Sec)', label: 'Direct Stream Copy (Ultra-Fast 1-Sec)' }
        ],
        onSelect: 'handleSelectAudioFmt'
      })}
    `;
  } else if (toolId === 'video_compressor') {
    return OptionsUI.videoGoal(state.activeToolOptions);
  } else if (toolId === 'pdf_compress') {
    return OptionsUI.compressGoal(state.activeToolOptions, 'pdf');
  } else if (toolId === 'pdf_converter') {
    return `
      <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Conversion Target</span>
      ${renderCustomDropdown({
        id: 'dropdown-pdf-mode',
        currentValue: state.activeToolOptions.mode || 'PDF to Images (PNG)',
        options: [
          { value: 'PDF to Images (PNG)', label: 'PDF to Images (PNG)' },
          { value: 'PDF to Images (JPG)', label: 'PDF to Images (JPG)' },
          { value: 'Images to PDF Document', label: 'Images to PDF Document' },
          { value: 'PDF to Plain Text (.txt)', label: 'PDF to Plain Text (.txt)' }
        ],
        onSelect: 'handleSelectPdfMode'
      })}
    `;
  } else if (toolId === 'image_webp_compress') {
    return OptionsUI.compressGoal(state.activeToolOptions, 'image');
  } else if (toolId === 'system_batch_rename') {
    return `
      <div class="space-y-3">
        <div>
          <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Output Mode</span>
          ${renderCustomDropdown({
            id: 'dropdown-rename-mode',
            currentValue: state.activeToolOptions.op_mode || 'Save to Destination',
            options: [
              { value: 'Save to Destination', label: 'Save Renamed Files to Destination Folder' },
              { value: 'Rename In-Place', label: 'Rename In-Place (Modify original files directly)' }
            ],
            onSelect: 'handleSelectRenameOpMode'
          })}
        </div>
        <div>
          <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Renaming Rule</span>
          ${renderCustomDropdown({
            id: 'dropdown-rename-rule',
            currentValue: state.activeToolOptions.rule || 'Add Suffix',
            options: [
              { value: 'Add Suffix', label: 'Add Suffix (e.g. _final)' },
              { value: 'Add Prefix', label: 'Add Prefix (e.g. 2026_)' },
              { value: 'Sequential Numbering', label: 'Sequential Numbering (_01, _02)' },
              { value: 'Find & Replace String', label: 'Find & Replace String' },
              { value: 'Lowercase all characters', label: 'Lowercase all characters' },
              { value: 'UPPERCASE all characters', label: 'UPPERCASE all characters' }
            ],
            onSelect: 'handleSelectRenameRule'
          })}
        </div>
        ${renderRenameTextInputs(state.activeToolOptions)}
      </div>
    `;
  } else if (toolId === 'subtitle_animator') {
    const opts = state.activeToolOptions || {};
    const presets = [
      { id: 'white_box', name: 'Clean White Tag', desc: 'Viral rounded white pill badges with bold black text' },
      { id: 'hormozi', name: 'The Hormozi Punch', desc: 'Bold uppercase, neon yellow active pop, heavy stroke' },
      { id: 'bounce', name: 'Pop & Bounce', desc: 'Playful spring scale bounce on each word entry' },
      { id: 'minimal', name: 'Clean Minimal Box', desc: 'Crisp text on translucent dark backdrop' }
    ];
    const isBoxStyle = (opts.style === 'minimal' || opts.style === 'white_box');

    return `
      <div class="space-y-4">
        <!-- Preset Style Cards -->
        <div>
          <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Viral Animation Presets</span>
          <div class="grid grid-cols-2 gap-2 pt-1.5">
            ${presets.map(p => `
              <button
                type="button"
                data-action="sub-select-style" data-style="${escapeAttr(p.id)}"
                class="p-2.5 rounded-lg border text-left transition-all cursor-pointer ${opts.style === p.id ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] font-semibold text-[var(--brand-primary)] ring-1 ring-[var(--brand-primary)]' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-primary)] hover:border-[var(--border-hover)]'}"
              >
                <div class="text-xs font-bold">${p.name}</div>
                <div class="text-[10px] text-[var(--text-secondary)] line-clamp-1 mt-0.5">${p.desc}</div>
              </button>
            `).join('')}
          </div>
        </div>

        <!-- Typography & Custom Font -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Font Family</span>
            <button 
              type="button" 
              data-action="sub-browse-font" 
              class="text-[11px] text-[var(--brand-primary)] hover:underline flex items-center gap-1 cursor-pointer font-medium"
            >
              ${getIcon('plus', 'w-3 h-3')}
              <span>${opts.font_path ? 'Custom Font Loaded ✓' : 'Upload .TTF / .OTF'}</span>
            </button>
          </div>
          ${renderCustomDropdown({
            id: 'dropdown-sub-font',
            currentValue: opts.font_name || 'Montserrat',
            options: [
              { value: 'Montserrat', label: 'Montserrat (Ultra Bold)' },
              { value: 'Impact', label: 'Impact / Heavy' },
              { value: 'Arial', label: 'Arial (Clean Sans)' },
              { value: 'Trebuchet MS', label: 'Trebuchet MS' },
              { value: 'Roboto', label: 'Roboto' },
              { value: 'TheBoldFont', label: 'The Bold Font' },
              ...(opts.font_path ? [{ value: opts.font_name, label: `Custom: ${opts.font_name}` }] : [])
            ],
            onSelect: 'handleSelectSubtitleFont'
          })}
        </div>

        <!-- Color Controls (Conditional for Box Styles vs Word Highlight) -->
        ${isBoxStyle ? `
          <div class="grid grid-cols-2 gap-2">
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Text Color</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.primary_color || (opts.style === 'white_box' ? '#000000' : '#FFFFFF')}" data-action="sub-color-change" data-color-prop="primary_color" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.primary_color || (opts.style === 'white_box' ? '#000' : '#FFF')}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">${opts.style === 'white_box' ? 'Tag Background' : 'Box Background'}</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.outline_color || (opts.style === 'white_box' ? '#FFFFFF' : '#0F172A')}" data-action="sub-color-change" data-color-prop="outline_color" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.outline_color || (opts.style === 'white_box' ? '#FFF' : '#0F172A')}</span>
              </div>
            </div>
          </div>
        ` : `
          <div class="grid grid-cols-3 gap-2">
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Base Text</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.primary_color || '#FFFFFF'}" data-action="sub-color-change" data-color-prop="primary_color" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.primary_color || '#FFF'}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Active Highlight</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.highlight_color || '#FFE600'}" data-action="sub-color-change" data-color-prop="highlight_color" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.highlight_color || '#FFE600'}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Outline Stroke</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.outline_color || '#000000'}" data-action="sub-color-change" data-color-prop="outline_color" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.outline_color || '#000'}</span>
              </div>
            </div>
          </div>
        `}

        <!-- Sizing & Placement -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-semibold text-[var(--text-muted)] uppercase tracking-wider text-[10px]">Font Size</span>
              <span id="sub-fontsize-val" class="font-bold text-[var(--brand-primary)] tabular-nums">${opts.font_size || 46}px</span>
            </div>
            <input 
              type="range" 
              min="28" 
              max="72" 
              value="${opts.font_size || 48}" 
              data-action="sub-fontsize-input" 
              class="w-full accent-[var(--brand-primary)] cursor-pointer" 
            />
          </div>
          <div>
            <span class="font-semibold text-[var(--text-muted)] uppercase tracking-wider text-[10px] block mb-1">Vertical Position</span>
            <div class="grid grid-cols-3 gap-1">
              ${['Bottom', 'Middle', 'Top'].map(p => {
                const pKey = p.toLowerCase();
                const isSel = (opts.position || 'bottom') === pKey;
                return `
                  <button 
                    type="button" 
                    data-action="sub-set-position" data-pos="${escapeAttr(pKey)}" 
                    class="py-1 px-1.5 rounded text-[11px] font-medium border text-center transition-all cursor-pointer ${isSel ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] text-[var(--brand-primary)] font-bold' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
                  >
                    ${p}
                  </button>
                `;
              }).join('')}
            </div>
          </div>
        </div>

        <!-- Pacing & Casing Options -->
        <div class="flex items-center justify-between pt-1 border-t border-[var(--border-subtle)] text-xs">
          <label class="flex items-center gap-2 cursor-pointer">
            <input 
              type="checkbox" 
              ${opts.all_caps ? 'checked' : ''} 
              data-action="sub-all-caps-change" 
              class="rounded text-[var(--brand-primary)] accent-[var(--brand-primary)] cursor-pointer" 
            />
            <span class="font-medium text-[var(--text-primary)]">Force UPPERCASE</span>
          </label>
          <div class="flex items-center gap-1.5">
            <button 
              type="button" 
              data-action="sub-load-demo" 
              class="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
            >
              Reset to Demo Cues
            </button>
          </div>
        </div>
      </div>
    `;
  }
  return '';
}

// ── Custom Dropdown Component ───────────────────────────────────────────────
function renderCustomDropdown({ id, currentValue, options, onSelect }) {
  const currentItem = options.find(o => (typeof o === 'string' ? o : o.value) === currentValue);
  const currentLabel = currentItem 
    ? (typeof currentItem === 'string' ? currentItem : currentItem.label) 
    : (typeof options[0] === 'string' ? options[0] : options[0].label);

  const optionsHtml = options.map(opt => {
    const val = typeof opt === 'string' ? opt : opt.value;
    const lbl = typeof opt === 'string' ? opt : opt.label;
    const isSelected = val === currentValue;
    const safeVal = val.replace(/'/g, "\\'");
    const safeLbl = lbl.replace(/'/g, "\\'");
    return `
      <div 
        role="option"
        aria-selected="${isSelected}"
        data-action="select-dropdown-option" data-dd-id="${escapeAttr(id)}" data-dd-val="${escapeAttr(val)}" data-dd-lbl="${escapeAttr(lbl)}" data-dd-callback="${escapeAttr(onSelect)}"
        class="custom-dropdown-item ${isSelected ? 'active' : ''}"
      >
        <span class="truncate">${lbl}</span>
        ${isSelected ? `<span class="item-check">${getIcon('check', 'w-3.5 h-3.5')}</span>` : ''}
      </div>
    `;
  }).join('');

  return `
    <div class="custom-dropdown-container mt-1.5" id="${id}">
      <button 
        type="button"
        data-action="toggle-dropdown" data-dd-id="${escapeAttr(id)}"
        class="custom-dropdown-trigger"
      >
        <span class="custom-dropdown-current-label truncate">${currentLabel}</span>
        <span class="custom-dropdown-chevron">
          ${getIcon('chevron-down', 'w-3.5 h-3.5')}
        </span>
      </button>

      <div class="custom-dropdown-menu">
        ${optionsHtml}
      </div>
    </div>
  `;
}

function toggleCustomDropdown(dropdownId, e) {
  if (e) {
    e.stopPropagation();
    e.preventDefault();
  }
  const dropdown = document.getElementById(dropdownId);
  if (!dropdown) return;
  const wasOpen = dropdown.classList.contains('open');

  // Close any other open dropdowns first
  closeAllCustomDropdowns();

  if (!wasOpen) {
    dropdown.classList.add('open');
  }
}

function closeAllCustomDropdowns() {
  document.querySelectorAll('.custom-dropdown-container.open').forEach(d => {
    d.classList.remove('open');
  });
}

function selectCustomDropdownOption(dropdownId, value, label, callbackName) {
  const dropdown = document.getElementById(dropdownId);
  if (dropdown) {
    const currentLbl = dropdown.querySelector('.custom-dropdown-current-label');
    if (currentLbl) currentLbl.innerText = label;
  }
  closeAllCustomDropdowns();

  if (callbackName && typeof window[callbackName] === 'function') {
    window[callbackName](value);
  }
}

window.handleSelectAudioFmt = function(val) {
  state.activeToolOptions.format = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
};

window.handleSelectPdfMode = function(val) {
  state.activeToolOptions.mode = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
};

function renderRenameTextInputs(options) {
  const rule = options.rule || 'Add Suffix';
  const field = (label, action, value, placeholder) => `
    <label class="opt-field">
      <span class="opt-label">${label}</span>
      <input type="text" value="${escapeAttr(value)}" placeholder="${escapeAttr(placeholder)}" data-action="${action}" />
    </label>`;
  if (rule.includes('Find & Replace')) {
    return field('Find', 'renamer-text-input', options.text1 || '', 'IMG_')
      + field('Replace with', 'renamer-text2-input', options.text2 || '', 'Trip_');
  }
  if (rule.includes('Prefix') || rule.includes('Suffix')) {
    return field(rule.includes('Prefix') ? 'Text to add at the start' : 'Text to add at the end', 'renamer-text-input', options.text1 ?? '_v1', '_v1');
  }
  return '';
}

window.handleSelectRenameRule = function(val) {
  state.activeToolOptions.rule = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
  refreshStudioPreview();
};

window.handleSelectRenameOpMode = function(val) {
  state.activeToolOptions.op_mode = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
};

function setStudioMode(modeName) {
  state.activeToolOptions.mode = modeName;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
}

async function handleStudioBrowseFiles(toolId, isAppend = false) {
  let fileTypes = [];
  if (['pdf_studio', 'pdf_merge', 'pdf_split'].includes(toolId)) {
    fileTypes = ['PDF Documents (*.pdf)', 'All Files (*.*)'];
  } else if (toolId === 'video_compressor') {
    fileTypes = ['Video Files (*.mp4;*.mkv;*.mov;*.webm;*.avi;*.flv;*.wmv;*.m4v)'];
  } else if (toolId === 'media_audio_extractor') {
    fileTypes = ['Audio Video Files (*.mp4;*.mkv;*.mov;*.webm;*.avi;*.flv;*.wmv;*.mp3;*.wav;*.m4a;*.flac;*.ogg)'];
  } else if (toolId === 'pdf_converter') {
    fileTypes = ['Document Files (*.pdf;*.png;*.jpg;*.jpeg)'];
  } else if (toolId === 'image_webp_compress') {
    fileTypes = ['Image Files (*.png;*.jpg;*.jpeg;*.bmp;*.webp)'];
  } else if (toolId === 'subtitle_animator') {
    fileTypes = ['Media & Subtitle Files (*.mp4;*.mkv;*.mov;*.webm;*.srt;*.vtt)', 'Video Files (*.mp4;*.mkv;*.mov;*.webm)', 'Subtitle Files (*.srt;*.vtt)', 'All Files (*.*)'];
  } else {
    fileTypes = ['All Files (*.*)'];
  }

  const files = await callBridge('browse_files', fileTypes);
  if (files && files.length > 0) {
    if (isAppend) {
      // Append unique files
      const existing = new Set(state.selectedFiles);
      files.forEach(f => {
        if (!existing.has(f)) state.selectedFiles.push(f);
      });
    } else {
      state.selectedFiles = files;
    }
    updateStudioFilesUI();
    if (['pdf_studio', 'pdf_merge', 'pdf_split'].includes(toolId)) {
      inspectSelectedPdfFiles(state.selectedFiles);
    } else if (toolId === 'subtitle_animator') {
      await handleSubtitleFilesLoaded(files);
    }
  }
}

// PDF Inspection Cache for badges
let pdfFilesMeta = {};

async function inspectSelectedPdfFiles(files) {
  try {
    const inspected = await callBridge('inspect_pdf', files);
    if (inspected && Array.isArray(inspected)) {
      inspected.forEach(item => {
        if (item.file) {
          pdfFilesMeta[item.file] = item;
        }
      });
      updateStudioFilesUI();
    }
  } catch (e) {
    console.error('PDF inspect error:', e);
  }
}

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Tools whose files are photos: shown as a thumbnail grid, since order does not matter.
const GRID_TOOLS = new Set(['image_webp_compress']);
let imageFilesMeta = {};
const thumbnailsInFlight = new Set();

async function loadImageThumbnails(files) {
  const missing = files.filter(f => !imageFilesMeta[f] && !thumbnailsInFlight.has(f));
  if (!missing.length) return;
  missing.forEach(f => thumbnailsInFlight.add(f));
  const results = await callBridge('get_thumbnails', missing);
  missing.forEach(f => thumbnailsInFlight.delete(f));
  (results || []).forEach(item => { imageFilesMeta[item.file] = item; });
  if (results && results.length) updateStudioFilesUI();
}

function updateStudioFilesUI() {
  const wrap = document.getElementById('studio-files-wrap');
  const countLbl = document.getElementById('studio-files-count');
  const list = document.getElementById('studio-files-list');
  const dropzone = document.getElementById('studio-dropzone');
  const dropTitle = dropzone ? dropzone.querySelector('h4') : null;
  const dropHint = dropzone ? dropzone.querySelector('p') : null;

  // Calculate live total bytes and pages
  let totalBytes = 0;
  let totalKnownPages = 0;
  state.selectedFiles.forEach(f => {
    const meta = pdfFilesMeta[f] || {};
    if (meta.size_bytes) totalBytes += meta.size_bytes;
    if (meta.pages) totalKnownPages += meta.pages;
  });

  // Update right pane summary card
  const summaryCount = document.getElementById('studio-summary-count');
  const summarySize = document.getElementById('studio-summary-size');
  if (summaryCount) {
    summaryCount.innerText = `${state.selectedFiles.length} file${state.selectedFiles.length === 1 ? '' : 's'}${totalKnownPages > 0 ? ` (${totalKnownPages} total pages)` : ''}`;
  }
  if (summarySize) {
    summarySize.innerText = formatBytes(totalBytes);
  }

  syncStudioPanelToFiles();

  if (state.selectedFiles.length === 0) {
    if (wrap) wrap.classList.add('hidden');
    if (dropzone) dropzone.classList.remove('ft-compact');
    if (dropTitle) {
      dropTitle.innerText = `Drop ${['pdf_studio', 'pdf_merge', 'pdf_split'].includes(state.activeToolId) ? 'PDF' : ''} files here`;
    }
    if (dropHint) {
      dropHint.innerHTML = `or click to <span class="text-[var(--brand-primary)] font-medium">browse</span>`;
    }
    return;
  }

  // With files present the drop area shrinks to a slim bar; the list becomes the focus.
  if (dropzone) dropzone.classList.add('ft-compact');
  if (dropTitle) dropTitle.innerText = 'Add more files';

  if (wrap) wrap.classList.remove('hidden');
  if (countLbl) {
    const sizeSummary = totalBytes > 0 ? ` • ${formatBytes(totalBytes)}` : '';
    countLbl.innerText = `${state.selectedFiles.length} file${state.selectedFiles.length > 1 ? 's' : ''}${sizeSummary}`;
  }

  if (!list) return;
  const reorderable = ['pdf_studio', 'pdf_merge'].includes(state.activeToolId) && state.selectedFiles.length > 1;
  const layout = GRID_TOOLS.has(state.activeToolId) ? 'grid' : 'list';
  FileTray.render(list, state.selectedFiles, { meta: { ...pdfFilesMeta, ...imageFilesMeta }, reorderable, layout });
  if (layout === 'grid') loadImageThumbnails(state.selectedFiles);
  FileTray.bindReorder(list, (fromIndex, toIndex) => {
    const [moved] = state.selectedFiles.splice(fromIndex, 1);
    state.selectedFiles.splice(toIndex, 0, moved);
    updateStudioFilesUI();
  });
}

// Reordering logic
let draggedPdfIndex = null;

function moveStudioFile(idx, delta) {
  const newIdx = idx + delta;
  if (newIdx >= 0 && newIdx < state.selectedFiles.length) {
    const item = state.selectedFiles.splice(idx, 1)[0];
    state.selectedFiles.splice(newIdx, 0, item);
    updateStudioFilesUI();
  }
}

window.handlePdfDragStart = function(e, idx) {
  draggedPdfIndex = idx;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(idx));
  }
  const item = e.currentTarget || e.target.closest('.file-drag-item');
  if (item) item.classList.add('opacity-50');
};

window.handlePdfDragOver = function(e) {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
  const target = e.currentTarget || e.target.closest('.file-drag-item');
  if (!target) return;
  const rect = target.getBoundingClientRect();
  const relY = e.clientY - rect.top;
  if (relY < rect.height / 2) {
    target.classList.add('border-t-2', 'border-[var(--brand-primary)]');
    target.classList.remove('border-b-2');
  } else {
    target.classList.add('border-b-2', 'border-[var(--brand-primary)]');
    target.classList.remove('border-t-2');
  }
};

window.handlePdfDragLeave = function(e) {
  const target = e.currentTarget || e.target.closest('.file-drag-item');
  if (target) {
    target.classList.remove('border-t-2', 'border-b-2', 'border-[var(--brand-primary)]', 'opacity-50');
  }
};

window.handlePdfDrop = function(e, targetIdx) {
  e.preventDefault();
  const target = e.currentTarget || e.target.closest('.file-drag-item');
  if (target) {
    target.classList.remove('border-t-2', 'border-b-2', 'border-[var(--brand-primary)]', 'opacity-50');
  }
  let sourceIdx = draggedPdfIndex;
  if (sourceIdx === null && e.dataTransfer) {
    const data = e.dataTransfer.getData('text/plain');
    if (data !== '') sourceIdx = parseInt(data, 10);
  }
  draggedPdfIndex = null;
  if (sourceIdx === null || isNaN(sourceIdx) || isNaN(targetIdx) || sourceIdx === targetIdx) {
    return;
  }
  if (sourceIdx >= 0 && sourceIdx < state.selectedFiles.length && targetIdx >= 0 && targetIdx < state.selectedFiles.length) {
    const item = state.selectedFiles.splice(sourceIdx, 1)[0];
    state.selectedFiles.splice(targetIdx, 0, item);
    updateStudioFilesUI();
  }
};

function removeStudioFile(idx) {
  if (idx < 0 || idx >= state.selectedFiles.length) return;
  const list = document.getElementById('studio-files-list');
  const commit = () => {
    state.selectedFiles.splice(idx, 1);
    updateStudioFilesUI();
  };
  if (list) FileTray.animateRemoval(list, idx, commit);
  else commit();
}

window.removePdfFile = function(idx) {
  removeStudioFile(idx);
};

function clearStudioFiles() {
  state.selectedFiles = [];
  pdfFilesMeta = {};
  updateStudioFilesUI();
}

async function handleStudioBrowseOutFolder() {
  const dir = await callBridge('browse_directory');
  if (dir) {
    const inp = document.getElementById('studio-out-folder');
    if (inp) inp.value = dir;
    state.customOutputDir = dir;
  }
}

function handleOpenOutputFile() {
  if (state.lastOutputFile) {
    callBridge('open_file', state.lastOutputFile);
  }
}

function handleRevealOutputFolder() {
  if (state.lastOutputFile) {
    callBridge('reveal_file', state.lastOutputFile);
  }
}

async function handleStudioToggleFavorite(toolId, btn) {
  const updated = await callBridge('toggle_favorite', toolId);
  if (updated) {
    state.favorites = updated;
    const isFav = state.favorites.includes(toolId);
    btn.innerHTML = isFav ? getIcon('heartFilled', 'w-4 h-4') : getIcon('heart', 'w-4 h-4');
  }
}

// ── Tool Execution & Bridge Callbacks ────────────────────────────────────────
async function handleExecuteTool(toolId) {
  if (state.selectedFiles.length === 0) {
    alert('Please select or drop at least one file to process.');
    return;
  }

  const outDir = document.getElementById('studio-out-folder')?.value || state.defaultDownloads;
  state.isToolRunning = true;

  const btnExec = document.getElementById('studio-btn-execute');
  if (btnExec) {
    btnExec.disabled = true;
    btnExec.classList.add('opacity-50');
  }
  RunStage.start(state.selectedFiles);

  if (toolId === 'pdf_merge') {
    state.activeToolOptions.mode = 'merge';
  } else if (toolId === 'pdf_split') {
    state.activeToolOptions.mode = 'split';
  }

  const customFileName = document.getElementById('studio-out-filename')?.value?.trim();
  if (customFileName) {
    state.activeToolOptions.custom_filename = customFileName;
    state.activeToolOptions.output_filename = customFileName;
  }

  await callBridge('execute_tool', toolId, state.selectedFiles, state.activeToolOptions, outDir);
}

async function handleCancelTool() {
  RunStage.stopping();
  const hadActiveJob = await callBridge('cancel_tool');
  // No engine left to stop means no CANCELLED event will arrive; reset the screen ourselves.
  if (!hadActiveJob) window.onToolError('Operation cancelled.');
}

// Bridge Event Handlers (Called by Python evaluate_js)
window.onToolProgress = function(data) {
  const pct = data.indeterminate ? -1 : data.percent;
  RunStage.progress(pct, data.status);
};

window.onToolLog = function(msg) {
  RunStage.log(msg);
};

window.onToolComplete = function(data) {
  state.isToolRunning = false;
  state.lastOutputFile = data.output_file || '';
  const stats = data.stats || null;

  if (state.lastOutputFile) {
    const fullPath = state.lastOutputFile;
    const fileName = fullPath.split('\\').pop().split('/').pop();
    const fileExt = fileName.split('.').pop() || 'file';
    const activeTool = state.tools.find(t => t.id === state.activeToolId);
    recordRecentFile({
      path: fullPath,
      name: fileName,
      ext: fileExt,
      toolId: state.activeToolId,
      toolName: activeTool ? activeTool.name : 'Boltools',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
  }

  const btnExec = document.getElementById('studio-btn-execute');
  if (btnExec) {
    btnExec.disabled = false;
    btnExec.classList.remove('opacity-50');
  }

  const outputs = [].concat(data.outputs || data.output_file || []).filter(Boolean);
  RunStage.complete({ outputs, stats, requestedName: state.activeToolOptions.custom_filename });
  StudioPanel.showNext(outputs, toolId => state.tools.some(t => t.id === toolId), openToolWithFiles);
};

// The right column follows the run: locked while working, editable again after a stop or error.
function syncStudioPanelToRun(runState) {
  if (runState === 'running') StudioPanel.setPhase('running');
  else if (runState === 'failed' || runState === 'stopped') StudioPanel.setPhase('ready');
  else if (runState === 'idle') StudioPanel.setPhase(state.selectedFiles.length ? 'ready' : 'empty');
}

function syncStudioPanelToFiles() {
  refreshStudioPreview();
  prefillSingleFileName();
  const stageBusy = document.getElementById('studio-stage-left')?.classList.contains('th-on');
  if (!stageBusy) StudioPanel.setPhase(state.selectedFiles.length ? 'ready' : 'empty');
}

// One file in: offer its own name, so the output field never says "output_result".
function prefillSingleFileName() {
  const field = document.getElementById('studio-out-filename');
  if (!field || state.selectedFiles.length !== 1 || ToolUX.get(state.activeToolId).namesOutput !== 'single') return;
  if (field.value && field.value !== 'output_result' && field.dataset.autofilled !== 'true') return;
  const base = state.selectedFiles[0].split(/[\\/]/).pop();
  field.value = base.replace(/\.[^.]+$/, '');
  field.dataset.autofilled = 'true';
}

// Re-run after any setting that changes the outcome (split ranges, rename rule).
function refreshStudioPreview() {
  const preview = document.getElementById('studio-preview');
  const label = FilePreviews.render(preview, state.activeToolId, state.selectedFiles, state.activeToolOptions, pdfFilesMeta);
  StudioPanel.refreshStart(state.selectedFiles.length, label);
}

// "Next steps" hand the file just made to another tool, already loaded.
function openToolWithFiles(toolId, files) {
  navigateTo('tool_studio', toolId);
  state.selectedFiles = files.slice();
  updateStudioFilesUI();
  if (files.every(f => f.toLowerCase().endsWith('.pdf'))) inspectSelectedPdfFiles(files);
}

function handleStudioShortcut(e) {
  if (state.currentView !== 'tool_studio') return;
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'o' && !state.isToolRunning) {
    e.preventDefault();
    handleStudioBrowseFiles(state.activeToolId, state.selectedFiles.length > 0);
    return;
  }
  if (e.key === 'Escape' && state.isToolRunning) {
    handleCancelTool();
    return;
  }
  const typing = e.target.closest && e.target.closest('input, textarea, select, button, a, [contenteditable="true"]');
  const startButton = document.getElementById('studio-btn-execute');
  if (e.key === 'Enter' && !typing && startButton && !startButton.hidden && !startButton.disabled && state.selectedFiles.length) {
    e.preventDefault();
    startButton.click();
  }
}

window.onToolError = function(errMsg) {
  state.isToolRunning = false;
  const btnExec = document.getElementById('studio-btn-execute');
  if (btnExec) {
    btnExec.disabled = false;
    btnExec.classList.remove('opacity-50');
  }
  RunStage.fail(errMsg);
};

// ── Subtitle Animation Maker Studio Suite ─────────────────────────────────────
let subPreviewTimer = null;
let subPreviewIsPlaying = false;
let subPreviewCurrentTime = 0.8;
let subPreviewDuration = 8.0;

function getSampleSubtitleCues() {
  return [
    {
      id: 1,
      start: 0.2,
      end: 2.2,
      text: "Instant captions\nfor your videos",
      words: [
        { word: "Instant", start: 0.2, end: 0.7 },
        { word: "captions", start: 0.7, end: 1.2 },
        { word: "for", start: 1.2, end: 1.6 },
        { word: "your", start: 1.6, end: 1.9 },
        { word: "videos", start: 1.9, end: 2.2 }
      ]
    },
    {
      id: 2,
      start: 2.3,
      end: 4.6,
      text: "Viral subtitles\nbuilt offline",
      words: [
        { word: "Viral", start: 2.3, end: 2.8 },
        { word: "subtitles", start: 2.8, end: 3.5 },
        { word: "built", start: 3.5, end: 4.0 },
        { word: "offline", start: 4.0, end: 4.6 }
      ]
    },
    {
      id: 3,
      start: 4.7,
      end: 7.2,
      text: "Zero lag\nmaximum speed",
      words: [
        { word: "Zero", start: 4.7, end: 5.3 },
        { word: "lag", start: 5.3, end: 5.9 },
        { word: "maximum", start: 5.9, end: 6.5 },
        { word: "speed", start: 6.5, end: 7.2 }
      ]
    }
  ];
}

function parseSrtOrVttClient(content) {
  if (!content) return [];
  const lines = content.replace(/\r\n/g, '\n').split('\n');
  const cues = [];
  let cueId = 1;
  const timeRegex = /(\d+:\d+:\d+[,\.]\d+|\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+|\d+:\d+[,\.]\d+)/;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith('WEBVTT') || line.startsWith('NOTE')) continue;

    const match = line.match(timeRegex);
    if (match) {
      const startSec = parseTimestampClient(match[1]);
      const endSec = parseTimestampClient(match[2]);
      i++;
      const textLines = [];
      while (i < lines.length) {
        const nextLine = lines[i].trim();
        if (!nextLine || nextLine.match(timeRegex)) {
          i--;
          break;
        }
        textLines.push(nextLine);
        i++;
      }

      const cleanText = textLines.join(' ').replace(/<[^>]+>/g, '').trim();
      if (cleanText) {
        const words = cleanText.split(/\s+/).filter(Boolean);
        const dur = Math.max(0.2, endSec - startSec);
        const wordTokens = words.map((w, idx) => ({
          word: w,
          start: Math.round((startSec + (idx / words.length) * dur) * 100) / 100,
          end: Math.round((startSec + ((idx + 1) / words.length) * dur) * 100) / 100
        }));

        cues.push({
          id: cueId++,
          start: Math.round(startSec * 100) / 100,
          end: Math.round(endSec * 100) / 100,
          text: cleanText,
          words: wordTokens
        });
      }
    }
  }
  return cues;
}

function parseTimestampClient(ts) {
  const clean = ts.trim().replace(',', '.');
  const parts = clean.split(':');
  if (parts.length === 3) {
    return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
  } else if (parts.length === 2) {
    return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
  }
  return parseFloat(parts[0]) || 0;
}

function formatDisplayTime(sec) {
  const s = Math.max(0, parseFloat(sec) || 0);
  const m = Math.floor(s / 60);
  const remSec = (s % 60).toFixed(2);
  const padSec = remSec < 10 ? '0' + remSec : remSec;
  return `${m < 10 ? '0' + m : m}:${padSec}`;
}

async function handleSubtitleFilesLoaded(files) {
  if (!files || files.length === 0) return;
  const videoExts = ['.mp4', '.mkv', '.mov', '.webm', '.avi', '.flv'];
  const subExts = ['.srt', '.vtt', '.ass'];

  let videoFile = null;
  let subFile = null;

  for (const f of files) {
    const lower = f.toLowerCase();
    if (videoExts.some(ext => lower.endsWith(ext)) && !videoFile) {
      videoFile = f;
    } else if (subExts.some(ext => lower.endsWith(ext)) && !subFile) {
      subFile = f;
    }
  }

  // Load Subtitle Text
  if (subFile) {
    const text = await callBridge('read_text_file', subFile);
    if (text) {
      const parsed = parseSrtOrVttClient(text);
      if (parsed.length > 0) {
        state.activeToolOptions.subtitles = parsed;
        const maxEnd = Math.max(...parsed.map(c => c.end));
        if (maxEnd > subPreviewDuration) subPreviewDuration = maxEnd + 1.0;
        renderSubtitleCuesList();
        updateSubtitleLiveOverlay(subPreviewCurrentTime);
      }
    }
  }

  // Load Video in Preview player
  if (videoFile) {
    loadVideoInPreviewPlayer(videoFile);
  }
}

function loadVideoInPreviewPlayer(videoPathOrUrl) {
  const vidEl = document.getElementById('sub-video-element');
  const emptyBg = document.getElementById('sub-empty-bg');
  if (!vidEl) return;

  try {
    let srcUrl = videoPathOrUrl;
    if (!videoPathOrUrl.startsWith('blob:') && !videoPathOrUrl.startsWith('http')) {
      srcUrl = 'file:///' + videoPathOrUrl.replace(/\\/g, '/');
    }
    vidEl.src = srcUrl;
    vidEl.classList.remove('hidden');
    if (emptyBg) emptyBg.classList.add('hidden');

    vidEl.onloadedmetadata = () => {
      if (vidEl.duration && !isNaN(vidEl.duration)) {
        subPreviewDuration = vidEl.duration;
        const scrubber = document.getElementById('sub-video-scrubber');
        if (scrubber) scrubber.max = vidEl.duration;
        const durLbl = document.getElementById('sub-dur-label');
        if (durLbl) durLbl.innerText = formatDisplayTime(vidEl.duration);
      }
    };

    vidEl.ontimeupdate = () => {
      subPreviewCurrentTime = vidEl.currentTime;
      updateSubtitleTimeDisplays(subPreviewCurrentTime);
      updateSubtitleLiveOverlay(subPreviewCurrentTime);
    };

    vidEl.onended = () => {
      subPreviewIsPlaying = false;
      updatePlayPauseButtonUI();
    };
  } catch (e) {
    console.error('Error loading video preview:', e);
  }
}

function initSubtitleStudio() {
  subPreviewIsPlaying = false;
  subPreviewCurrentTime = 0.8;
  const opts = state.activeToolOptions;
  if (!opts.subtitles || opts.subtitles.length === 0) {
    opts.subtitles = getSampleSubtitleCues();
  }

  const maxEnd = Math.max(...opts.subtitles.map(c => c.end));
  subPreviewDuration = Math.max(8.0, maxEnd + 1.0);

  const scrubber = document.getElementById('sub-video-scrubber');
  if (scrubber) {
    scrubber.max = subPreviewDuration;
    scrubber.value = subPreviewCurrentTime;
  }
  const durLbl = document.getElementById('sub-dur-label');
  if (durLbl) durLbl.innerText = formatDisplayTime(subPreviewDuration);

  renderSubtitleCuesList();
  updateSubtitleTimeDisplays(subPreviewCurrentTime);
  updateSubtitleLiveOverlay(subPreviewCurrentTime);

  // Hook dropzone for HTML5 Drag-and-Drop Video & SRT files
  const dropzone = document.getElementById('studio-dropzone');
  if (dropzone) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('border-[var(--brand-primary)]');
    });
    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('border-[var(--brand-primary)]');
    });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-[var(--brand-primary)]');
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleDroppedSubtitleFiles(e.dataTransfer.files);
      }
    });
  }
}

function handleDroppedSubtitleFiles(fileList) {
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    const name = file.name.toLowerCase();
    if (name.endsWith('.mp4') || name.endsWith('.mov') || name.endsWith('.webm') || name.endsWith('.mkv')) {
      const blobUrl = URL.createObjectURL(file);
      loadVideoInPreviewPlayer(blobUrl);
      if (file.path) {
        state.selectedFiles.push(file.path);
        updateStudioFilesUI();
      }
    } else if (name.endsWith('.srt') || name.endsWith('.vtt')) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        const text = evt.target.result;
        const cues = parseSrtOrVttClient(text);
        if (cues.length > 0) {
          state.activeToolOptions.subtitles = cues;
          const maxEnd = Math.max(...cues.map(c => c.end));
          if (maxEnd > subPreviewDuration) subPreviewDuration = maxEnd + 1.0;
          renderSubtitleCuesList();
          updateSubtitleLiveOverlay(subPreviewCurrentTime);
        }
      };
      reader.readAsText(file);
      if (file.path) {
        state.selectedFiles.push(file.path);
        updateStudioFilesUI();
      }
    }
  }
}

function updateSubtitleTimeDisplays(t) {
  const ind = document.getElementById('sub-time-indicator');
  if (ind) ind.innerText = `${formatDisplayTime(t)} / ${formatDisplayTime(subPreviewDuration)}`;
  const scrubber = document.getElementById('sub-video-scrubber');
  if (scrubber && !scrubber.matches(':active')) scrubber.value = t;
}

function toggleSubtitleVideoPlay() {
  const vidEl = document.getElementById('sub-video-element');
  if (vidEl && !vidEl.classList.contains('hidden') && vidEl.src) {
    if (vidEl.paused) {
      vidEl.play();
      subPreviewIsPlaying = true;
    } else {
      vidEl.pause();
      subPreviewIsPlaying = false;
    }
    updatePlayPauseButtonUI();
    return;
  }

  // Simulated Timer Mode if no video loaded
  subPreviewIsPlaying = !subPreviewIsPlaying;
  updatePlayPauseButtonUI();

  if (subPreviewIsPlaying) {
    if (subPreviewTimer) clearInterval(subPreviewTimer);
    subPreviewTimer = setInterval(() => {
      subPreviewCurrentTime += 0.05;
      if (subPreviewCurrentTime > subPreviewDuration) {
        subPreviewCurrentTime = 0.0;
      }
      updateSubtitleTimeDisplays(subPreviewCurrentTime);
      updateSubtitleLiveOverlay(subPreviewCurrentTime);
    }, 50);
  } else {
    if (subPreviewTimer) clearInterval(subPreviewTimer);
    subPreviewTimer = null;
  }
}

function updatePlayPauseButtonUI() {
  const btn = document.getElementById('sub-btn-playpause');
  if (btn) {
    btn.innerHTML = subPreviewIsPlaying 
      ? `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect width="4" height="16" x="6" y="4" rx="1"/><rect width="4" height="16" x="14" y="4" rx="1"/></svg>`
      : getIcon('play', 'w-3.5 h-3.5');
  }
}

function handleSubtitleScrub(val) {
  const t = parseFloat(val) || 0;
  subPreviewCurrentTime = t;
  const vidEl = document.getElementById('sub-video-element');
  if (vidEl && !vidEl.classList.contains('hidden') && vidEl.src) {
    vidEl.currentTime = t;
  }
  updateSubtitleTimeDisplays(t);
  updateSubtitleLiveOverlay(t);
}

function seekSubtitlePreview(seconds) {
  handleSubtitleScrub(seconds);
}

function updateSubtitleLiveOverlay(currentTime) {
  const overlayBox = document.getElementById('sub-preview-text-box');
  const overlayWrap = document.getElementById('sub-preview-overlay-wrap');
  if (!overlayBox || !overlayWrap) return;

  const opts = state.activeToolOptions || {};
  const cues = opts.subtitles || [];
  const stylePreset = opts.style || 'white_box';
  const pos = opts.position || 'bottom';
  const allCaps = opts.all_caps === true;

  // Apply vertical positioning
  if (pos === 'top') {
    overlayWrap.style.top = '12%';
    overlayWrap.style.bottom = 'auto';
  } else if (pos === 'middle') {
    overlayWrap.style.top = '44%';
    overlayWrap.style.bottom = 'auto';
  } else {
    overlayWrap.style.top = 'auto';
    overlayWrap.style.bottom = '12%';
  }

  // Typography
  overlayBox.style.fontFamily = `"${opts.font_name || 'Montserrat'}", sans-serif`;
  overlayBox.style.fontSize = `${Math.max(16, (opts.font_size || 46) * 0.44)}px`;
  overlayBox.style.color = opts.primary_color || (stylePreset === 'white_box' ? '#000000' : '#FFFFFF');

  // Preset decorations
  const strokeColor = opts.outline_color || '#000000';
  if (stylePreset === 'white_box') {
    overlayBox.style.backgroundColor = 'transparent';
    overlayBox.style.borderRadius = '0px';
    overlayBox.style.padding = '0px';
    overlayBox.style.textShadow = 'none';
  } else if (stylePreset === 'minimal') {
    overlayBox.style.backgroundColor = opts.outline_color || 'rgba(15, 23, 42, 0.85)';
    overlayBox.style.borderRadius = '8px';
    overlayBox.style.padding = '6px 14px';
    overlayBox.style.textShadow = 'none';
  } else {
    overlayBox.style.backgroundColor = 'transparent';
    overlayBox.style.borderRadius = '0px';
    overlayBox.style.padding = '6px 14px';
    overlayBox.style.textShadow = `-2px -2px 0 ${strokeColor}, 2px -2px 0 ${strokeColor}, -2px 2px 0 ${strokeColor}, 2px 2px 0 ${strokeColor}, 0 4px 10px rgba(0,0,0,0.7)`;
  }

  // Find active cue
  const activeCue = cues.find(c => c.start <= currentTime && currentTime <= c.end);
  highlightActiveCueInEditor(activeCue ? activeCue.id : null);

  if (!activeCue) {
    overlayBox.innerHTML = '';
    return;
  }

  // 1. Clean White Tag / Pill Box Preset (from user's image)
  if (stylePreset === 'white_box') {
    const rawText = activeCue.text || '';
    const displayText = allCaps ? rawText.toUpperCase() : rawText;
    const lines = displayText.split('\n').filter(l => l.trim().length > 0);
    const tagBg = opts.outline_color || '#FFFFFF';
    const tagText = opts.primary_color || '#000000';

    overlayBox.innerHTML = `
      <div class="flex flex-col items-center gap-1.5">
        ${lines.map(line => `
          <div class="sub-pill-tag" style="background-color: ${tagBg}; color: ${tagText};">
            ${line}
          </div>
        `).join('')}
      </div>
    `;
    return;
  }

  // 2. Clean Minimal Box Preset (whole phrase without active word highlight)
  if (stylePreset === 'minimal') {
    const rawText = activeCue.text || '';
    const displayText = allCaps ? rawText.toUpperCase() : rawText;
    overlayBox.innerText = displayText;
    return;
  }

  // 3. Animated Presets (Hormozi Pop, Bounce)
  const words = activeCue.words || [];
  if (words.length === 0) {
    overlayBox.innerText = allCaps ? activeCue.text.toUpperCase() : activeCue.text;
    return;
  }

  // Chunk words for viral video rhythm
  const chunkSize = opts.chunk_size || 4;
  let activeChunk = words;
  if (chunkSize > 0 && words.length > chunkSize) {
    for (let i = 0; i < words.length; i += chunkSize) {
      const slice = words.slice(i, i + chunkSize);
      if (slice[0].start <= currentTime && currentTime <= slice[slice.length - 1].end) {
        activeChunk = slice;
        break;
      }
    }
  }

  const spans = activeChunk.map(w => {
    const isActive = (w.start <= currentTime && currentTime <= w.end);
    let wordText = w.word;
    if (allCaps) wordText = wordText.toUpperCase();

    if (isActive) {
      let activeClass = `sub-word sub-word-active-${stylePreset}`;
      return `<span class="${activeClass}" style="color: ${opts.highlight_color || '#FFE600'};">${wordText}</span>`;
    } else {
      return `<span class="sub-word" style="color: ${opts.primary_color || '#FFFFFF'};">${wordText}</span>`;
    }
  });

  overlayBox.innerHTML = spans.join(' ');
}

function highlightActiveCueInEditor(cueId) {
  document.querySelectorAll('.sub-cue-row').forEach(row => {
    if (cueId && row.dataset.cueId == cueId) {
      row.classList.add('active');
    } else {
      row.classList.remove('active');
    }
  });
}

function renderSubtitleCuesList() {
  const container = document.getElementById('sub-cues-list');
  const badge = document.getElementById('sub-cues-badge');
  const cues = (state.activeToolOptions && state.activeToolOptions.subtitles) || [];
  if (badge) badge.innerText = `${cues.length} cue${cues.length === 1 ? '' : 's'}`;
  if (!container) return;

  if (cues.length === 0) {
    container.innerHTML = `
      <div class="text-center p-4 text-[var(--text-muted)] text-xs">
        No subtitle cues loaded. Click "+ Add Cue" or "Reset to Demo Cues" to start.
      </div>
    `;
    return;
  }

  container.innerHTML = cues.map(cue => `
    <div class="sub-cue-row p-2 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-inset)] transition-all space-y-1.5" data-cue-id="${cue.id}">
      <div class="flex items-center justify-between text-[11px]">
        <div class="flex items-center gap-1.5">
          <button data-action="sub-seek-cue" data-cue-start="${cue.start}" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--brand-light)] hover:text-[var(--brand-primary)] text-[var(--text-secondary)] font-semibold tabular-nums transition-colors cursor-pointer border border-[var(--border-subtle)]" title="Click to seek preview">
            ${formatDisplayTime(cue.start)} → ${formatDisplayTime(cue.end)}
          </button>
          <button data-action="sub-nudge-cue" data-cue-id="${cue.id}" data-nudge="-0.1" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] text-[10px] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-pointer" title="Nudge back 0.1s">-0.1s</button>
          <button data-action="sub-nudge-cue" data-cue-id="${cue.id}" data-nudge="0.1" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] text-[10px] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-pointer" title="Nudge forward 0.1s">+0.1s</button>
        </div>
        <button data-action="sub-delete-cue" data-cue-id="${cue.id}" class="text-red-400 hover:text-red-500 text-[11px] p-1 cursor-pointer transition-colors" title="Delete Cue">
          ${getIcon('trash', 'w-3 h-3')}
        </button>
      </div>
      <input 
        type="text" 
        value="${cue.text.replace(/"/g, '&quot;')}" 
        data-action="sub-cue-text-input" data-cue-id="${cue.id}" 
        class="w-full px-2 py-1 text-xs rounded-md bg-[var(--surface-card)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)]"
        placeholder="Edit subtitle text..."
      />
    </div>
  `).join('');
}

function updateSubtitleCueText(cueId, newText) {
  const cue = (state.activeToolOptions.subtitles || []).find(c => c.id === cueId);
  if (!cue) return;
  cue.text = newText;
  const words = newText.split(/\s+/).filter(Boolean);
  const dur = Math.max(0.2, cue.end - cue.start);
  cue.words = words.map((w, idx) => ({
    word: w,
    start: Math.round((cue.start + (idx / words.length) * dur) * 100) / 100,
    end: Math.round((cue.start + ((idx + 1) / words.length) * dur) * 100) / 100
  }));
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

function nudgeCueTime(cueId, delta) {
  const cue = (state.activeToolOptions.subtitles || []).find(c => c.id === cueId);
  if (!cue) return;
  cue.start = Math.max(0, Math.round((cue.start + delta) * 100) / 100);
  cue.end = Math.max(cue.start + 0.2, Math.round((cue.end + delta) * 100) / 100);
  updateSubtitleCueText(cueId, cue.text);
  renderSubtitleCuesList();
}

function deleteSubtitleCue(cueId) {
  state.activeToolOptions.subtitles = (state.activeToolOptions.subtitles || []).filter(c => c.id !== cueId);
  renderSubtitleCuesList();
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

function addSubtitleCue() {
  const cues = state.activeToolOptions.subtitles || [];
  const lastEnd = cues.length > 0 ? cues[cues.length - 1].end : 0.0;
  const newStart = Math.round((lastEnd + 0.2) * 100) / 100;
  const newEnd = Math.round((newStart + 2.0) * 100) / 100;
  const nextId = cues.length > 0 ? Math.max(...cues.map(c => c.id)) + 1 : 1;

  cues.push({
    id: nextId,
    start: newStart,
    end: newEnd,
    text: "NEW SUBTITLE LINE",
    words: [
      { word: "NEW", start: newStart, end: newStart + 0.6 },
      { word: "SUBTITLE", start: newStart + 0.6, end: newStart + 1.3 },
      { word: "LINE", start: newStart + 1.3, end: newEnd }
    ]
  });

  if (newEnd > subPreviewDuration) {
    subPreviewDuration = newEnd + 1.0;
    const scrubber = document.getElementById('sub-video-scrubber');
    if (scrubber) scrubber.max = subPreviewDuration;
  }

  renderSubtitleCuesList();
  seekSubtitlePreview(newStart);
}

function loadDemoSubtitleSample() {
  state.activeToolOptions.subtitles = getSampleSubtitleCues();
  renderSubtitleCuesList();
  seekSubtitlePreview(0.8);
}

function handleSelectSubtitleStyle(presetId) {
  state.activeToolOptions.style = presetId;
  // Apply aesthetic presets
  if (presetId === 'white_box') {
    state.activeToolOptions.primary_color = '#000000';
    state.activeToolOptions.outline_color = '#FFFFFF';
    state.activeToolOptions.font_name = 'Montserrat';
    state.activeToolOptions.all_caps = false;
  } else if (presetId === 'hormozi') {
    state.activeToolOptions.primary_color = '#FFFFFF';
    state.activeToolOptions.highlight_color = '#FFE600';
    state.activeToolOptions.outline_color = '#000000';
    state.activeToolOptions.font_name = 'Montserrat';
    state.activeToolOptions.all_caps = true;
  } else if (presetId === 'bounce') {
    state.activeToolOptions.primary_color = '#FFFFFF';
    state.activeToolOptions.highlight_color = '#00FF66';
    state.activeToolOptions.outline_color = '#000000';
    state.activeToolOptions.font_name = 'Impact';
    state.activeToolOptions.all_caps = true;
  } else if (presetId === 'minimal') {
    state.activeToolOptions.primary_color = '#F8FAFC';
    state.activeToolOptions.outline_color = '#0F172A';
    state.activeToolOptions.font_name = 'Arial';
    state.activeToolOptions.all_caps = false;
  }

  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

window.handleSelectSubtitleFont = function(fontName) {
  state.activeToolOptions.font_name = fontName;
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
};

async function handleBrowseCustomFont() {
  const files = await callBridge('browse_files', ['Font Files (*.ttf;*.otf)']);
  if (files && files.length > 0) {
    const fontPath = files[0];
    const res = await callBridge('get_font_base64', fontPath);
    if (res && res.success) {
      const fontName = res.font_family;
      let styleTag = document.getElementById('custom-font-style');
      if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'custom-font-style';
        document.head.appendChild(styleTag);
      }
      styleTag.textContent = `@font-face { font-family: "${fontName}"; src: url("${res.data_url}") format("truetype"); font-weight: normal; font-style: normal; }`;

      state.activeToolOptions.font_name = fontName;
      state.activeToolOptions.font_path = fontPath;

      const optBox = document.getElementById('studio-options-box');
      if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
      updateSubtitleLiveOverlay(subPreviewCurrentTime);
    }
  }
}

function setSubtitleColor(key, hexVal) {
  state.activeToolOptions[key] = hexVal;
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

function setSubtitleFontSize(size) {
  state.activeToolOptions.font_size = parseInt(size) || 48;
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

function setSubtitlePosition(pos) {
  state.activeToolOptions.position = pos;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

function setSubtitleAllCaps(checked) {
  state.activeToolOptions.all_caps = checked;
  updateSubtitleLiveOverlay(subPreviewCurrentTime);
}

// ── Modals: Command Palette & 2-Tier Uninstall ───────────────────────────────
function openCommandPalette() {
  const modal = document.getElementById('modal-command-palette');
  const input = document.getElementById('cmd-palette-input');
  if (modal && input) {
    modal.classList.remove('hidden');
    input.value = '';
    renderPaletteResults('');
    input.focus();
  }
}

function closeCommandPalette() {
  const modal = document.getElementById('modal-command-palette');
  if (modal) modal.classList.add('hidden');
}

function renderPaletteResults(query) {
  const list = document.getElementById('cmd-palette-list');
  if (!list) return;

  const q = query.toLowerCase().trim();
  const matched = state.tools.filter(t => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q));

  if (matched.length === 0) {
    list.innerHTML = `<div class="p-4 text-xs text-center text-[var(--text-muted)]">No matching tools found.</div>`;
    return;
  }

  list.innerHTML = matched.map((t, idx) => `
    <div data-action="cmd-select-tool" data-tool-id="${escapeAttr(t.id)}" class="p-2.5 rounded-lg hover:bg-[var(--surface-inset)] cursor-pointer flex items-center justify-between transition-colors">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-md flex items-center justify-center bg-[var(--surface-card)] text-[var(--brand-primary)]">
          ${getIcon(t.icon, 'w-3.5 h-3.5')}
        </div>
        <div>
          <span class="text-xs font-semibold text-[var(--text-primary)]">${escapeHtml(t.name)}</span>
          <span class="ml-2 text-[10px] text-[var(--text-muted)]">${escapeHtml(t.category_name)}</span>
        </div>
      </div>
      ${getIcon('chevron-right', 'w-3.5 h-3.5 text-[var(--text-muted)]')}
    </div>
  `).join('');
}

function openUninstallModal(toolId, toolName) {
  const modal = document.getElementById('modal-uninstall');
  const nameLbl = document.getElementById('uninstall-tool-name');
  if (modal && nameLbl) {
    modal.dataset.toolId = toolId;
    nameLbl.innerText = toolName;
    modal.classList.remove('hidden');
  }
}

function closeUninstallModal() {
  const modal = document.getElementById('modal-uninstall');
  if (modal) modal.classList.add('hidden');
}

async function confirmUninstall(purgeData) {
  const modal = document.getElementById('modal-uninstall');
  const toolId = modal?.dataset?.toolId;
  if (!toolId) return;

  await callBridge('uninstall_tool', toolId, purgeData);
  closeUninstallModal();
  // get_initial_data deliberately carries no tool list; the catalog comes only from get_catalog_summary
  const summaryData = await callBridge('get_catalog_summary');
  if (Array.isArray(summaryData)) state.tools = summaryData;
  const container = document.getElementById('main-content');
  if (state.currentView === 'tool_hub' && container) {
    renderToolHub(container);
  } else if (state.currentView === 'home' && container) {
    renderHome(container);
  } else if (state.currentView === 'tool_studio' && state.activeToolId === toolId) {
    navigateTo('tool_hub');
  }
}

// ── Announcements Modal & Notification System ──────────────────────────────
function updateBellBadge(count = null) {
  if (count !== null && count !== undefined) {
    state.unreadAnnouncementsCount = Math.max(0, count);
  }
  const pendingUpdates = state.updatesCount || (state.tools ? state.tools.filter(t => t.update_available || t.status === 'update_available').length : 0);
  const totalAlerts = (state.unreadAnnouncementsCount || 0) + pendingUpdates;
  const dot = document.getElementById('bell-dot');
  if (dot) {
    dot.style.display = totalAlerts > 0 ? 'block' : 'none';
  }
}

function toggleAnnouncementsModal() {
  const modal = document.getElementById('modal-announcements');
  if (!modal) return;
  if (modal.classList.contains('hidden')) {
    openAnnouncementsModal();
  } else {
    closeAnnouncementsModal();
  }
}

function openAnnouncementsModal() {
  const modal = document.getElementById('modal-announcements');
  const list = document.getElementById('announcements-list');
  if (!modal || !list) return;

  const items = state.announcements || [];

  if (items.length === 0) {
    list.innerHTML = `
      <div class="py-10 text-center text-xs text-[var(--text-muted)]">
        <p>No new notifications or announcements.</p>
      </div>
    `;
    modal.classList.remove('hidden');
    return;
  }

  list.innerHTML = items.map(a => `
    <div class="p-3.5 rounded-xl bg-[var(--surface-inset)] border border-[var(--border-subtle)] space-y-1.5">
      <div class="flex items-center justify-between">
        <span class="px-2 py-0.5 text-[9px] font-bold rounded bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${escapeHtml(a.tag || 'UPDATE')}</span>
        <span class="text-[10px] text-[var(--text-muted)]">${escapeHtml(a.date || '')}</span>
      </div>
      <h4 class="text-xs font-semibold text-[var(--text-primary)]">${escapeHtml(a.title)}</h4>
      <p class="text-[11px] text-[var(--text-secondary)] leading-relaxed">${escapeHtml(a.description)}</p>
      ${a.cta_action ? `
        <div class="pt-1">
          <button data-action="announcement-cta" data-cta-action="${escapeAttr(a.cta_action)}" data-cta-target="${escapeAttr(a.cta_target || '')}" class="text-[11px] font-medium text-[var(--brand-primary)] hover:underline inline-flex items-center gap-1 cursor-pointer">
            <span>${escapeHtml(a.cta_text || 'Open in App')}</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
      ` : (a.cta_url ? `
        <div class="pt-1">
          <a href="${escapeAttr(a.cta_url)}" target="_blank" class="text-[11px] font-medium text-[var(--brand-primary)] hover:underline inline-flex items-center gap-1">
            <span>${escapeHtml(a.cta_text || 'Learn more')}</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </a>
        </div>
      ` : '')}
    </div>
  `).join('');

  // Mark all seen
  const seenIds = items.map(i => i.id);
  localStorage.setItem('boltools-seen-announcements', JSON.stringify(seenIds));
  updateBellBadge(0);

  modal.classList.remove('hidden');
}

function closeAnnouncementsModal() {
  const modal = document.getElementById('modal-announcements');
  if (modal) modal.classList.add('hidden');
}

function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(toastContainer);
  }
  const toast = document.createElement('div');
  const bg = type === 'success' ? 'bg-emerald-600 text-white' : (type === 'error' ? 'bg-red-600 text-white' : 'bg-neutral-800 text-white');
  toast.className = `${bg} px-4 py-2.5 rounded-xl shadow-lg text-xs font-medium flex items-center gap-2 pointer-events-auto transition-all duration-300 transform translate-y-2 opacity-0`;
  toast.innerHTML = `
    <span>${getIcon(type === 'success' ? 'check' : 'info', 'w-4 h-4')}</span>
    <span>${escapeHtml(message)}</span>
  `;
  toastContainer.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function handleAnnouncementAction(action, target) {
  closeAnnouncementsModal();
  if (action === 'update_tool' && target) {
    navigateTo('tool_hub');
    handleInstallOrUpdateTool(target, true);
  } else if (action === 'navigate_hub') {
    navigateTo('tool_hub');
  } else if (action === 'open_tool' && target) {
    const tool = state.tools.find(t => t.id === target);
    if (tool && (tool.status === 'update_available' || tool.update_available)) {
      navigateTo('tool_hub');
    } else {
      navigateTo('tool_studio', target);
    }
  } else if (action === 'navigate_category' && target) {
    navigateToCategory(target);
  } else {
    navigateTo('tool_hub');
  }
}

// ── Application Bootstrapper ─────────────────────────────────────────────────
async function initApp() {
  applyTheme(state.theme);

  // Central Delegated Event Dispatcher (Zero inline handlers, Strict CSP compliance)
  document.addEventListener('click', (e) => {
    // 1. Dismiss dropdowns if click is outside
    if (!e.target.closest('.custom-dropdown-container')) {
      closeAllCustomDropdowns();
    }

    // 2. Handle data-action click delegation
    const el = e.target.closest('[data-action]');
    if (!el) return;

    const action = el.dataset.action;

    switch (action) {
      case 'stop-prop':
        e.stopPropagation();
        break;

      case 'nav': {
        const view = el.dataset.view;
        const arg = el.dataset.arg || null;
        if (view) navigateTo(view, arg);
        break;
      }

      case 'nav-category': {
        const cat = el.dataset.cat;
        if (cat) navigateToCategory(cat);
        break;
      }

      case 'open-tool': {
        const tid = el.dataset.toolId;
        const tool = state.tools.find(t => t.id === tid);
        if (tool && tool.status !== 'installed' && !tool.update_available) {
          installTool(tid);
        } else if (tid) {
          navigateTo('tool_studio', tid);
        }
        break;
      }

      case 'open-updates-hub':
        setHubTab('Updates');
        navigateTo('tool_hub');
        break;

      case 'install-tool': {
        e.stopPropagation();
        const tid = el.dataset.toolId;
        if (tid) installTool(tid);
        break;
      }

      case 'update-tool': {
        e.stopPropagation();
        const tid = el.dataset.toolId;
        if (tid) handleInstallOrUpdateTool(tid, true);
        break;
      }

      case 'uninstall-tool': {
        e.stopPropagation();
        const tid = el.dataset.toolId;
        const tname = el.dataset.toolName || '';
        if (tid) openUninstallModal(tid, tname);
        break;
      }

      case 'set-hub-tab': {
        const tab = el.dataset.tab;
        if (tab) setHubTab(tab);
        break;
      }

      case 'toggle-fav': {
        e.stopPropagation();
        const tid = el.dataset.toolId;
        if (tid) handleToggleFavorite(tid, el);
        break;
      }

      case 'set-theme': {
        const theme = el.dataset.theme;
        if (theme) ThemeTransition.switchTo(theme);
        break;
      }

      case 'toggle-theme':
        ThemeTransition.switchTo(state.theme === 'dark' ? 'light' : 'dark');
        break;

      case 'browse-default-folder':
        handleBrowseDefaultFolder();
        break;

      case 'clean-cache':
        handleCleanCache(el);
        break;

      case 'navigate-back':
        if (state.isToolRunning && RunStage.confirmLeave()) break;
        navigateBack();
        break;

      case 'retry-failed': {
        // Load only the files that failed, so the user can fix or remove them and run again.
        const failed = RunStage.failedFiles();
        RunStage.reset();
        state.selectedFiles = failed;
        updateStudioFilesUI();
        if (failed.length && failed.every(f => f.toLowerCase().endsWith('.pdf'))) inspectSelectedPdfFiles(failed);
        break;
      }

      case 'run-stage-keep':
        RunStage.keepRunning();
        break;

      case 'run-stage-stop-back':
        handleCancelTool().then(navigateBack);
        break;

      case 'studio-toggle-fav': {
        const tid = el.dataset.toolId;
        if (tid) handleStudioToggleFavorite(tid, el);
        break;
      }

      case 'studio-browse-files': {
        const tid = el.dataset.toolId;
        if (tid) handleStudioBrowseFiles(tid, false);
        break;
      }

      case 'studio-add-more-files': {
        const tid = el.dataset.toolId || state.activeToolId;
        if (tid) handleStudioBrowseFiles(tid, true);
        break;
      }

      case 'clear-studio-files':
        clearStudioFiles();
        break;

      case 'remove-studio-file': {
        e.stopPropagation();
        const fIdx = parseInt(el.dataset.fileIdx, 10);
        if (!isNaN(fIdx)) removeStudioFile(fIdx);
        break;
      }

      case 'studio-browse-out-folder':
        handleStudioBrowseOutFolder();
        break;

      case 'studio-execute': {
        const tid = el.dataset.toolId;
        if (tid) handleExecuteTool(tid);
        break;
      }

      case 'cancel-tool':
        handleCancelTool();
        break;

      case 'run-stage-reset':
        RunStage.reset();
        break;

      case 'open-output-file':
        handleOpenOutputFile();
        break;

      case 'reveal-output-folder':
        handleRevealOutputFolder();
        break;

      case 'set-studio-mode': {
        const mode = el.dataset.mode;
        if (mode) setStudioMode(mode);
        break;
      }

      case 'move-studio-file-up': {
        e.stopPropagation();
        const fIdx = parseInt(el.dataset.fileIdx, 10);
        if (!isNaN(fIdx)) moveStudioFile(fIdx, -1);
        break;
      }

      case 'move-studio-file-down': {
        e.stopPropagation();
        const fIdx = parseInt(el.dataset.fileIdx, 10);
        if (!isNaN(fIdx)) moveStudioFile(fIdx, 1);
        break;
      }

      case 'set-pdf-mode': {
        const mode = el.dataset.mode;
        if (mode) {
          state.activeToolOptions.mode = mode;
          const optBox = document.getElementById('studio-options-box');
          if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
          const execLbl = document.getElementById('studio-btn-exec-label');
          if (execLbl) {
            execLbl.innerText = mode === 'merge' ? 'Merge Documents' : 'Split Document';
          }
          const fnameInp = document.getElementById('studio-out-filename');
          if (fnameInp && (!fnameInp.value || fnameInp.value === 'merged_document.pdf' || fnameInp.value === 'split_document')) {
            fnameInp.value = mode === 'merge' ? 'merged_document.pdf' : 'split_document';
            state.activeToolOptions.custom_filename = fnameInp.value;
            state.activeToolOptions.output_filename = fnameInp.value;
          }
        }
        break;
      }

      case 'set-pdf-split-mode': {
        const sm = el.dataset.splitMode;
        if (sm) {
          state.activeToolOptions.split_mode = sm;
          const optBox = document.getElementById('studio-options-box');
          if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
          refreshStudioPreview();
        }
        break;
      }

      case 'set-tool-option': {
        const { key, value } = el.dataset;
        if (key) {
          OptionsUI.apply(state.activeToolOptions, key, value);
          const optBox = document.getElementById('studio-options-box');
          if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
          refreshStudioPreview();
        }
        break;
      }

      case 'sub-select-style': {
        const style = el.dataset.style;
        if (style) handleSelectSubtitleStyle(style);
        break;
      }

      case 'sub-browse-font':
        handleBrowseCustomFont();
        break;

      case 'sub-set-position': {
        const pos = el.dataset.pos;
        if (pos) setSubtitlePosition(pos);
        break;
      }

      case 'sub-load-demo':
        loadDemoSubtitleSample();
        break;

      case 'sub-toggle-play':
        toggleSubtitleVideoPlay();
        break;

      case 'sub-add-cue':
        addSubtitleCue();
        break;

      case 'sub-seek-cue': {
        const start = parseFloat(el.dataset.cueStart);
        if (!isNaN(start)) seekSubtitlePreview(start);
        break;
      }

      case 'sub-nudge-cue': {
        const cueId = parseInt(el.dataset.cueId, 10);
        const delta = parseFloat(el.dataset.nudge);
        if (!isNaN(cueId) && !isNaN(delta)) nudgeCueTime(cueId, delta);
        break;
      }

      case 'sub-delete-cue': {
        const cueId = parseInt(el.dataset.cueId, 10);
        if (!isNaN(cueId)) deleteSubtitleCue(cueId);
        break;
      }

      case 'toggle-dropdown': {
        const id = el.dataset.ddId;
        if (id) toggleCustomDropdown(id, e);
        break;
      }

      case 'select-dropdown-option': {
        const id = el.dataset.ddId;
        const val = el.dataset.ddVal;
        const lbl = el.dataset.ddLbl;
        const cb = el.dataset.ddCallback;
        if (id) selectCustomDropdownOption(id, val, lbl, cb);
        break;
      }

      case 'open-cmd-palette':
        openCommandPalette();
        break;

      case 'close-cmd':
      case 'close-cmd-backdrop':
        closeCommandPalette();
        break;

      case 'cmd-select-tool': {
        const tid = el.dataset.toolId;
        closeCommandPalette();
        if (tid) navigateTo('tool_studio', tid);
        break;
      }

      case 'toggle-announcements':
        openAnnouncementsModal();
        break;

      case 'close-announcements':
      case 'close-announcements-backdrop':
        closeAnnouncementsModal();
        break;

      case 'announcement-cta': {
        const ctaAction = el.dataset.ctaAction;
        const ctaTarget = el.dataset.ctaTarget;
        handleAnnouncementAction(ctaAction, ctaTarget);
        break;
      }

      case 'close-uninstall':
      case 'close-uninstall-backdrop':
        closeUninstallModal();
        break;

      case 'confirm-uninstall': {
        const purge = el.dataset.purge === 'true';
        confirmUninstall(purge);
        break;
      }

      case 'home-browse-files':
        handleHomeBrowseFiles();
        break;

      case 'smart-action-merge':
        openPdfStudioWithFiles(pendingGlobalFiles, 'merge');
        break;

      case 'smart-action-split':
        openPdfStudioWithFiles(pendingGlobalFiles, 'split');
        break;

      case 'close-file-action':
      case 'close-file-action-backdrop': {
        const modal = document.getElementById('modal-file-action');
        if (modal) modal.classList.add('hidden');
        break;
      }

      case 'open-file': {
        e.stopPropagation();
        const p = el.dataset.filePath;
        if (p) callBridge('open_file', p);
        break;
      }

      case 'reveal-file': {
        e.stopPropagation();
        const p = el.dataset.filePath;
        if (p) callBridge('reveal_file', p);
        break;
      }

      case 'clear-recent-files': {
        e.stopPropagation();
        state.recentFiles = [];
        localStorage.removeItem('boltools-recent-files');
        const c = document.getElementById('main-content');
        if (state.currentView === 'home' && c) renderHome(c);
        else if (state.currentView === 'history' && c) renderHistory(c);
        break;
      }

      case 'clear-recent-tools': {
        e.stopPropagation();
        state.recentTools = [];
        localStorage.removeItem('boltools-recent-tools');
        const c = document.getElementById('main-content');
        if (state.currentView === 'home' && c) renderHome(c);
        break;
      }

      case 'open-url': {
        e.stopPropagation();
        e.preventDefault();
        const targetUrl = el.dataset.url || el.getAttribute('href');
        if (targetUrl) {
          if (window.boltoolsBridge) {
            callBridge('open_url', targetUrl);
          } else {
            window.open(targetUrl, '_blank');
          }
        }
        break;
      }

      default:
        break;
    }
  });

  // Delegated Input Dispatcher
  document.addEventListener('input', (e) => {
    const el = e.target.closest('[data-action]');
    if (!el) return;

    const action = el.dataset.action;
    switch (action) {
      case 'cmd-palette-input':
        renderPaletteResults(el.value);
        break;

      case 'hub-search-input':
        handleHubSearch(el.value);
        break;

      case 'studio-out-folder-input':
        state.customOutputDir = el.value;
        break;

      case 'studio-out-filename-input':
        state.activeToolOptions.custom_filename = el.value.trim();
        state.activeToolOptions.output_filename = el.value.trim();
        break;


      case 'renamer-text-input':
        state.activeToolOptions.text1 = el.value;
        refreshStudioPreview();
        break;

      case 'renamer-text2-input':
        state.activeToolOptions.text2 = el.value;
        refreshStudioPreview();
        break;

      case 'pdf-ranges-input':
        state.activeToolOptions.ranges = el.value;
        refreshStudioPreview();
        break;

      case 'pdf-every-n-input': {
        const val = parseInt(el.value, 10);
        state.activeToolOptions.every_n = isNaN(val) || val < 1 ? 1 : val;
        refreshStudioPreview();
        break;
      }

      case 'sub-scrubber-input':
        handleSubtitleScrub(el.value);
        break;

      case 'sub-fontsize-input': {
        const lbl = document.getElementById('sub-fontsize-val');
        if (lbl) lbl.innerText = el.value + 'px';
        setSubtitleFontSize(el.value);
        break;
      }

      case 'sub-cue-text-input': {
        const cueId = parseInt(el.dataset.cueId, 10);
        if (!isNaN(cueId)) updateSubtitleCueText(cueId, el.value);
        break;
      }

      default:
        break;
    }
  });

  // Delegated Change Dispatcher
  document.addEventListener('change', (e) => {
    const el = e.target.closest('[data-action]');
    if (!el) return;

    const action = el.dataset.action;
    switch (action) {
      case 'sub-color-change': {
        const prop = el.dataset.colorProp;
        if (prop) setSubtitleColor(prop, el.value);
        break;
      }

      case 'sub-all-caps-change':
        setSubtitleAllCaps(el.checked);
        break;

      default:
        break;
    }
  });

  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openCommandPalette();
    }
    handleStudioShortcut(e);
    if (e.key === 'Escape') {
      closeCommandPalette();
      closeUninstallModal();
      closeAnnouncementsModal();
      closeAllCustomDropdowns();
    }
  });

  function updateSidebarCategoryCounts() {
    let catSection = document.getElementById('sidebar-categories-section');
    if (!catSection) {
      const nav = document.querySelector('aside nav');
      if (nav && nav.parentNode) {
        catSection = document.createElement('div');
        catSection.id = 'sidebar-categories-section';
        catSection.className = 'pt-3 border-t border-[var(--border-subtle)] space-y-1';
        nav.parentNode.insertBefore(catSection, nav.nextElementSibling);
      }
    }

    if (catSection && (!catSection.querySelector('.sidebar-cat-btn') || catSection.children.length <= 1)) {
      catSection.innerHTML = `
        <span class="px-2 text-[10px] font-semibold text-[var(--text-muted)] tracking-wider uppercase">Categories</span>
        <button data-action="nav-category" data-cat="pdf" class="sidebar-cat-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-card-hover)] transition-all cursor-pointer group">
          <div class="flex items-center gap-2.5">
            <svg class="w-3.5 h-3.5 text-red-500 shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
            <span>PDF Studio</span>
          </div>
          <span id="cat-count-pdf" class="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-500 font-mono">2</span>
        </button>

        <button data-action="nav-category" data-cat="video" class="sidebar-cat-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-card-hover)] transition-all cursor-pointer group">
          <div class="flex items-center gap-2.5">
            <svg class="w-3.5 h-3.5 text-blue-500 shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2"/></svg>
            <span>Media & Video</span>
          </div>
          <span id="cat-count-video" class="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-mono">3</span>
        </button>

        <button data-action="nav-category" data-cat="image" class="sidebar-cat-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-card-hover)] transition-all cursor-pointer group">
          <div class="flex items-center gap-2.5">
            <svg class="w-3.5 h-3.5 text-emerald-500 shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
            <span>Image Studio</span>
          </div>
          <span id="cat-count-image" class="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-mono">1</span>
        </button>

        <button data-action="nav-category" data-cat="system" class="sidebar-cat-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-card-hover)] transition-all cursor-pointer group">
          <div class="flex items-center gap-2.5">
            <svg class="w-3.5 h-3.5 text-amber-500 shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/></svg>
            <span>System & Files</span>
          </div>
          <span id="cat-count-system" class="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-mono">1</span>
        </button>
      `;
    }

    const counts = {
      pdf: state.tools.filter(t => t.category_id === 'pdf').length,
      video: state.tools.filter(t => t.category_id === 'video').length,
      image: state.tools.filter(t => t.category_id === 'image').length,
      system: state.tools.filter(t => t.category_id === 'system').length,
    };
    Object.keys(counts).forEach(catId => {
      const el = document.getElementById(`cat-count-${catId}`);
      if (el && counts[catId] !== undefined && counts[catId] > 0) {
        el.innerText = counts[catId];
      }
    });

    if (state.activeCategoryId) {
      document.querySelectorAll('.sidebar-cat-btn').forEach(btn => {
        if (btn.dataset.cat === state.activeCategoryId) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }
  }

  // Render initial view immediately with guaranteed defaults (0ms UI latency)
  navigateTo('home', null, false);
  updateSidebarCategoryCounts();

  // Background bridge synchronization loop
  async function syncBridgeData() {
    let attempts = 0;
    while (attempts < 40) {
      const initData = await callBridge('get_initial_data');
      if (initData) {
        if (initData.categories && initData.categories.length) state.categories = initData.categories;
        if (initData.favorites) state.favorites = initData.favorites;
        if (initData.announcements && initData.announcements.length) state.announcements = initData.announcements;
        if (initData.updates_count !== undefined) state.updatesCount = initData.updates_count;
        if (initData.system_stats) state.systemStats = initData.system_stats;
        if (initData.default_downloads) state.defaultDownloads = initData.default_downloads;

        // Fetch compact catalog summaries via get_catalog_summary
        const summaryData = await callBridge('get_catalog_summary');
        if (Array.isArray(summaryData)) {
          state.tools = summaryData;
          updateSidebarCategoryCounts();
        }

        // Check unread announcements and pending updates
        const seenIds = JSON.parse(localStorage.getItem('boltools-seen-announcements') || '[]');
        const unread = (state.announcements || []).filter(a => !seenIds.includes(a.id)).length;
        updateBellBadge(unread > 0 ? unread : 0);

        // Re-render to reflect synced state
        const container = document.getElementById('main-content');
        if (container) {
          if (state.currentView === 'home') renderHome(container);
          else if (state.currentView === 'tool_hub') renderToolHub(container);
          else if (state.currentView === 'favorites') renderFavorites(container);
        }
        OpenRequest.takeInitial();
        break;
      }
      attempts++;
      await new Promise(r => setTimeout(r, 100));
    }
  }
  syncBridgeData();

  // Start system monitor ticker (5s interval, only while Home & document are visible)
  let sysPollTimer = null;

  async function pollSystemStats() {
    if (document.hidden || state.currentView !== 'home') return;
    const stats = await callBridge('get_system_stats');
    if (stats) {
      const cpu = document.getElementById('mon-cpu-fill');
      const ram = document.getElementById('mon-ram-fill');
      const disk = document.getElementById('mon-disk-fill');
      if (cpu) cpu.style.width = `${stats.cpu}%`;
      if (ram) ram.style.width = `${stats.ram}%`;
      if (disk) disk.style.width = `${stats.disk}%`;
    }
  }

  function startSystemPolling() {
    if (sysPollTimer) clearInterval(sysPollTimer);
    sysPollTimer = setInterval(pollSystemStats, 5000);
  }

  function stopSystemPolling() {
    if (sysPollTimer) {
      clearInterval(sysPollTimer);
      sysPollTimer = null;
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopSystemPolling();
    } else {
      if (state.currentView === 'home') pollSystemStats();
      startSystemPolling();
    }
  });

  startSystemPolling();
}

// ── Single Deterministic Bootstrap from Bridge Ready Promise ───────────────
let appInitialized = false;

async function bootstrapApp() {
  if (appInitialized) return;
  appInitialized = true;
  await initApp();
}

if (window.boltoolsBridge) {
  window.boltoolsBridge.ready.then(() => {
    bootstrapApp();
  });
} else {
  window.addEventListener('pywebviewready', bootstrapApp);
}

// Export for tests, modules, and debugging
window.state = state;
window.navigateTo = navigateTo;
window.getActiveSearchIndex = () => activeSearchIndex;
