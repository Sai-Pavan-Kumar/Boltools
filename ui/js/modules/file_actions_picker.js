/**
 * Files dropped (or browsed) on Home: show only the actions that fit them, like
 * the right-click menu, and let the user pick. The list comes from the tools
 * list via the bridge, so new tools join without changes here.
 */
const FileActionsPicker = (() => {
  let pending = { files: [], actions: [] };

  const fileName = (path) => String(path).split(/[\\/]/).pop();
  const extOf = (path) => (fileName(path).split('.').pop() || '').toUpperCase().slice(0, 4);

  function optionButton(action, index) {
    return `
      <button type="button" data-action="pick-file-action" data-index="${index}"
        class="w-full p-3 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] text-left flex items-center justify-between gap-3 group transition-all cursor-pointer">
        <div>
          <div class="text-xs font-bold text-[var(--text-primary)] group-hover:text-[var(--brand-primary)]">${escapeHtml(action.label)}</div>
          <div class="text-[11px] text-[var(--text-secondary)]">${escapeHtml(action.tool_name)}</div>
        </div>
        ${getIcon('arrow-right', 'w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand-primary)]')}
      </button>`;
  }

  function emptyState() {
    return `
      <p class="text-xs text-[var(--text-secondary)]">None of your installed tools can open this type of file yet.</p>
      <button type="button" data-action="nav" data-view="tool_hub"
        class="w-full p-3 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--brand-primary)] text-xs font-bold text-[var(--brand-primary)] cursor-pointer">
        Browse the Tool Store
      </button>`;
  }

  async function open(files) {
    if (!files || !files.length) return;
    const actions = (await callBridge('get_file_actions', files)) || [];
    pending = { files: files.slice(), actions };
    const modal = document.getElementById('modal-file-action');
    const opts = document.getElementById('file-action-options');
    if (!modal || !opts) return;
    const first = fileName(files[0]);
    document.getElementById('file-action-title').innerText = files.length > 1 ? `${first} + ${files.length - 1} more` : first;
    document.getElementById('file-action-subtitle').innerText = files.length > 1 ? `${files.length} files` : '1 file';
    const icon = document.getElementById('file-action-icon');
    if (icon) {
      icon.className = 'w-8 h-8 rounded-md bg-[var(--surface-inset)] text-[var(--brand-primary)] flex items-center justify-center font-bold text-[10px] border border-[var(--border-subtle)] shrink-0';
      icon.innerText = extOf(files[0]);
    }
    opts.innerHTML = actions.length ? actions.map(optionButton).join('') : emptyState();
    modal.classList.remove('hidden');
  }

  // Opens the tool with the files and the action's settings already chosen.
  function pick(index) {
    const action = pending.actions[Number(index)];
    document.getElementById('modal-file-action')?.classList.add('hidden');
    if (!action) return;
    openToolWithFiles(action.tool_id, pending.files);
    if (action.options && Object.keys(action.options).length) {
      Object.assign(state.activeToolOptions, action.options);
      const optBox = document.getElementById('studio-options-box');
      if (optBox) optBox.innerHTML = renderToolSpecificOptions(state.activeToolId);
    }
  }

  return { open, pick };
})();
