// Quick card: Python (src/quick_run.py) drives it through window.Quick.*;
// buttons call back through window.pywebview.api.
(function () {
  const AUTO_CLOSE_MS = 12000;
  const $ = (id) => document.getElementById(id);
  const card = $('quick');
  const fileName = (path) => String(path || '').split(/[\\/]/).pop();
  let outputPath = null;
  let closeTimer = null;
  let hovering = false;

  document.documentElement.dataset.theme =
    window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';

  const api = () => (window.pywebview && window.pywebview.api) || null;

  function formatSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  // "4.8 MB → 612 KB · 87% smaller", built as nodes so file text is never parsed as HTML.
  function appendSizes(target, stats) {
    const before = stats && stats.input_bytes;
    const after = stats && stats.output_bytes;
    if (!before || !after) return;
    target.append(document.createTextNode(` · ${formatSize(before)} → ${formatSize(after)}`));
    const saved = Math.round((1 - after / before) * 100);
    if (saved > 0) {
      const strong = document.createElement('strong');
      strong.textContent = `${saved}% smaller`;
      target.append(document.createTextNode(' · '), strong);
    }
  }

  function scheduleClose() {
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => { if (!hovering) close(); else scheduleClose(); }, AUTO_CLOSE_MS);
  }

  function close() { const a = api(); if (a) a.close(); }

  window.Quick = {
    start({ label, files }) {
      $('quick-title').textContent = label;
      const first = fileName(files[0]);
      $('quick-file').textContent = files.length > 1 ? `${first} + ${files.length - 1} more` : first;
    },
    progress({ percent, status }) {
      $('quick-fill').style.width = `${Math.max(4, Math.min(100, percent || 0))}%`;
      $('quick-bar').setAttribute('aria-valuenow', String(Math.round(percent || 0)));
      if (status) $('quick-status').textContent = RunStats.cleanStatus(status);
    },
    done({ outputs, stats }) {
      card.dataset.phase = 'done';
      outputPath = (outputs && outputs[0]) || null;
      $('quick-fill').style.width = '100%';
      const count = (outputs || []).length;
      const what = count > 1 ? `${count} files saved next to the original` : `Saved as ${fileName(outputPath)}`;
      $('quick-status').textContent = what;
      appendSizes($('quick-status'), stats);
      $('quick-title').textContent = 'Done';
      $('quick-show').focus();
      scheduleClose();
    },
    failed({ message }) {
      card.dataset.phase = 'failed';
      $('quick-title').textContent = 'Could not finish';
      $('quick-status').textContent = RunStats.brand(message) || 'Something went wrong.';
      $('quick-dismiss').focus();
    }
  };

  $('quick-show').addEventListener('click', () => { const a = api(); if (a && outputPath) a.show_file(outputPath); });
  $('quick-dismiss').addEventListener('click', close);
  $('quick-close').addEventListener('click', () => { const a = api(); if (a) a.cancel_and_close(); });
  card.addEventListener('mouseenter', () => { hovering = true; });
  card.addEventListener('mouseleave', () => { hovering = false; });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { const a = api(); if (a) a.cancel_and_close(); } });
})();
