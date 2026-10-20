/**
 * Live preview for tools marked "output": "live" in the tools list: the result
 * sits on the tool screen and redraws while settings change. Nothing is written
 * until Save, which is an ordinary run into the user's chosen folder.
 */
const LivePreview = (() => {
  const REDRAW_DELAY_MS = 120;
  const SLOW_NOTE_MS = 250;
  let toolId = '';
  let root = null;
  let timer = null;
  let busy = false;
  let again = false;
  let saving = false;
  let images = [];
  let active = 0;

  const isLiveTool = (id) => (state.tools || []).some(t => t.id === id && t.output === 'live');

  function mount(id) {
    stop();
    toolId = isLiveTool(id) ? id : '';
    images = [];
    active = 0;
    if (!toolId) return;
    root = document.createElement('section');
    root.className = 'lp';
    root.hidden = true;
    root.setAttribute('aria-label', 'Live preview');
    root.innerHTML = `
      <div class="lp-head">
        <div class="lp-tabs" role="tablist"></div>
        <span class="lp-status" aria-live="polite"></span>
      </div>
      <div class="lp-stage"><img class="lp-image" alt=""></div>
      <p class="lp-foot"></p>`;
    root.querySelector('.lp-tabs').addEventListener('click', (e) => {
      const tab = e.target.closest('[data-index]');
      if (tab) paint(Number(tab.dataset.index));
    });
    document.getElementById('studio-stage-left')?.append(root);
  }

  function stop() {
    clearTimeout(timer);
    if (toolId) callBridge('stop_live_preview');
    toolId = '';
    root = null;
  }

  // Called after any file or setting change; quick typing collapses into one redraw.
  function refresh() {
    if (!toolId || !root) return;
    if (!state.selectedFiles.length) {
      root.hidden = true;
      images = [];
      callBridge('stop_live_preview');
      return;
    }
    root.hidden = false;
    root.querySelector('.lp-foot').textContent = state.selectedFiles.length > 1
      ? `Showing the first image. Save makes previews for all ${state.selectedFiles.length}.`
      : 'Nothing is saved until you press Save.';
    clearTimeout(timer);
    timer = setTimeout(draw, images.length ? REDRAW_DELAY_MS : 0);
  }

  async function draw() {
    if (busy) { again = true; return; }
    busy = true;
    const view = root;
    const status = view.querySelector('.lp-status');
    const slow = setTimeout(() => { status.textContent = images.length ? 'Updating…' : 'Drawing previews…'; }, images.length ? SLOW_NOTE_MS : 0);
    const result = await callBridge('live_preview', toolId, state.selectedFiles[0], { ...state.activeToolOptions });
    clearTimeout(slow);
    busy = false;
    if (view !== root) return;
    if (result && Array.isArray(result.images) && result.images.length) {
      images = result.images;
      status.textContent = '';
      paint(Math.min(active, images.length - 1));
    } else {
      status.textContent = (result && result.error) || 'Could not draw the preview.';
    }
    if (again) { again = false; draw(); }
  }

  function paint(index) {
    active = index;
    root.querySelector('.lp-tabs').innerHTML = images.map((img, i) => `
      <button type="button" role="tab" class="lp-tab${i === active ? ' is-active' : ''}"
        aria-selected="${i === active}" data-index="${i}">${escapeHtml(img.label)}</button>`).join('');
    const img = root.querySelector('.lp-image');
    img.src = images[active].data;
    img.alt = `${images[active].label} preview`;
    img.dataset.layout = images[active].label.toLowerCase();
  }

  // Save runs the engine for real; the screen stays put and a toast confirms.
  function startSave() { saving = true; }
  const isSaving = () => saving;

  function finishSave(outputs, error) {
    saving = false;
    if (error) return showToast(error, 'error');
    const dest = document.getElementById('studio-out-folder')?.value || state.defaultDownloads;
    const folder = String(dest).split(/[\\/]/).filter(Boolean).pop() || dest;
    showToast(`Saved ${outputs.length} preview${outputs.length === 1 ? '' : 's'} in ${folder}`, 'success');
  }

  return { isLiveTool, mount, stop, refresh, startSave, isSaving, finishSave };
})();
