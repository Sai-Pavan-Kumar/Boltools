/**
 * Boltools Desktop Client Application Controller (Option 1 Architecture)
 * 100% Offline, Pixel-Perfect Linear / Apple Standard
 */

// ── Application State ────────────────────────────────────────────────────────
const state = {
  theme: localStorage.getItem('boltools-theme') || 'dark',
  currentView: 'home',
  activeToolId: null,
  navHistory: ['home'],
  categories: [],
  tools: [],
  favorites: [],
  systemStats: { cpu: 12, ram: 45, disk: 38 },
  defaultDownloads: '',
  searchQuery: '',
  hubFilterTab: 'All', // 'All', 'Installed', 'Hub Catalog'
  selectedFiles: [],
  activeToolOptions: {},
  isToolRunning: false
};

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
    state.navHistory.push({ view: viewName, toolId });
  }

  // Update Sidebar Active Highlight
  document.querySelectorAll('.sidebar-nav-btn').forEach(btn => {
    const key = btn.dataset.key;
    if (key === viewName || (key === 'tools' && viewName === 'tool_hub')) {
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
    renderToolStudio(container, toolId);
  }
}

function navigateBack() {
  if (state.navHistory.length > 1) {
    state.navHistory.pop(); // Pop current view
    const prev = state.navHistory[state.navHistory.length - 1];
    navigateTo(prev.view, prev.toolId, false);
  } else {
    navigateTo('home', null, false);
  }
}

function updateBreadcrumb(crumbs) {
  const bc = document.getElementById('header-breadcrumb');
  if (!bc) return;

  let html = '';
  if (crumbs.length > 1) {
    html += `<button onclick="navigateBack()" class="flex items-center gap-1.5 px-2 py-1 mr-2 text-xs font-medium rounded-md bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">
      ${getIcon('arrow-left', 'w-3.5 h-3.5')}
      <span>Back</span>
    </button>`;
  }

  crumbs.forEach((crumb, idx) => {
    const isLast = idx === crumbs.length - 1;
    if (idx > 0) {
      html += `<span class="mx-2 text-xs text-[var(--text-muted)]">/</span>`;
    }
    if (idx === 0 && !isLast) {
      html += `<button onclick="navigateTo('home')" class="text-xs font-normal text-[var(--brand-primary)] hover:underline">${crumb}</button>`;
    } else {
      html += `<span class="text-xs ${isLast ? 'font-semibold text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}">${crumb}</span>`;
    }
  });

  bc.innerHTML = html;
}

// ── View Renderers ───────────────────────────────────────────────────────────

// 1. Home Dashboard View
function renderHome(container) {
  const catCards = state.categories.map(c => `
    <div onclick="navigateTo('tool_hub')" class="group p-4 rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] hover:border-[var(--border-hover)] cursor-pointer transition-all flex items-center justify-between">
      <div class="flex items-center gap-3.5">
        <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] group-hover:scale-105 transition-transform" style="color: ${c.accent};">
          ${getIcon(c.icon, 'w-5 h-5')}
        </div>
        <div>
          <h4 class="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)] transition-colors">${c.name}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-0.5 line-clamp-1">${c.desc}</p>
        </div>
      </div>
      <div class="text-[var(--text-muted)] group-hover:text-[var(--text-primary)] group-hover:translate-x-1 transition-all">
        ${getIcon('chevron-right', 'w-4 h-4')}
      </div>
    </div>
  `).join('');

  const readyTools = state.tools.filter(t => t.status === 'installed');
  const toolRows = readyTools.length > 0 ? readyTools.map(t => `
    <div class="p-3.5 rounded-xl bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] transition-all flex items-center justify-between gap-4">
      <div class="flex items-center gap-3.5 min-w-0">
        <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)] shrink-0">
          ${getIcon(t.icon, 'w-4.5 h-4.5')}
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-[var(--text-primary)] truncate">${t.name}</span>
            <span class="px-2 py-0.5 text-[10px] font-medium rounded-full bg-[var(--surface-pill)] text-[var(--text-secondary)] uppercase tracking-wider">${t.category_name}</span>
          </div>
          <p class="text-xs text-[var(--text-secondary)] truncate mt-0.5">${t.description}</p>
        </div>
      </div>
      <button onclick="navigateTo('tool_studio', '${t.id}')" class="btn-primary shrink-0 px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm">
        <span>Launch</span>
        ${getIcon('arrow-right', 'w-3 h-3')}
      </button>
    </div>
  `).join('') : `
    <div class="p-6 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] text-center">
      <p class="text-xs text-[var(--text-secondary)] mb-2">No utilities currently installed on this PC.</p>
      <button onclick="navigateTo('tool_hub')" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white inline-flex items-center gap-1.5">
        <span>Browse Tool Hub</span>
        ${getIcon('arrow-right', 'w-3 h-3')}
      </button>
    </div>
  `;

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-7 pb-10">
      <!-- Hero -->
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Offline Utility Suite</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">High-speed, 100% private tools for creator workflows and local power operations.</p>
      </div>

      <!-- Categories 2x2 Grid -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Categories</span>
          <button onclick="navigateTo('tool_hub')" class="text-xs font-medium text-[var(--brand-primary)] hover:underline flex items-center gap-1">
            <span>Open Tool Hub</span>
            ${getIcon('chevron-right', 'w-3 h-3')}
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          ${catCards}
        </div>
      </div>

      <!-- Available Utilities Shelf -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Available Utilities</span>
          <span class="text-xs text-[var(--text-muted)]">${readyTools.length} offline ready</span>
        </div>
        <div class="space-y-2.5">
          ${toolRows}
        </div>
      </div>
    </div>
  `;
}

// 2. Tool Hub & Catalog View
function renderToolHub(container) {
  const filterTab = state.hubFilterTab;
  const query = state.searchQuery.toLowerCase().trim();

  let filtered = state.tools.filter(t => {
    const isInstalled = t.status === 'installed';
    if (filterTab === 'Installed' && !isInstalled) return false;
    if (filterTab === 'Hub Catalog' && isInstalled) return false;
    if (query) {
      const match = t.name.toLowerCase().includes(query) ||
                    t.description.toLowerCase().includes(query) ||
                    t.category_name.toLowerCase().includes(query);
      if (!match) return false;
    }
    return true;
  });

  const cardsHtml = filtered.map(t => {
    const isInstalled = t.status === 'installed';
    return `
      <div class="p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] hover:border-[var(--border-hover)] transition-all flex flex-col justify-between">
        <div>
          <div class="flex items-center gap-2.5 mb-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-inset)] text-[var(--brand-primary)]">
              ${getIcon(t.icon, 'w-4 h-4')}
            </div>
            <span class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--surface-pill)] text-[var(--brand-primary)] uppercase tracking-wider">${t.category_name}</span>
          </div>
          <h4 class="text-sm font-semibold text-[var(--text-primary)]">${t.name}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">${t.description}</p>
        </div>
        <div class="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between gap-2">
          ${isInstalled ? `
            <button onclick="navigateTo('tool_studio', '${t.id}')" class="btn-primary px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm">
              <span>Open Tool</span>
              ${getIcon('arrow-right', 'w-3 h-3')}
            </button>
            <button onclick="openUninstallModal('${t.id}', '${t.name}')" class="px-2.5 py-1.5 text-xs font-normal rounded-lg text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors">
              Uninstall
            </button>
          ` : `
            <button onclick="handleInstallTool('${t.id}')" class="btn-primary px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm">
              ${getIcon('download', 'w-3.5 h-3.5')}
              <span>+ Install (Free)</span>
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="max-w-5xl mx-auto space-y-6 pb-10">
      <div>
        <h2 class="text-xl font-bold font-display text-[var(--text-primary)] tracking-tight">Tool Hub</h2>
        <p class="text-xs text-[var(--text-secondary)] mt-1">Browse, install, and manage modular offline tools on this PC.</p>
      </div>

      <!-- Filter Tabs & Search Bar -->
      <div class="p-2 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex flex-col sm:flex-row items-center gap-3">
        <!-- Segmented Tabs -->
        <div class="flex items-center gap-1 p-1 bg-[var(--surface-inset)] rounded-lg shrink-0">
          ${['All', 'Installed', 'Hub Catalog'].map(tab => `
            <button onclick="setHubTab('${tab}')" class="px-3 py-1 text-xs font-medium rounded-md transition-all ${filterTab === tab ? 'bg-[var(--surface-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}">
              ${tab}
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

async function handleInstallTool(toolId) {
  await callBridge('install_tool', toolId);
  const data = await callBridge('get_initial_data');
  if (data) state.tools = data.tools;
  const container = document.getElementById('main-content');
  if (state.currentView === 'tool_hub' && container) {
    renderToolHub(container);
  } else if (state.currentView === 'home' && container) {
    renderHome(container);
  }
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
        <!-- Left Pane: Controls & Inputs (7 Cols) -->
        <div class="lg:col-span-7 space-y-4 overflow-y-auto max-h-[calc(100vh-160px)] pr-1">
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
              <input type="text" id="studio-out-folder" value="${state.defaultDownloads}" readonly class="w-full px-3 py-1.5 text-xs rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-[var(--text-primary)]" />
              <button onclick="handleStudioBrowseOutFolder()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors">
                Browse
              </button>
            </div>
          </div>

          <!-- Primary Execute Action CTA -->
          <button 
            id="studio-btn-execute"
            onclick="handleExecuteTool('${tool.id}')"
            class="btn-primary w-full py-3 text-xs font-semibold rounded-xl bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
          >
            <span>Start Processing</span>
            ${getIcon('arrow-right', 'w-3.5 h-3.5')}
          </button>
        </div>

        <!-- Right Pane: Live Inspector & Output Hub (5 Cols) -->
        <div class="lg:col-span-5 space-y-4 flex flex-col max-h-[calc(100vh-160px)]">
          <!-- Stage Card -->
          <div id="studio-stage-card" class="p-6 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] flex-1 flex flex-col justify-center text-center">
            <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center bg-emerald-500/10 text-emerald-500 mb-3">
              ${getIcon('shield', 'w-6 h-6')}
            </div>
            <h4 class="text-sm font-semibold text-[var(--text-primary)]">Ready for Processing</h4>
            <p class="text-xs text-[var(--text-secondary)] mt-1 mb-5">Select or drop your files on the left to begin.</p>
            <div class="text-left space-y-2 p-3.5 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
              <div class="flex items-center gap-2">
                ${getIcon('check', 'w-3.5 h-3.5 text-emerald-500 shrink-0')}
                <span>100% Offline execution on your local PC</span>
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

          <!-- Progress Bar & Cancel Row -->
          <div id="studio-progress-wrap" class="hidden p-4 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2.5">
            <div class="flex items-center justify-between text-xs">
              <span id="studio-status-txt" class="font-semibold text-[var(--text-primary)]">Processing...</span>
              <span id="studio-pct-txt" class="font-mono text-[var(--brand-primary)]">0%</span>
            </div>
            <div class="w-full bg-[var(--surface-inset)] h-2 rounded-full overflow-hidden">
              <div id="studio-progress-fill" class="bg-[var(--brand-primary)] h-full w-0 transition-all duration-200"></div>
            </div>
            <button onclick="handleCancelTool()" class="w-full py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10 rounded-lg transition-colors">
              Cancel Operation
            </button>
          </div>

          <!-- Activity Log Drawer -->
          <div class="p-3.5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-2 flex-1 flex flex-col min-h-[140px]">
            <span class="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Activity Log</span>
            <div id="studio-log-box" class="flex-1 p-2 rounded-lg bg-[var(--surface-inset)] border border-[var(--border-subtle)] font-mono text-[11px] text-[var(--text-secondary)] overflow-y-auto max-h-36 leading-relaxed">
              System ready. Waiting for input...
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function getDefaultOptionsForTool(toolId) {
  if (toolId === 'media_audio_extractor') return { format: 'MP3 (320 kbps Studio Quality)' };
  if (toolId === 'video_compressor') return { mode: 'Balanced', target_mb: 50 };
  if (toolId === 'pdf_converter') return { mode: 'PDF to Images (PNG)' };
  if (toolId === 'image_webp_compress') return { quality: 80, smart_mode: true, max_dim: '1920px (Full HD)' };
  if (toolId === 'system_batch_rename') return { rule: 'Add Suffix', text1: '_v1', text2: '', op_mode: 'Rename In-Place' };
  return {};
}

function getDropzoneHint(toolId) {
  if (toolId === 'media_audio_extractor') return 'Supports MP4, MKV, MOV, WebM, AVI, FLV, WMV';
  if (toolId === 'video_compressor') return 'Supports MP4, MKV, MOV, WebM, AVI';
  if (toolId === 'pdf_converter') return 'Supports PDF documents and JPG/PNG images';
  if (toolId === 'image_webp_compress') return 'Supports PNG, JPG, JPEG, BMP, WebP';
  if (toolId === 'system_batch_rename') return 'Select any files or folder to batch rename';
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

function setStudioMode(modeName) {
  state.activeToolOptions.mode = modeName;
  const container = document.getElementById('main-content');
  if (container) renderToolStudio(container, state.activeToolId);
}

async function handleStudioBrowseFiles(toolId) {
  let fileTypes = [];
  if (toolId === 'video_compressor' || toolId === 'media_audio_extractor') {
    fileTypes = ['Media & Video Files (*.mp4;*.mkv;*.mov;*.webm;*.avi;*.flv;*.wmv;*.m4v)'];
  } else if (toolId === 'pdf_converter') {
    fileTypes = ['Documents & Images (*.pdf;*.png;*.jpg;*.jpeg)'];
  } else if (toolId === 'image_webp_compress') {
    fileTypes = ['Image Files (*.png;*.jpg;*.jpeg;*.bmp;*.webp)'];
  }

  const files = await callBridge('browse_files', fileTypes);
  if (files && files.length > 0) {
    state.selectedFiles = files;
    updateStudioFilesUI();
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
  const outPath = data.output_file || '';

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
        <button onclick="callBridge('open_path', '${outPath.replace(/\\\\/g, '/')}')" class="btn-primary w-full py-2 text-xs font-semibold rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all flex items-center justify-center gap-1.5">
          <span>Open Output File</span>
          ${getIcon('arrow-right', 'w-3.5 h-3.5')}
        </button>
        <button onclick="callBridge('open_path', '${outPath.replace(/\\\\/g, '/').split('/').slice(0, -1).join('/')}')" class="w-full py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">
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

// ── Application Bootstrapper ─────────────────────────────────────────────────
async function initApp() {
  applyTheme(state.theme);

  // Fetch initial state from bridge (with fast retry if bridge was still connecting)
  let data = await callBridge('get_initial_data');
  if (!data) {
    await new Promise(r => setTimeout(r, 120));
    data = await callBridge('get_initial_data');
  }

  if (data) {
    state.categories = data.categories || [];
    state.tools = data.tools || [];
    state.favorites = data.favorites || [];
    state.systemStats = data.system_stats || { cpu: 12, ram: 45, disk: 38 };
    state.defaultDownloads = data.default_downloads || '';
  }

  // Bind shortcuts & global click dismissals
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.custom-dropdown-container')) {
      closeAllCustomDropdowns();
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
      closeAllCustomDropdowns();
    }
  });

  // Render initial view
  navigateTo('home', null, false);

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
  // Fallback in case pywebviewready already fired or was delayed
  setTimeout(bootstrapApp, 50);
});
