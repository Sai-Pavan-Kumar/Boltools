/**
 * Settings card for the daily "new tools" check (src/core/background_check.py).
 * The switch reflects the saved choice; flipping it creates or removes the
 * Windows scheduled job right away.
 */
const NotificationSettings = (() => {
  function card() {
    return `
      <div class="p-5 rounded-xl bg-[var(--surface-card)] border border-[var(--border-subtle)] space-y-3">
        <span class="text-xs font-semibold text-[var(--text-muted)] tracking-wider uppercase">Notifications</span>
        <div class="flex items-center justify-between gap-4 pt-1">
          <div>
            <h4 class="text-sm font-semibold text-[var(--text-primary)]">Tell me about new tools, even when Boltools is closed</h4>
            <p class="text-xs text-[var(--text-secondary)] mt-0.5">A tiny check runs once a day and shows a Windows notification only when a new tool is out. Turn it off and nothing of Boltools runs in the background. While Boltools is open you always see new tools.</p>
          </div>
          <button type="button" id="setting-background-check" role="switch" aria-checked="false"
            aria-label="Daily check for new tools" class="nset-switch" data-action="toggle-background-check" disabled>
            <span class="nset-knob"></span>
          </button>
        </div>
      </div>`;
  }

  function setSwitch(enabled, busy = false) {
    const sw = document.getElementById('setting-background-check');
    if (!sw) return;
    sw.setAttribute('aria-checked', String(Boolean(enabled)));
    sw.disabled = busy;
  }

  async function load() {
    const enabled = await callBridge('get_background_check');
    setSwitch(enabled !== false);
  }

  async function toggle() {
    const sw = document.getElementById('setting-background-check');
    if (!sw || sw.disabled) return;
    const next = sw.getAttribute('aria-checked') !== 'true';
    setSwitch(next, true);
    const ok = await callBridge('set_background_check', next);
    setSwitch(ok ? next : !next);
    showToast(ok ? (next ? 'Daily new-tool check is on' : 'Daily check is off. Nothing runs in the background.')
                 : 'Windows did not accept the change. Please try again.', ok ? 'success' : 'error');
  }

  return { card, load, toggle };
})();
