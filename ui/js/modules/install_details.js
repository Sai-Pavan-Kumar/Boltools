/**
 * Tool Hub: what installing a tool puts on this PC, before the user installs.
 * The plan comes from src/core/install_plan.py through the catalog summary.
 */
const InstallDetails = (() => {
  const STATUS_TEXT = {
    download: 'Downloads now',
    present: 'Already on this PC, nothing to download',
    built_in: 'Built into Boltools',
    missing: 'Needed, not on this PC yet'
  };

  function formatBytes(bytes) {
    if (!bytes) return '0 KB';
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  const toolOf = (toolId) => (state.tools || []).find(t => t.id === toolId) || null;

  // One line for the card: the download size plus the shared part that matters most.
  function summaryLine(tool) {
    const plan = tool.install_plan;
    if (!plan) return '';
    const shared = plan.parts.slice(1);
    const missing = shared.find(p => p.status === 'missing');
    const present = shared.find(p => p.status === 'present');
    const size = plan.download_bytes ? `${formatBytes(plan.download_bytes)} download` : 'Nothing to download';
    if (missing) return `${size} · also needs ${missing.name}`;
    if (present) return `${size} · ${present.name} already on this PC`;
    return size;
  }

  function partRow(part) {
    const size = part.bytes ? ` · ${formatBytes(part.bytes)}` : '';
    return `
      <li class="idt-part idt-${escapeAttr(part.status)}">
        <strong>${escapeHtml(part.name)}</strong>
        <span>${escapeHtml(STATUS_TEXT[part.status] || part.status)}${escapeHtml(size)}</span>
        ${part.hint ? `<em>${escapeHtml(part.hint)}</em>` : ''}
      </li>`;
  }

  function ensureModal() {
    let modal = document.getElementById('install-details');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'install-details';
    modal.className = 'idt-backdrop hidden';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.innerHTML = '<div class="idt-panel"></div>';
    modal.addEventListener('click', (e) => {
      if (e.target === modal || e.target.closest('[data-idt="close"]')) modal.classList.add('hidden');
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') modal.classList.add('hidden'); });
    document.body.appendChild(modal);
    return modal;
  }

  function show(toolId) {
    const tool = toolOf(toolId);
    if (!tool || !tool.install_plan) return;
    const modal = ensureModal();
    const plan = tool.install_plan;
    modal.querySelector('.idt-panel').innerHTML = `
      <h3 class="idt-title">What installing ${escapeHtml(tool.name)} adds</h3>
      <p class="idt-total">${plan.download_bytes ? `Total download: <strong>${formatBytes(plan.download_bytes)}</strong>` : 'Nothing new to download.'}</p>
      <ul class="idt-parts">${plan.parts.map(partRow).join('')}</ul>
      <div class="idt-actions">
        <button type="button" class="idt-btn" data-idt="close">Close</button>
        <button type="button" class="idt-btn idt-btn-primary" data-action="install-tool" data-tool-id="${escapeAttr(tool.id)}" data-idt="close">Install</button>
      </div>`;
    modal.classList.remove('hidden');
    modal.querySelector('.idt-btn-primary').focus();
  }

  return { summaryLine, show, formatBytes };
})();
