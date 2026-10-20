/**
 * Sidebar collapse: full labels, or icons only to give tools more room.
 * The choice is a per-PC convenience, so it lives in localStorage.
 */
const SidebarToggle = (() => {
  const STORAGE_KEY = 'boltools-sidebar-collapsed';
  const CLASS_NAME = 'sidebar-collapsed';

  function read() {
    try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch (err) { return false; }
  }

  function write(collapsed) {
    try { localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0'); } catch (err) { /* private storage: just not remembered */ }
  }

  // Icons alone need their names on hover; the visible label already says it when expanded.
  function syncTooltips(collapsed) {
    document.querySelectorAll('#app-sidebar .sidebar-nav-btn, #app-sidebar .sidebar-cat-btn').forEach(btn => {
      const label = btn.querySelector('span')?.textContent.trim() || '';
      if (collapsed) {
        btn.title = label;
        btn.setAttribute('aria-label', label);
      } else {
        btn.removeAttribute('title');
        btn.removeAttribute('aria-label');
      }
    });
  }

  function apply(collapsed) {
    document.documentElement.classList.toggle(CLASS_NAME, collapsed);
    const button = document.getElementById('btn-sidebar-toggle');
    if (button) {
      button.setAttribute('aria-expanded', String(!collapsed));
      button.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
      button.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
    }
    syncTooltips(collapsed);
  }

  function toggle() {
    const collapsed = !document.documentElement.classList.contains(CLASS_NAME);
    write(collapsed);
    apply(collapsed);
  }

  document.addEventListener('DOMContentLoaded', () => apply(read()));

  return { toggle };
})();
