/**
 * New tools in the store: a dot on Tool Hub until the user opens it, and the
 * bell refreshed with "<tool> is available". Python decides what is new
 * (src/core/new_tools.py); this only shows it.
 */
const NewToolsBadge = (() => {
  function setDot(visible) {
    const button = document.querySelector('#app-sidebar [data-key="tools"]');
    if (!button) return;
    let dot = button.querySelector('.sb-new-dot');
    if (!dot) {
      dot = document.createElement('i');
      dot.className = 'sb-new-dot';
      dot.setAttribute('aria-hidden', 'true');
      button.appendChild(dot);
    }
    dot.hidden = !visible;
    button.dataset.newTools = visible ? 'true' : 'false';
  }

  async function refreshBell() {
    const items = await callBridge('get_announcements');
    if (!Array.isArray(items)) return;
    state.announcements = items;
    let seenIds = [];
    try { seenIds = JSON.parse(localStorage.getItem('boltools-seen-announcements') || '[]'); } catch (err) { seenIds = []; }
    updateBellBadge(items.filter(a => !seenIds.includes(a.id)).length);
  }

  async function refresh() {
    const ids = await callBridge('get_new_tools');
    setDot(Array.isArray(ids) && ids.length > 0);
  }

  // Opening the store is "seeing" the new tools: the dot goes, the bell notice stays until read.
  async function storeOpened() {
    if (document.querySelector('#app-sidebar [data-new-tools="true"]')) {
      await callBridge('mark_store_seen');
      setDot(false);
    }
  }

  window.onNewTools = () => { refresh(); refreshBell(); };

  return { refresh, refreshBell, storeOpened };
})();
