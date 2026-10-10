/**
 * Boltools Desktop Client Application Controller (Option 1 Architecture)
 * 100% Offline, Pixel-Perfect Linear / Apple Standard
 */

// ── Default Fallback Categories & Tools (Immediate 0ms Offline Render) ────────
const DEFAULT_CATEGORIES = [
  { id: "video", name: "Media & Video", desc: "Fast offline video compression, extraction, and formatting", icon: "video", accent: "#2563EB" },
  { id: "pdf", name: "PDF Studio", desc: "Offline conversion, splitting, merging, and document protection", icon: "file-text", accent: "#DC2626" },
  { id: "image", name: "Image Studio", desc: "Batch WebP compression, target sizing, and format switching", icon: "image", accent: "#059669" },
  { id: "system", name: "System & Files", desc: "Power file renaming, extension repair, and organization", icon: "sliders", accent: "#475569" }
];

const DEFAULT_TOOLS = [
  {
    id: "media_audio_extractor",
    name: "Audio Extractor",
    category_id: "video",
    category_name: "Media & Video",
    description: "Extract clean MP3, WAV, AAC, or FLAC audio tracks from video and audio files locally.",
    icon: "music",
    is_implemented: true,
    status: "installed"
  },
  {
    id: "video_compressor",
    name: "Video Compressor",
    category_id: "video",
    category_name: "Media & Video",
    description: "Compress video files with Low, Balanced, and Maximum compression presets.",
    icon: "video",
    is_implemented: true,
    status: "installed"
  },
  {
    id: "pdf_converter",
    name: "PDF & Image Converter",
    category_id: "pdf",
    category_name: "PDF Studio",
    description: "Convert PDF pages to high-resolution PNG/JPG images or compile multiple images into a PDF.",
    icon: "file-text",
    is_implemented: true,
    status: "installed"
  },
  {
    id: "image_webp_compress",
    name: "WebP Image Compressor",
    category_id: "image",
    category_name: "Image Studio",
    description: "Bulk compress photos into web-optimized WebP images with custom quality controls.",
    icon: "image",
    is_implemented: true,
    status: "installed"
  },
  {
    id: "system_batch_rename",
    name: "Bulk File Renamer",
    category_id: "system",
    category_name: "System & Files",
    description: "Batch rename files with rule-based prefix, suffix, sequence numbering, and find-and-replace.",
    icon: "sliders",
    is_implemented: true,
    status: "installed"
  },
  {
    id: "subtitle_animator",
    name: "Subtitle Animation Maker",
    category_id: "video",
    category_name: "Media & Video",
    description: "Create viral animated subtitles with word-by-word karaoke highlight, custom fonts, colors, and live timing editor.",
    icon: "type",
    is_implemented: true,
    status: "installed"
  }
];

// ── Application State ────────────────────────────────────────────────────────
const state = {
  theme: localStorage.getItem('boltools-theme') || 'light',
  currentView: 'home',
  activeToolId: null,
  navHistory: [{ view: 'home', toolId: null }],
  categories: DEFAULT_CATEGORIES,
  tools: DEFAULT_TOOLS,
  favorites: [],
  recentTools: JSON.parse(localStorage.getItem('boltools-recent-tools') || '[]'),
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

// ── Bridge Communication Helpers ─────────────────────────────────────────────
async function callBridge(fnName, ...args) {
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api[fnName] === 'function') {
    return await window.pywebview.api[fnName](...args);
  }
  console.warn(`Bridge function ${fnName} not available in mock/browser mode.`);
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

  if (viewName === 'home') {
    renderHome(container);
    updateBreadcrumb(['Home']);
  } else if (viewName === 'tool_hub') {
    renderToolHub(container);
    updateBreadcrumb(['Home', 'Tool Hub']);
  } else if (viewName === 'favorites') {
    renderFavorites(container);
    updateBreadcrumb(['Home', 'Favorites']);
  } else if (viewName === 'settings') {
    renderSettings(container);
    updateBreadcrumb(['Home', 'Settings']);
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
      let onclickStr = "navigateTo('home')";
      if (crumb === 'Home') {
        onclickStr = "navigateTo('home')";
      } else if (crumb === 'Tool Hub') {
        onclickStr = "navigateTo('tool_hub')";
      } else if (crumb === 'Favorites') {
        onclickStr = "navigateTo('favorites')";
      } else if (crumb === 'Settings') {
        onclickStr = "navigateTo('settings')";
      } else {
        const cat = state.categories.find(c => c.name.toLowerCase() === crumb.toLowerCase());
        if (cat) {
          onclickStr = `navigateToCategory('${cat.id}')`;
        }
      }
      html += `<button onclick="${onclickStr}" class="text-xs font-medium text-[var(--brand-primary)] hover:underline cursor-pointer">${crumb}</button>`;
    }
  });

  bc.innerHTML = html;
}

// ── View Renderers ───────────────────────────────────────────────────────────

// 1. Home Dashboard View
function renderHome(container) {
  const readyTools = state.tools.filter(t => t.status === 'installed' || t.status === 'update_available' || t.update_available);
  const updatesCount = state.updatesCount || state.tools.filter(t => t.update_available || t.status === 'update_available').length;

  // Compute Last Used 3 Utilities
  let recentList = (state.recentTools || [])
    .map(id => state.tools.find(t => t.id === id && (t.status === 'installed' || t.status === 'update_available')))
    .filter(Boolean);

  if (recentList.length === 0) {
    // Default to first 3 installed tools if none recorded yet
    recentList = readyTools.slice(0, 3);
  } else {
    recentList = recentList.slice(0, 3);
  }

  const recentRows = recentList.length > 0 ? recentList.map(t => {
    const isUpdate = t.update_available || t.status === 'update_available';
    return `
      <div onclick="navigateTo('tool_studio', '${t.id}')" class="group p-3 px-4 rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border ${isUpdate ? 'border-amber-500/30' : 'border-[var(--border-subtle)]'} hover:border-[var(--brand-primary)] cursor-pointer transition-all flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] shrink-0 group-hover:scale-105 transition-transform">
            ${getIcon(t.icon, 'w-4 h-4')}
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors truncate">${t.name}</span>
              <span class="px-2 py-0.5 text-[9px] font-medium rounded-full bg-[var(--surface-pill)] text-[var(--text-secondary)] uppercase tracking-wider">${t.category_name}</span>
              ${isUpdate ? `<span class="px-1.5 py-0.2 text-[8px] font-bold rounded bg-amber-500/10 text-amber-500">UPDATE</span>` : ''}
            </div>
            <p class="text-[11px] text-[var(--text-secondary)] truncate mt-0.5">${t.description}</p>
          </div>
        </div>
        <button class="shrink-0 px-2.5 py-1 text-[11px] font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--brand-primary)] hover:text-white border border-[var(--border-subtle)] text-[var(--text-primary)] transition-all flex items-center gap-1.5 shadow-xs">
          <span>Launch</span>
          ${getIcon('arrow-right', 'w-3 h-3')}
        </button>
      </div>
    `;
  }).join('') : `
    <div class="p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center text-xs text-[var(--text-muted)]">
      No recently used utilities yet. Launch any tool below to see it here!
    </div>
  `;

  // Bento Box Squared Cards for Available Utilities
  const bentoGrid = readyTools.length > 0 ? readyTools.map(t => {
    const isUpdate = t.update_available || t.status === 'update_available';
    return `
      <div onclick="navigateTo('tool_studio', '${t.id}')" class="group p-5 rounded-2xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border ${isUpdate ? 'border-amber-500/40' : 'border-[var(--border-subtle)]'} hover:border-[var(--brand-primary)] cursor-pointer transition-all duration-200 flex flex-col justify-between hover:shadow-md relative overflow-hidden min-h-[180px]">
        ${isUpdate ? `
          <div class="absolute top-0 right-0 bg-amber-500 text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg tracking-wider uppercase flex items-center gap-1">
            ${getIcon('refresh-cw', 'w-2.5 h-2.5')} Update v${t.remote_version || t.version}
          </div>
        ` : ''}
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform shadow-xs">
              ${getIcon(t.icon, 'w-5 h-5')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--text-secondary)] uppercase tracking-wider">${t.category_name}</span>
          </div>
          <h4 class="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors line-clamp-1">${t.name}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1.5 line-clamp-2 leading-relaxed">${t.description}</p>
        </div>
        <div class="pt-4 mt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
          <span class="text-xs font-semibold ${isUpdate ? 'text-amber-500' : 'text-[var(--brand-primary)]'} group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
            <span>${isUpdate ? 'Update or Open' : 'Open Tool'}</span>
            ${getIcon('arrow-right', 'w-3 h-3')}
          </span>
        </div>
      </div>
    `;
  }).join('') : `
    <div class="col-span-full p-8 rounded-2xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center">
      <p class="text-xs text-[var(--text-secondary)] mb-2">No utilities currently installed on this PC.</p>
      <button onclick="navigateTo('tool_hub')" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white inline-flex items-center gap-1.5">
        <span>Browse Tool Hub</span>
        ${getIcon('arrow-right', 'w-3 h-3')}
      </button>
    </div>
  `;

  const updateBanner = (updatesCount > 0) ? `
    <div class="p-3.5 px-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 shadow-xs">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0">
          ${getIcon('refresh-cw', 'w-4 h-4')}
        </div>
        <div>
          <span class="text-xs font-bold text-amber-700 dark:text-amber-400">Updates Available for ${updatesCount} Tool${updatesCount > 1 ? 's' : ''}</span>
          <p class="text-[11px] text-[var(--text-secondary)] mt-0.5">Engine enhancements and bug fixes are ready. Update in 1 click without re-downloading software.</p>
        </div>
      </div>
      <button onclick="setHubTab('Updates'); navigateTo('tool_hub');" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-all shrink-0 cursor-pointer shadow-sm">
        Review & Update
      </button>
    </div>
  ` : '';

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-7 pb-10">
      <!-- Hero -->
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Utility Suite</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">High-speed, 100% private tools for creator workflows and local power operations.</p>
      </div>

      ${updateBanner}

      <!-- Recent Utilities -->
      <div>
        <div class="flex items-center justify-between mb-2.5">
          <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Recent Utilities</span>
          <button onclick="navigateTo('tool_hub')" class="text-xs font-medium text-[var(--brand-primary)] hover:underline flex items-center gap-1">
            <span>Browse All</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
        <div class="space-y-2">
          ${recentRows}
        </div>
      </div>

      <!-- Available Utilities Bento Grid -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Available Utilities</span>
          <span class="text-xs text-[var(--text-muted)]">${readyTools.length} Utilities</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          ${bentoGrid}
        </div>
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

  const toolCardsHtml = catTools.length > 0 ? catTools.map(t => {
    const isInstalled = t.status === 'installed';
    return `
      <div onclick="navigateTo('tool_studio', '${t.id}')" class="group p-5 rounded-2xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer transition-all duration-200 flex flex-col justify-between hover:shadow-md relative overflow-hidden min-h-[180px]">
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--surface-inset)] group-hover:scale-105 transition-transform shadow-xs" style="color: ${cat.accent};">
              ${getIcon(t.icon, 'w-5 h-5')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full ${isInstalled ? 'bg-emerald-500/10 text-emerald-500' : 'bg-[var(--surface-pill)] text-[var(--text-muted)]'}">
              ${isInstalled ? 'Ready' : 'Available'}
            </span>
          </div>
          <h4 class="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors line-clamp-1">${t.name}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1.5 line-clamp-2 leading-relaxed">${t.description}</p>
        </div>
        <div class="pt-4 mt-3 border-t border-[var(--border-subtle)] flex items-center justify-between gap-2">
          <span class="text-xs font-semibold text-[var(--brand-primary)] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
            <span>Open Tool</span>
            ${getIcon('arrow-right', 'w-3 h-3')}
          </span>
          ${isInstalled ? `
            <button onclick="event.stopPropagation(); openUninstallModal('${t.id}', '${t.name}')" class="px-2 py-1 text-[11px] font-normal rounded-md text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors">
              Uninstall
            </button>
          ` : `
            <button onclick="event.stopPropagation(); installTool('${t.id}')" class="px-2.5 py-1 text-[11px] font-medium rounded-md bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-hover)] transition-all">
              Install
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
          <button onclick="navigateTo('tool_hub')" class="text-xs text-[var(--brand-primary)] hover:underline flex items-center gap-1">
            <span>View All Tools</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          ${toolCardsHtml}
        </div>
      </div>
    </div>
  `;
}

// 2. Tool Hub & Catalog View
function renderToolHub(container) {
  const filterTab = state.hubFilterTab || 'All';
  const query = state.searchQuery.toLowerCase().trim();
  const updatesCount = state.updatesCount || state.tools.filter(t => t.update_available || t.status === 'update_available').length;

  let filtered = state.tools.filter(t => {
    const isUpdate = t.update_available || t.status === 'update_available';
    const isInstalled = t.status === 'installed' || isUpdate;

    if (filterTab === 'Installed' && !isInstalled) return false;
    if (filterTab === 'Updates' && !isUpdate) return false;
    if ((filterTab === 'Hub Catalog' || filterTab === 'Catalog') && isInstalled) return false;

    if (query) {
      const match = t.name.toLowerCase().includes(query) ||
                    t.description.toLowerCase().includes(query) ||
                    t.category_name.toLowerCase().includes(query);
      if (!match) return false;
    }
    return true;
  });

  const cardsHtml = filtered.map(t => {
    const isUpdate = t.update_available || t.status === 'update_available';
    const isInstalled = t.status === 'installed' || isUpdate;
    const installedVer = t.installed_version || (t.status === 'installed' ? (t.version || '1.0.0') : null);
    const remoteVer = t.remote_version || t.version || '1.0.0';

    return `
      <div class="p-4 rounded-xl bg-[var(--surface-card)] border ${isUpdate ? 'border-amber-500/40 shadow-sm' : 'border-[var(--border-subtle)]'} hover:border-[var(--border-hover)] transition-all flex flex-col justify-between relative overflow-hidden">
        ${isUpdate ? `
          <div class="absolute top-0 right-0 bg-amber-500 text-white text-[9px] font-bold px-2.5 py-0.5 rounded-bl-lg tracking-wider uppercase flex items-center gap-1 shadow-xs">
            ${getIcon('refresh-cw', 'w-2.5 h-2.5')} Update Available
          </div>
        ` : ''}
        <div>
          <div class="flex items-center gap-2.5 mb-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
              ${getIcon(t.icon, 'w-4 h-4')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${t.category_name}</span>
            <span class="text-[10px] font-mono text-[var(--text-muted)]">v${installedVer || remoteVer}</span>
          </div>
          <h4 class="text-sm font-semibold text-[var(--text-primary)]">${t.name}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">${t.description}</p>
          ${isUpdate && t.release_notes ? `
            <div class="mt-2.5 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-700 dark:text-amber-400">
              <span class="font-semibold">What's New in v${remoteVer}:</span> ${t.release_notes}
            </div>
          ` : ''}
        </div>
        <div class="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between gap-2">
          ${isUpdate ? `
            <div class="flex items-center gap-2 w-full justify-between">
              <button id="btn-action-${t.id}" onclick="handleInstallOrUpdateTool('${t.id}', true)" class="btn-primary px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">
                ${getIcon('download', 'w-3.5 h-3.5')}
                <span>Update Tool (v${remoteVer})</span>
              </button>
              <button onclick="navigateTo('tool_studio', '${t.id}')" class="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-inset)] transition-colors cursor-pointer">
                <span>Launch (v${installedVer || '1.0.0'})</span>
              </button>
            </div>
          ` : (isInstalled ? `
            <button onclick="navigateTo('tool_studio', '${t.id}')" class="btn-primary px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">
              <span>Open Tool</span>
              ${getIcon('arrow-right', 'w-3 h-3')}
            </button>
            <button onclick="openUninstallModal('${t.id}', '${t.name}')" class="px-2.5 py-1.5 text-xs font-normal rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer">
              Uninstall
            </button>
          ` : `
            <button id="btn-action-${t.id}" onclick="handleInstallOrUpdateTool('${t.id}', false)" class="btn-primary px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">
              ${getIcon('download', 'w-3.5 h-3.5')}
              <span>+ Install (Free)</span>
            </button>
          `)}
        </div>
      </div>
    `;
  }).join('');

  const hubTabs = [
    { id: 'All', label: 'All' },
    { id: 'Installed', label: 'Installed' },
    { id: 'Updates', label: updatesCount > 0 ? `Updates (${updatesCount})` : 'Updates', badge: updatesCount > 0 },
    { id: 'Hub Catalog', label: 'Hub Catalog' }
  ];

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Tool Hub</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Browse, install, and update modular offline tools directly on this PC.</p>
      </div>

      <!-- Filter Tabs & Search Bar -->
      <div class="p-2 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex flex-col sm:flex-row items-center gap-3">
        <!-- Segmented Tabs -->
        <div class="flex items-center gap-1 p-1 bg-[var(--surface-inset)] rounded-lg shrink-0 overflow-x-auto max-w-full">
          ${hubTabs.map(tab => `
            <button onclick="setHubTab('${tab.id}')" class="px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 cursor-pointer ${filterTab === tab.id ? 'bg-[var(--surface-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}">
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
            oninput="handleHubSearch(this.value)"
            class="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--brand-primary)]"
          />
        </div>
      </div>

      <!-- Tools Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        ${cardsHtml.length > 0 ? cardsHtml : `
          <div class="col-span-2 p-8 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center">
            <p class="text-xs text-[var(--text-muted)]">No utilities match your filter query.</p>
          </div>
        `}
      </div>
    </div>
  `;
}

function setHubTab(tabName) {
  state.hubFilterTab = tabName;
  const container = document.getElementById('main-content');
  if (container) renderToolHub(container);
}

function handleHubSearch(val) {
  state.searchQuery = val;
  const container = document.getElementById('main-content');
  if (container) renderToolHub(container);
}

async function handleInstallOrUpdateTool(toolId, isUpdate = false) {
  const btn = document.getElementById(`btn-action-${toolId}`);
  if (btn) {
    btn.disabled = true;
    btn.style.opacity = '0.7';
    btn.innerHTML = `<span class="inline-block animate-spin mr-1.5">⏳</span><span>${isUpdate ? 'Updating Engine...' : 'Installing Engine...'}</span>`;
  }

  try {
    const res = await callBridge('install_or_update_tool', toolId);
    if (res && res.success) {
      const data = await callBridge('get_initial_data');
      if (data) {
        state.tools = data.tools;
        state.updatesCount = data.updates_count || 0;
        updateBellBadge();
      }
      showToast(res.message || `${toolId} updated successfully!`, 'success');
      const container = document.getElementById('main-content');
      if (container) {
        if (state.currentView === 'tool_hub') renderToolHub(container);
        else if (state.currentView === 'home') renderHome(container);
        else if (state.currentView === 'category_view') renderCategoryView(container, state.activeCategoryId);
      }
    } else {
      alert((res && res.error) || 'Failed to download tool engine.');
      if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.innerHTML = `<span>Retry</span>`;
      }
    }
  } catch (err) {
    console.error('Error in handleInstallOrUpdateTool:', err);
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
        <button onclick="navigateTo('tool_hub')" class="btn-primary px-4 py-2 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all inline-flex items-center gap-1.5">
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
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${t.category_name}</span>
          </div>
          <button onclick="handleToggleFavorite('${t.id}')" class="text-red-500 hover:scale-110 transition-transform">
            ${getIcon('heartFilled', 'w-4 h-4')}
          </button>
        </div>
        <h4 class="text-sm font-semibold text-[var(--text-primary)]">${t.name}</h4>
        <p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">${t.description}</p>
      </div>
      <div class="mt-4 pt-3 border-t border-[var(--border-subtle)]">
        <button onclick="navigateTo('tool_studio', '${t.id}')" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm">
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

async function handleToggleFavorite(toolId) {
  const updated = await callBridge('toggle_favorite', toolId);
  if (updated) state.favorites = updated;
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
              <button onclick="applyTheme('${m}')" class="px-3 py-1 text-xs font-medium rounded-md capitalize transition-all ${state.theme === m ? 'bg-[var(--surface-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}">
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
            <button onclick="handleBrowseDefaultFolder()" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors">
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
          <button onclick="handleCleanCache(this)" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">
            Clean Cache
          </button>
        </div>
      </div>

      <!-- About -->
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">About</span>
        <h4 class="text-sm font-semibold text-[var(--text-primary)]">Boltools Desktop v1.0</h4>
        <p class="text-xs text-[var(--text-secondary)] leading-relaxed">Fast, private, 100% offline utilities for creators and power users. Designed and built with obsessed human craftsmanship.</p>
        <div class="pt-2">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium bg-[var(--surface-inset)] text-[var(--text-muted)]">
            ${getIcon('shield', 'w-3 h-3 text-emerald-500')}
            <span>100% Local PC Engine • Zero Cloud Telemetry</span>
          </span>
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
    <div class="max-w-6xl mx-auto space-y-5 pb-8 h-full flex flex-col">
      <!-- Studio Header Bar -->
      <div class="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)] shrink-0">
        <div class="flex items-center gap-3">
          <button onclick="navigateBack()" class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">
            ${getIcon('arrow-left', 'w-4 h-4')}
          </button>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
            ${getIcon(tool.icon, 'w-5 h-5')}
          </div>
          <div>
            <h3 class="text-base font-bold font-display text-[var(--text-primary)]">${tool.name}</h3>
            <p class="text-xs text-[var(--text-secondary)] line-clamp-1">${tool.description}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="handleStudioToggleFavorite('${tool.id}', this)" class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-secondary)] transition-colors">
            ${isFav ? getIcon('heartFilled', 'w-4 h-4') : getIcon('heart', 'w-4 h-4')}
          </button>
        </div>
      </div>

      <!-- Studio 2-Pane Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 items-start min-h-0">
        <!-- Left Pane: Controls & Inputs (${tool.id === 'subtitle_animator' ? '6 Cols' : '7 Cols'}) -->
        <div class="${tool.id === 'subtitle_animator' ? 'lg:col-span-6' : 'lg:col-span-7'} space-y-4 overflow-y-auto max-h-[calc(100vh-160px)] pr-1">
          <!-- Dropzone -->
          <div 
            id="studio-dropzone" 
            onclick="handleStudioBrowseFiles('${tool.id}')"
            class="p-7 rounded-xl bg-[var(--surface-card)] border-2 border-dashed border-[var(--border-subtle)] hover:border-[var(--brand-primary)] cursor-pointer text-center transition-all group"
          >
            <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform mb-3">
              ${getIcon('upload-cloud', 'w-6 h-6')}
            </div>
            <h4 class="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">Click to browse or drop files here</h4>
            <p class="text-xs text-[var(--text-secondary)] mt-1">${getDropzoneHint(tool.id)}</p>
          </div>

          <!-- Loaded Files Chips -->
          <div id="studio-files-wrap" class="hidden space-y-2 p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)]">
            <div class="flex items-center justify-between text-xs">
              <span id="studio-files-count" class="font-semibold text-[var(--text-primary)]">0 files selected</span>
              <button onclick="clearStudioFiles()" class="text-red-500 hover:underline">Clear all</button>
            </div>
            <div id="studio-files-list" class="space-y-1.5 max-h-36 overflow-y-auto"></div>
          </div>

          <!-- Tool Options Builder -->
          <div id="studio-options-box" class="p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-4">
            ${renderToolSpecificOptions(tool.id)}
          </div>

          <!-- Destination Folder Picker -->
          <div class="p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-1.5">
            <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Save Destination</span>
            <div class="flex items-center gap-2">
              <input type="text" id="studio-out-folder" value="${state.customOutputDir || state.defaultDownloads}" oninput="state.customOutputDir = this.value" class="w-full px-3 py-1.5 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)] cursor-text" />
              <button onclick="handleStudioBrowseOutFolder()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors">
                Browse
              </button>
            </div>
          </div>

          <!-- Primary Execute Action CTA -->
          <button 
            id="studio-btn-execute"
            onclick="handleExecuteTool('${tool.id}')"
            class="btn-primary w-full py-3 text-xs font-semibold rounded-xl bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>${tool.id === 'subtitle_animator' ? 'Export Video with Subtitles' : 'Start Processing'}</span>
            ${getIcon('arrow-right', 'w-3.5 h-3.5')}
          </button>
        </div>

        <!-- Right Pane: (${tool.id === 'subtitle_animator' ? 'Subtitle Studio 6 Cols' : 'Standard Stage Hub 5 Cols'}) -->
        <div class="${tool.id === 'subtitle_animator' ? 'lg:col-span-6' : 'lg:col-span-5'} space-y-4 flex flex-col max-h-[calc(100vh-160px)] overflow-y-auto pr-1">
          ${tool.id === 'subtitle_animator' ? `
            <!-- Live Preview Screen Card -->
            <div class="p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-1.5 font-bold text-[var(--text-primary)]">
                  ${getIcon('play', 'w-3.5 h-3.5 text-[var(--brand-primary)]')}
                  <span>Live 60fps Subtitle Preview</span>
                </div>
                <span id="sub-time-indicator" class="text-[11px] text-[var(--text-muted)] font-medium tabular-nums">00:00.80</span>
              </div>

              <div class="sub-preview-screen" id="sub-preview-screen-box">
                <video id="sub-video-element" class="sub-preview-video hidden" playsinline></video>
                <div id="sub-empty-bg" class="absolute inset-0 flex flex-col items-center justify-center text-center p-4 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
                  <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 mb-2">
                    ${getIcon('video', 'w-5 h-5')}
                  </div>
                  <span class="text-xs font-semibold text-slate-300">Live Visual Stage</span>
                  <span class="text-[10px] text-slate-500 mt-0.5">Drop a video on the left to preview with real footage</span>
                </div>
                <div id="sub-preview-overlay-wrap" class="sub-preview-overlay-wrap" style="bottom: 12%;">
                  <div id="sub-preview-text-box" class="sub-preview-text-box font-bold"></div>
                </div>
              </div>

              <!-- Playback & Scrubbing Controls -->
              <div class="flex items-center gap-2 pt-1">
                <button id="sub-btn-playpause" onclick="toggleSubtitleVideoPlay()" class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-hover)] shrink-0 transition-colors cursor-pointer">
                  ${getIcon('play', 'w-3.5 h-3.5')}
                </button>
                <input type="range" id="sub-video-scrubber" min="0" max="8" step="0.05" value="0.8" oninput="handleSubtitleScrub(this.value)" class="w-full accent-[var(--brand-primary)] cursor-pointer" />
                <span id="sub-dur-label" class="text-[11px] font-medium tabular-nums text-[var(--text-secondary)] shrink-0">00:08</span>
              </div>
            </div>

            <!-- Transcript & Timing Editor Card -->
            <div class="p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2 flex flex-col min-h-[220px]">
              <div class="flex items-center justify-between text-xs pb-1 border-b border-[var(--border-subtle)]">
                <div class="flex items-center gap-1.5 font-bold text-[var(--text-primary)]">
                  ${getIcon('type', 'w-3.5 h-3.5 text-[var(--brand-primary)]')}
                  <span>Subtitle Transcript Editor</span>
                  <span id="sub-cues-badge" class="px-1.5 py-0.5 rounded-full text-[10px] bg-[var(--surface-inset)] text-[var(--text-muted)] font-medium tabular-nums">0 cues</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <button onclick="addSubtitleCue()" class="px-2 py-1 rounded bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[11px] font-medium text-[var(--text-primary)] flex items-center gap-1 cursor-pointer transition-colors">
                    ${getIcon('plus', 'w-3 h-3')}
                    <span>Add Cue</span>
                  </button>
                </div>
              </div>

              <!-- Scrollable Cues List -->
              <div id="sub-cues-list" class="space-y-2 overflow-y-auto max-h-48 pr-1"></div>
            </div>
          ` : `
            <!-- Standard Stage Card for Other Tools -->
            <div id="studio-stage-card" class="p-6 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex-1 flex flex-col justify-center text-center">
              <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center bg-emerald-500/10 text-emerald-500 mb-3">
                ${getIcon('shield', 'w-6 h-6')}
              </div>
              <h4 class="text-sm font-semibold text-[var(--text-primary)]">Ready for Processing</h4>
              <p class="text-xs text-[var(--text-secondary)] mt-1 mb-5">Select or drop your files on the left to begin.</p>
              <div class="text-left space-y-2 p-3.5 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
                <div class="flex items-center gap-2">
                  ${getIcon('check', 'w-3.5 h-3.5 text-emerald-500 shrink-0')}
                  <span>Private on-device execution on your PC</span>
                </div>
                <div class="flex items-center gap-2">
                  ${getIcon('check', 'w-3.5 h-3.5 text-emerald-500 shrink-0')}
                  <span>Zero telemetry, zero cloud data leaks</span>
                </div>
                <div class="flex items-center gap-2">
                  ${getIcon('check', 'w-3.5 h-3.5 text-emerald-500 shrink-0')}
                  <span>High-throughput multi-core processing</span>
                </div>
              </div>
            </div>
          `}

          <!-- Progress Bar & Cancel Row -->
          <div id="studio-progress-wrap" class="hidden p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2.5">
            <div class="flex items-center justify-between text-xs">
              <span id="studio-status-txt" class="font-semibold text-[var(--text-primary)]">Processing...</span>
              <span id="studio-pct-txt" class="text-xs font-bold text-[var(--brand-primary)] tabular-nums">0%</span>
            </div>
            <div class="w-full bg-[var(--surface-inset)] h-2 rounded-full overflow-hidden">
              <div id="studio-progress-fill" class="bg-[var(--brand-primary)] h-full w-0 transition-all duration-200"></div>
            </div>
            <button onclick="handleCancelTool()" class="w-full py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer">
              Cancel Operation
            </button>
          </div>

          <!-- Activity Log Drawer -->
          <div class="p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2 flex-1 flex flex-col min-h-[120px]">
            <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Activity Log</span>
            <div id="studio-log-box" class="flex-1 p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] overflow-y-auto max-h-32 leading-relaxed">
              System ready. Waiting for input...
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  if (tool.id === 'subtitle_animator') {
    setTimeout(() => {
      initSubtitleStudio();
    }, 30);
  }
}

function getDefaultOptionsForTool(toolId) {
  if (toolId === 'media_audio_extractor') return { format: 'MP3 (320 kbps Studio Quality)' };
  if (toolId === 'video_compressor') return { mode: 'Balanced', target_mb: 50 };
  if (toolId === 'pdf_converter') return { mode: 'PDF to Images (PNG)' };
  if (toolId === 'image_webp_compress') return { quality: 80, smart_mode: true, max_dim: '1920px (Full HD)' };
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
  if (toolId === 'media_audio_extractor') return 'Supports MP4, MKV, MOV, WebM, AVI, FLV, WMV';
  if (toolId === 'video_compressor') return 'Supports MP4, MKV, MOV, WebM, AVI';
  if (toolId === 'pdf_converter') return 'Supports PDF documents and JPG/PNG images';
  if (toolId === 'image_webp_compress') return 'Supports PNG, JPG, JPEG, BMP, WebP';
  if (toolId === 'system_batch_rename') return 'Select any files or folder to batch rename';
  if (toolId === 'subtitle_animator') return 'Supports Video (MP4, MKV, MOV, WebM) + Subtitles (.srt, .vtt)';
  return 'Select or drop your files';
}

function renderToolSpecificOptions(toolId) {
  if (toolId === 'media_audio_extractor') {
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
    return `
      <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Compression Mode</span>
      <div class="grid grid-cols-2 gap-2 pt-1">
        ${['Balanced', 'High Quality', 'Small Size', 'Custom'].map(m => `
          <button 
            type="button"
            onclick="setStudioMode('${m}')"
            class="p-2.5 rounded-lg border text-left text-xs transition-all ${state.activeToolOptions.mode === m ? 'border-[var(--brand-primary)] bg-[var(--brand-light)] font-semibold text-[var(--brand-primary)]' : 'border-[var(--border-subtle)] bg-[var(--surface-inset)] text-[var(--text-primary)] hover:border-[var(--border-hover)]'}"
          >
            ${m}
          </button>
        `).join('')}
      </div>
    `;
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
    const qual = state.activeToolOptions.quality !== undefined ? state.activeToolOptions.quality : 80;
    return `
      <div class="space-y-3">
        <div>
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-semibold text-[var(--text-muted)] uppercase tracking-wider">Quality</span>
            <span id="qual-val-lbl" class="font-bold text-[var(--brand-primary)]">${qual}%</span>
          </div>
          <input type="range" min="40" max="100" value="${qual}" oninput="document.getElementById('qual-val-lbl').innerText = this.value + '%'; state.activeToolOptions.quality = this.value;" class="w-full accent-[var(--brand-primary)]" />
        </div>
        <div>
          <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Max Dimension Limit</span>
          ${renderCustomDropdown({
            id: 'dropdown-webp-dim',
            currentValue: state.activeToolOptions.max_dim || '1920px (Full HD)',
            options: [
              { value: '1920px (Full HD)', label: '1920px (Full HD)' },
              { value: '2560px (2K)', label: '2560px (2K)' },
              { value: 'Original (No Downscale)', label: 'Original (No Downscale)' },
              { value: '1280px (Web Compact)', label: '1280px (Web Compact)' }
            ],
            onSelect: 'handleSelectWebpDim'
          })}
        </div>
      </div>
    `;
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
        <div>
          <span class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Text / Tag</span>
          <input type="text" value="${state.activeToolOptions.text1 || '_v1'}" oninput="state.activeToolOptions.text1 = this.value" class="w-full mt-1.5 px-3 py-2 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)]" />
        </div>
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
                onclick="handleSelectSubtitleStyle('${p.id}')"
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
              onclick="handleBrowseCustomFont()" 
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
                <input type="color" value="${opts.primary_color || (opts.style === 'white_box' ? '#000000' : '#FFFFFF')}" onchange="setSubtitleColor('primary_color', this.value)" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.primary_color || (opts.style === 'white_box' ? '#000' : '#FFF')}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">${opts.style === 'white_box' ? 'Tag Background' : 'Box Background'}</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.outline_color || (opts.style === 'white_box' ? '#FFFFFF' : '#0F172A')}" onchange="setSubtitleColor('outline_color', this.value)" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.outline_color || (opts.style === 'white_box' ? '#FFF' : '#0F172A')}</span>
              </div>
            </div>
          </div>
        ` : `
          <div class="grid grid-cols-3 gap-2">
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Base Text</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.primary_color || '#FFFFFF'}" onchange="setSubtitleColor('primary_color', this.value)" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.primary_color || '#FFF'}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Active Highlight</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.highlight_color || '#FFE600'}" onchange="setSubtitleColor('highlight_color', this.value)" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
                <span class="text-xs font-semibold tabular-nums text-[var(--text-primary)]">${opts.highlight_color || '#FFE600'}</span>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)]">
              <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase block mb-1">Outline Stroke</span>
              <div class="flex items-center gap-1.5">
                <input type="color" value="${opts.outline_color || '#000000'}" onchange="setSubtitleColor('outline_color', this.value)" class="w-6 h-6 rounded cursor-pointer border-0 bg-transparent" />
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
              oninput="document.getElementById('sub-fontsize-val').innerText = this.value + 'px'; setSubtitleFontSize(this.value);" 
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
                    onclick="setSubtitlePosition('${pKey}')" 
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
              onchange="setSubtitleAllCaps(this.checked)" 
              class="rounded text-[var(--brand-primary)] accent-[var(--brand-primary)] cursor-pointer" 
            />
            <span class="font-medium text-[var(--text-primary)]">Force UPPERCASE</span>
          </label>
          <div class="flex items-center gap-1.5">
            <button 
              type="button" 
              onclick="loadDemoSubtitleSample()" 
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
        onclick="selectCustomDropdownOption('${id}', '${safeVal}', '${safeLbl}', '${onSelect}')"
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
        onclick="toggleCustomDropdown('${id}', event)"
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

window.handleSelectWebpDim = function(val) {
  state.activeToolOptions.max_dim = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
};

window.handleSelectRenameRule = function(val) {
  state.activeToolOptions.rule = val;
  const optBox = document.getElementById('studio-options-box');
  if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
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

async function handleStudioBrowseFiles(toolId) {
  let fileTypes = [];
  if (toolId === 'video_compressor') {
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
    state.selectedFiles = files;
    updateStudioFilesUI();
    if (toolId === 'subtitle_animator') {
      await handleSubtitleFilesLoaded(files);
    }
  }
}

function updateStudioFilesUI() {
  const wrap = document.getElementById('studio-files-wrap');
  const countLbl = document.getElementById('studio-files-count');
  const list = document.getElementById('studio-files-list');
  if (!wrap || !list) return;

  if (state.selectedFiles.length === 0) {
    wrap.classList.add('hidden');
    return;
  }

  wrap.classList.remove('hidden');
  countLbl.innerText = `${state.selectedFiles.length} file${state.selectedFiles.length > 1 ? 's' : ''} loaded`;
  list.innerHTML = state.selectedFiles.map(f => `
    <div class="px-2.5 py-1.5 rounded-md bg-[var(--surface-inset)] flex items-center justify-between text-xs text-[var(--text-primary)]">
      <span class="truncate pr-2">${f.split('\\\\').pop()}</span>
      <span class="text-[10px] text-[var(--text-muted)] shrink-0">Ready</span>
    </div>
  `).join('');
}

function clearStudioFiles() {
  state.selectedFiles = [];
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

  // Show Progress UI
  const progWrap = document.getElementById('studio-progress-wrap');
  const btnExec = document.getElementById('studio-btn-execute');
  if (progWrap) progWrap.classList.remove('hidden');
  if (btnExec) {
    btnExec.disabled = true;
    btnExec.classList.add('opacity-50');
  }

  // Clear log
  const logBox = document.getElementById('studio-log-box');
  if (logBox) logBox.innerHTML = `<div>Starting execution...</div>`;

  await callBridge('execute_tool', toolId, state.selectedFiles, state.activeToolOptions, outDir);
}

async function handleCancelTool() {
  await callBridge('cancel_tool');
}

// Bridge Event Handlers (Called by Python evaluate_js)
window.onToolProgress = function(data) {
  const pct = data.percent || 0;
  const status = data.status || 'Processing...';

  const fill = document.getElementById('studio-progress-fill');
  const pctTxt = document.getElementById('studio-pct-txt');
  const statusTxt = document.getElementById('studio-status-txt');

  if (fill) fill.style.width = `${pct}%`;
  if (pctTxt) pctTxt.innerText = `${Math.round(pct)}%`;
  if (statusTxt) statusTxt.innerText = status;
};

window.onToolLog = function(msg) {
  const logBox = document.getElementById('studio-log-box');
  if (logBox) {
    logBox.innerHTML += `<div>${msg}</div>`;
    logBox.scrollTop = logBox.scrollHeight;
  }
};

window.onToolComplete = function(data) {
  state.isToolRunning = false;
  state.lastOutputFile = data.output_file || '';

  const btnExec = document.getElementById('studio-btn-execute');
  if (btnExec) {
    btnExec.disabled = false;
    btnExec.classList.remove('opacity-50');
  }

  const stage = document.getElementById('studio-stage-card');
  if (stage) {
    stage.innerHTML = `
      <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center bg-emerald-500/10 text-emerald-500 mb-3">
        ${getIcon('check', 'w-6 h-6')}
      </div>
      <h4 class="text-sm font-semibold text-[var(--text-primary)]">Processing Complete!</h4>
      <p class="text-xs text-[var(--text-secondary)] mt-1 mb-5">Your output file was successfully generated.</p>
      <div class="space-y-2">
        <button onclick="handleOpenOutputFile()" class="btn-primary w-full py-2 text-xs font-semibold rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all flex items-center justify-center gap-1.5 cursor-pointer">
          <span>Open Output File</span>
          ${getIcon('arrow-right', 'w-3.5 h-3.5')}
        </button>
        <button onclick="handleRevealOutputFolder()" class="w-full py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors cursor-pointer">
          Reveal in Folder
        </button>
      </div>
    `;
  }
};

window.onToolError = function(errMsg) {
  state.isToolRunning = false;
  const btnExec = document.getElementById('studio-btn-execute');
  if (btnExec) {
    btnExec.disabled = false;
    btnExec.classList.remove('opacity-50');
  }

  const statusTxt = document.getElementById('studio-status-txt');
  if (statusTxt) statusTxt.innerText = `Error: ${errMsg}`;
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
          <button onclick="seekSubtitlePreview(${cue.start})" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--brand-light)] hover:text-[var(--brand-primary)] text-[var(--text-secondary)] font-semibold tabular-nums transition-colors cursor-pointer border border-[var(--border-subtle)]" title="Click to seek preview">
            ${formatDisplayTime(cue.start)} → ${formatDisplayTime(cue.end)}
          </button>
          <button onclick="nudgeCueTime(${cue.id}, -0.1)" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] text-[10px] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-pointer" title="Nudge back 0.1s">-0.1s</button>
          <button onclick="nudgeCueTime(${cue.id}, 0.1)" class="px-1.5 py-0.5 rounded bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] text-[10px] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-pointer" title="Nudge forward 0.1s">+0.1s</button>
        </div>
        <button onclick="deleteSubtitleCue(${cue.id})" class="text-red-400 hover:text-red-500 text-[11px] p-1 cursor-pointer transition-colors" title="Delete Cue">
          ${getIcon('trash', 'w-3 h-3')}
        </button>
      </div>
      <input 
        type="text" 
        value="${cue.text.replace(/"/g, '&quot;')}" 
        oninput="updateSubtitleCueText(${cue.id}, this.value)" 
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
    <div onclick="closeCommandPalette(); navigateTo('tool_studio', '${t.id}')" class="p-2.5 rounded-lg hover:bg-[var(--surface-inset)] cursor-pointer flex items-center justify-between transition-colors">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-md flex items-center justify-center bg-[var(--surface-card)] text-[var(--brand-primary)]">
          ${getIcon(t.icon, 'w-3.5 h-3.5')}
        </div>
        <div>
          <span class="text-xs font-semibold text-[var(--text-primary)]">${t.name}</span>
          <span class="ml-2 text-[10px] text-[var(--text-muted)]">${t.category_name}</span>
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
  const data = await callBridge('get_initial_data');
  if (data) state.tools = data.tools;
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

  const items = state.announcements && state.announcements.length > 0 ? state.announcements : [
    {
      id: "sb_boltools_tool_06_subtitle_animator",
      date: "2026-10-10",
      tag: "NEW TOOL",
      title: "Subtitle Animation Maker (Now Live)",
      description: "Create viral animated subtitles with word-by-word karaoke highlights, custom fonts, colors, and live 60fps timing preview 100% offline.",
      cta_text: "Open Tool Hub",
      cta_url: "https://thesurfboard.in"
    },
    {
      id: "sb_boltools_launch_01",
      date: "2026-10-05",
      tag: "READY",
      title: "Welcome to Boltools Desktop Suite",
      description: "The 100% offline Swiss Army knife for creators, editors, and power users. Zero subscriptions. Zero data leaks.",
      cta_text: "Join SurfBoard Community",
      cta_url: "https://thesurfboard.in"
    }
  ];

  list.innerHTML = items.map(a => `
    <div class="p-3.5 rounded-xl bg-[var(--surface-inset)] border border-[var(--border-subtle)] space-y-1.5">
      <div class="flex items-center justify-between">
        <span class="px-2 py-0.5 text-[9px] font-bold rounded bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${a.tag || 'UPDATE'}</span>
        <span class="text-[10px] text-[var(--text-muted)]">${a.date || ''}</span>
      </div>
      <h4 class="text-xs font-semibold text-[var(--text-primary)]">${a.title}</h4>
      <p class="text-[11px] text-[var(--text-secondary)] leading-relaxed">${a.description}</p>
      ${a.cta_action ? `
        <div class="pt-1">
          <button onclick="handleAnnouncementAction('${a.cta_action}', '${a.cta_target || ''}')" class="text-[11px] font-medium text-[var(--brand-primary)] hover:underline inline-flex items-center gap-1 cursor-pointer">
            <span>${a.cta_text || 'Open in App'}</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
      ` : (a.cta_url ? `
        <div class="pt-1">
          <a href="${a.cta_url}" target="_blank" class="text-[11px] font-medium text-[var(--brand-primary)] hover:underline inline-flex items-center gap-1">
            <span>${a.cta_text || 'Learn more'}</span>
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
    <span>${message}</span>
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

  // Bind shortcuts & global click dismissals
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown-container')) {
      closeAllCustomDropdowns();
    }
    const cmdModal = document.getElementById('modal-command-palette');
    if (cmdModal && !cmdModal.classList.contains('hidden')) {
      if (e.target === cmdModal) {
        closeCommandPalette();
      }
    }
  });

  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openCommandPalette();
    }
    if (e.key === 'Escape') {
      closeCommandPalette();
      closeUninstallModal();
      closeAnnouncementsModal();
      closeAllCustomDropdowns();
    }
  });

  // Render initial view immediately with guaranteed defaults (0ms UI latency)
  navigateTo('home', null, false);

  // Background bridge synchronization loop
  async function syncBridgeData() {
    let attempts = 0;
    while (attempts < 40) {
      const data = await callBridge('get_initial_data');
      if (data) {
        if (data.categories && data.categories.length) state.categories = data.categories;
        if (data.tools && data.tools.length) state.tools = data.tools;
        if (data.favorites) state.favorites = data.favorites;
        if (data.announcements && data.announcements.length) state.announcements = data.announcements;
        if (data.updates_count !== undefined) state.updatesCount = data.updates_count;
        if (data.system_stats) state.systemStats = data.system_stats;
        if (data.default_downloads) state.defaultDownloads = data.default_downloads;

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
        break;
      }
      attempts++;
      await new Promise(r => setTimeout(r, 100));
    }
  }
  syncBridgeData();

  // Start system monitor ticker
  setInterval(async () => {
    const stats = await callBridge('get_system_stats');
    if (stats) {
      const cpu = document.getElementById('mon-cpu-fill');
      const ram = document.getElementById('mon-ram-fill');
      const disk = document.getElementById('mon-disk-fill');
      if (cpu) cpu.style.width = `${stats.cpu}%`;
      if (ram) ram.style.width = `${stats.ram}%`;
      if (disk) disk.style.width = `${stats.disk}%`;
    }
    // Background check for newly arrived announcements
    const latestAnnouncements = await callBridge('get_announcements');
    if (latestAnnouncements && latestAnnouncements.length) {
      state.announcements = latestAnnouncements;
      const seenIds = JSON.parse(localStorage.getItem('boltools-seen-announcements') || '[]');
      const unread = (state.announcements || []).filter(a => !seenIds.includes(a.id)).length;
      updateBellBadge(unread > 0 ? unread : 0);
    }
  }, 3000);
}

// ── Self-healing Bootstrap ──────────────────────────────────────────────────
let appInitialized = false;

async function bootstrapApp() {
  if (appInitialized) return;
  appInitialized = true;
  await initApp();
}

window.addEventListener('pywebviewready', bootstrapApp);
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(bootstrapApp, 20);
});
