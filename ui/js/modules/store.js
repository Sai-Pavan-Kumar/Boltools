/**
 * Reactive State Store with Granular Pub/Sub
 * Enables fine-grained DOM mutation without monolithic re-renders.
 */

class Store {
  constructor(initialState = {}) {
    this._state = {
      theme: localStorage.getItem('boltools-theme') || 'light',
      currentView: 'home',
      activeToolId: null,
      activeCategoryId: null,
      navHistory: [{ view: 'home', toolId: null }],
      categories: [],
      tools: [],
      favorites: [],
      recentTools: JSON.parse(localStorage.getItem('boltools-recent-tools') || '[]'),
      lastOutputFile: null,
      customOutputDir: '',
      announcements: [],
      unreadAnnouncementsCount: 0,
      systemStats: { cpu: 0, ram: 0, disk: 0 },
      defaultDownloads: '',
      searchQuery: '',
      hubFilterTab: 'All', // 'All', 'Installed', 'Updates', 'Hub Catalog'
      selectedFiles: [],
      activeToolOptions: {},
      isToolRunning: false,
      scrollPositions: {},
      ...initialState
    };
    this._listeners = new Map();
  }

  get state() {
    return this._state;
  }

  get(key) {
    return this._state[key];
  }

  set(key, value) {
    const prev = this._state[key];
    if (prev === value) return;
    this._state[key] = value;
    this._notify(key, value, prev);
  }

  update(partial) {
    for (const [key, val] of Object.entries(partial)) {
      this.set(key, val);
    }
  }

  subscribe(key, callback) {
    if (!this._listeners.has(key)) {
      this._listeners.set(key, new Set());
    }
    this._listeners.get(key).add(callback);
    return () => this.unsubscribe(key, callback);
  }

  unsubscribe(key, callback) {
    if (this._listeners.has(key)) {
      this._listeners.get(key).delete(callback);
    }
  }

  _notify(key, value, prev) {
    if (this._listeners.has(key)) {
      this._listeners.get(key).forEach(cb => cb(value, prev));
    }
    if (this._listeners.has('*')) {
      this._listeners.get('*').forEach(cb => cb(key, value, prev));
    }
  }
}

const store = new Store();
window.boltoolsStore = store;
