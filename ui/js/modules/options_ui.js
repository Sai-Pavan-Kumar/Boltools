/**
 * Options UI: the shared building blocks for every tool's settings, so all
 * tools look and behave the same. Each control reports through one
 * data-action ("set-tool-option") with data-key / data-value; app.js stores
 * the value in state.activeToolOptions and re-renders the settings.
 */
(function () {
  function choice(key, current, { value, label, hint }) {
    const selected = String(current) === String(value);
    return `
      <button type="button" class="opt-choice${selected ? ' is-selected' : ''}" aria-pressed="${selected}"
        data-action="set-tool-option" data-key="${escapeAttr(key)}" data-value="${escapeAttr(value)}">
        <strong>${escapeHtml(label)}</strong>${hint ? `<span>${escapeHtml(hint)}</span>` : ''}
      </button>`;
  }

  // Few options, all visible at once: faster than a dropdown (Hick's law, one click).
  function segmented({ key, label, current, options }) {
    return `
      <div class="opt-field">
        <span class="opt-label">${escapeHtml(label)}</span>
        <div class="opt-segmented" style="--opt-count: ${options.length}">
          ${options.map(option => choice(key, current, option)).join('')}
        </div>
      </div>`;
  }

  function chips({ key, label, current, options, hint }) {
    return `
      <div class="opt-field">
        <span class="opt-label">${escapeHtml(label)}</span>
        <div class="opt-chips">
          ${options.map(option => choice(key, current, option)).join('')}
        </div>
        ${hint ? `<p class="opt-hint">${escapeHtml(hint)}</p>` : ''}
      </div>`;
  }

  const SIZE_LIMITS = [
    { value: 0, label: 'No limit' },
    { value: 100, label: 'Under 100 KB' },
    { value: 200, label: 'Under 200 KB' },
    { value: 500, label: 'Under 500 KB' },
    { value: 1024, label: 'Under 1 MB' }
  ];

  // Same control for PDFs and images: one mental model for "make it smaller".
  function compressGoal(options, kind) {
    const preset = options.preset || 'balanced';
    const target = Number(options.target_kb || 0);
    const presets = [
      { value: 'smallest', label: 'Smallest', hint: 'Tiny files' },
      { value: 'balanced', label: 'Balanced', hint: 'Recommended' },
      { value: 'best', label: 'Best', hint: kind === 'pdf' ? 'For printing' : 'Near original' }
    ];
    const limitHint = kind === 'pdf'
      ? 'For upload portals with a size limit. Text always stays sharp.'
      : 'Boltools finds the best quality that fits.';
    return (target ? '' : segmented({ key: 'preset', label: 'Goal', current: preset, options: presets }))
      + chips({ key: 'target_kb', label: 'Size limit', current: target, options: SIZE_LIMITS, hint: limitHint });
  }

  // Values arrive from data attributes as strings; numbers are stored as numbers.
  function parseValue(key, raw) {
    return key === 'target_kb' ? Number(raw) || 0 : raw;
  }

  window.OptionsUI = { segmented, chips, compressGoal, parseValue };
})();
