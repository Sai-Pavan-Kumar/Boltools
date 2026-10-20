/**
 * Viewer for preview tools ("output": "preview" in the tools list): results open
 * here first and are saved only on request, so trying another image or title
 * never fills the user's folders with files.
 */
const PreviewViewer = (() => {
  let current = { paths: [], index: 0, cache: {} };

  const isPreviewTool = (toolId) => (state.tools || []).some(t => t.id === toolId && t.output === 'preview');

  // "My video - phone preview.png" -> "Phone"
  function tabLabel(path) {
    const name = String(path).split(/[\\/]/).pop().replace(/\.[^.]+$/, '');
    const part = name.includes(' - ') ? name.split(' - ').pop() : name;
    const word = part.replace(/\s*preview(\s*\(\d+\))?$/i, '').trim() || part;
    return word.charAt(0).toUpperCase() + word.slice(1);
  }

  function ensureRoot() {
    let root = document.getElementById('preview-viewer');
    if (root) return root;
    root = document.createElement('div');
    root.id = 'preview-viewer';
    root.className = 'pv-backdrop hidden';
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', 'Preview');
    root.innerHTML = `
      <div class="pv-panel">
        <header class="pv-head">
          <div class="pv-tabs" role="tablist"></div>
          <div class="pv-head-actions">
            <button type="button" class="pv-btn pv-btn-primary" data-pv="save">Save previews</button>
            <button type="button" class="pv-btn" data-pv="close">Close</button>
          </div>
        </header>
        <div class="pv-stage"><img class="pv-image" alt=""></div>
        <p class="pv-foot">Nothing is saved until you press Save previews. Close and try another image or title any time.</p>
      </div>`;
    root.addEventListener('click', onClick);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !root.classList.contains('hidden')) close();
    });
    document.body.appendChild(root);
    return root;
  }

  function renderTabs() {
    const tabs = ensureRoot().querySelector('.pv-tabs');
    tabs.innerHTML = current.paths.map((path, i) => `
      <button type="button" role="tab" class="pv-tab${i === current.index ? ' is-active' : ''}"
        aria-selected="${i === current.index}" data-pv="tab" data-index="${i}">${escapeHtml(tabLabel(path))}</button>`).join('');
  }

  async function showIndex(index) {
    current.index = index;
    renderTabs();
    const img = ensureRoot().querySelector('.pv-image');
    const path = current.paths[index];
    img.alt = `${tabLabel(path)} preview`;
    if (!current.cache[path]) current.cache[path] = await callBridge('read_preview_image', path);
    if (current.paths[current.index] === path) img.src = current.cache[path] || '';
  }

  function show(paths) {
    current = { paths: paths.slice(), index: 0, cache: {} };
    ensureRoot().classList.remove('hidden');
    showIndex(0);
    ensureRoot().querySelector('[data-pv="close"]').focus();
  }

  function close() {
    document.getElementById('preview-viewer')?.classList.add('hidden');
  }

  async function save() {
    const dest = document.getElementById('studio-out-folder')?.value || state.defaultDownloads;
    const result = await callBridge('save_previews', current.paths, dest);
    if (result && result.saved && result.saved.length) {
      state.lastOutputFile = result.saved[0];
      showToast(`Saved ${result.saved.length} previews in ${String(dest).split(/[\\/]/).pop() || dest}`, 'success');
    } else {
      showToast((result && result.error) || 'Could not save the previews.', 'error');
    }
  }

  function onClick(e) {
    if (e.target.id === 'preview-viewer') return close();
    const btn = e.target.closest('[data-pv]');
    if (!btn) return;
    if (btn.dataset.pv === 'tab') showIndex(Number(btn.dataset.index));
    else if (btn.dataset.pv === 'save') save();
    else if (btn.dataset.pv === 'close') close();
  }

  return { isPreviewTool, show, close };
})();
