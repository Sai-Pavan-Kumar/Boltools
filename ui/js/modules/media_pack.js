/**
 * The one-time media pack download, offered the first time a video or audio tool runs.
 * Python side: src/core/media_pack.py (download + checks) and media_pack_api.py (bridge).
 */
const MediaPack = (() => {
  const MARKER = 'MEDIA_PACK_NEEDED:';
  let waiting = null; // resolve() of the run that is waiting for the pack

  const toolNeedsPack = (toolId) =>
    ((state.tools || []).find(t => t.id === toolId)?.needs || []).includes('media_engine');

  function ensureModal() {
    let modal = document.getElementById('media-pack');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'media-pack';
    modal.className = 'idt-backdrop hidden';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'mpk-title');
    modal.innerHTML = '<div class="idt-panel"></div>';
    modal.addEventListener('click', onClick);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden') && !modal.dataset.busy) close(false);
    });
    document.body.appendChild(modal);
    return modal;
  }

  function render(html, busy = false) {
    const modal = ensureModal();
    modal.dataset.busy = busy ? '1' : '';
    modal.querySelector('.idt-panel').innerHTML = html;
    modal.classList.remove('hidden');
    (modal.querySelector('.idt-btn-primary') || modal.querySelector('.idt-btn'))?.focus();
  }

  function offer(status, error = '') {
    const size = status.size_bytes ? InstallDetails.formatBytes(status.size_bytes) : '';
    const body = status.available
      ? `Video and audio tools need the media pack. It downloads once${size ? ` (${size})` : ''}, then works offline.`
      : 'The media pack is not available yet. Please check your internet connection and try again in a moment.';
    render(`
      <h3 class="idt-title" id="mpk-title">One-time download: media pack</h3>
      <p class="idt-total">${escapeHtml(body)}</p>
      ${error ? `<p class="mpk-error" role="alert">${escapeHtml(error)}</p>` : ''}
      <div class="idt-actions">
        <button type="button" class="idt-btn" data-mpk="close">Not now</button>
        ${status.available ? `<button type="button" class="idt-btn idt-btn-primary" data-mpk="download">${error ? 'Try again' : `Download${size ? ` ${size}` : ''}`}</button>` : ''}
      </div>`);
  }

  function showProgress(percent, label) {
    const bar = document.getElementById('mpk-bar');
    if (bar) {
      bar.style.transform = `scaleX(${Math.max(0, Math.min(100, percent)) / 100})`;
      document.getElementById('mpk-status').textContent = `${label} · ${Math.round(percent)}%`;
      document.getElementById('mpk-track').setAttribute('aria-valuenow', String(Math.round(percent)));
      return;
    }
    render(`
      <h3 class="idt-title" id="mpk-title">Getting the media pack</h3>
      <p class="idt-total">Checked for safety before it is used. You can keep this window open.</p>
      <div class="mpk-track" id="mpk-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
        <div class="mpk-bar" id="mpk-bar"></div>
      </div>
      <p class="mpk-status" id="mpk-status" aria-live="polite">Starting · 0%</p>
      <div class="idt-actions">
        <button type="button" class="idt-btn" data-mpk="cancel">Cancel</button>
      </div>`, true);
  }

  function close(ready) {
    document.getElementById('media-pack')?.classList.add('hidden');
    const resolve = waiting;
    waiting = null;
    if (resolve) resolve(ready);
  }

  async function onClick(e) {
    const action = e.target.closest('[data-mpk]')?.dataset.mpk;
    if (e.target.id === 'media-pack' && !e.currentTarget.dataset.busy) return close(false);
    if (action === 'close') close(false);
    if (action === 'cancel') await callBridge('cancel_media_pack');
    if (action === 'download') {
      showProgress(0, 'Starting');
      const started = await callBridge('install_media_pack');
      if (!started) offer(await status(), 'A download is already running or could not start. Please try again.');
    }
  }

  const status = async () => (await callBridge('get_media_pack_status')) || { ready: false, available: false };

  /** Resolves true when the tool can run now; shows the download step when the pack is missing. */
  async function ensureReady(toolId) {
    if (!toolNeedsPack(toolId)) return true;
    const current = await status();
    if (current.ready) return true;
    return new Promise((resolve) => {
      waiting = resolve;
      if (current.busy) showProgress(0, 'Downloading');
      else offer(current);
    });
  }

  const isPackMessage = (msg) => typeof msg === 'string' && msg.startsWith(MARKER);
  const cleanMessage = (msg) => (isPackMessage(msg) ? msg.slice(MARKER.length).trim() : msg);

  window.onMediaPackProgress = ({ percent, status: label }) => showProgress(percent, label);
  window.onMediaPackDone = async (result) => {
    if (result.ok) {
      if (typeof showToast === 'function') showToast('Media pack ready. Video and audio tools now work offline.', 'success');
      // Tool Store cards read "already on this PC" from the catalog summary.
      const summary = await callBridge('get_catalog_summary');
      if (Array.isArray(summary)) state.tools = summary;
      return close(true);
    }
    offer(await status(), result.error);
  };

  return { ensureReady, isPackMessage, cleanMessage };
})();
