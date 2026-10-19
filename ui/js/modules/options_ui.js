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
    { value: '0', label: 'No limit' },
    { value: '100', label: 'Under 100 KB' },
    { value: '200', label: 'Under 200 KB' },
    { value: '500', label: 'Under 500 KB' },
    { value: '1024', label: 'Under 1 MB' }
  ];

  // Exam and government upload forms ask for a window, not just a maximum.
  const PORTAL_WINDOWS = [
    { value: '20-50', label: '20–50 KB' },
    { value: '10-20', label: '10–20 KB' }
  ];

  const SHAPES = [
    { value: 'original', label: 'Original' },
    { value: 'square', label: 'Square' },
    { value: 'passport', label: 'Passport' },
    { value: '4:3', label: '4:3' },
    { value: '16:9', label: '16:9' }
  ];

  function sizeWindowOf(options) {
    const max = Number(options.target_kb || 0);
    const min = Number(options.min_kb || 0);
    return min ? `${min}-${max}` : String(max);
  }

  // Same control for PDFs and images: one mental model for "make it smaller".
  function compressGoal(options, kind) {
    const preset = options.preset || 'balanced';
    const target = Number(options.target_kb || 0);
    const limits = kind === 'image' ? SIZE_LIMITS.concat(PORTAL_WINDOWS) : SIZE_LIMITS;
    const presets = [
      { value: 'smallest', label: 'Smallest', hint: 'Tiny files' },
      { value: 'balanced', label: 'Balanced', hint: 'Recommended' },
      { value: 'best', label: 'Best', hint: kind === 'pdf' ? 'For printing' : 'Near original' }
    ];
    const limitHint = kind === 'pdf'
      ? 'For upload portals with a size limit. Text always stays sharp.'
      : 'Boltools finds the best quality that fits. 20–50 KB and 10–20 KB match most exam photo and signature uploads.';
    const goal = target ? '' : segmented({ key: 'preset', label: 'Goal', current: preset, options: presets });
    const size = chips({ key: 'size_window', label: 'Size limit', current: sizeWindowOf(options), options: limits, hint: limitHint });
    if (kind !== 'image') return goal + size;
    const format = segmented({
      key: 'format', label: 'Format', current: options.format || 'webp',
      options: [{ value: 'webp', label: 'WebP', hint: 'Smallest' }, { value: 'jpg', label: 'JPG', hint: 'Works on every portal' }]
    });
    const shape = chips({ key: 'shape', label: 'Shape', current: options.shape || 'original', options: SHAPES, hint: 'Crops from the centre. Passport is 3.5 × 4.5.' });
    return goal + size + moreOptions(options, format + shape);
  }

  // Rarely needed settings stay folded (Hick's law); the summary shows what is chosen.
  function moreOptions(options, body) {
    const formatLabel = (options.format || 'webp') === 'jpg' ? 'JPG' : 'WebP';
    const shapeLabel = (SHAPES.find(s => s.value === (options.shape || 'original')) || SHAPES[0]).label;
    return `
      <div class="opt-more${options._more ? ' is-open' : ''}">
        <button type="button" class="opt-more-toggle" aria-expanded="${Boolean(options._more)}"
          data-action="set-tool-option" data-key="_more" data-value="${options._more ? '' : '1'}">
          <span>More options</span><span class="opt-more-summary">${escapeHtml(formatLabel)} · ${escapeHtml(shapeLabel)}</span>
        </button>
        ${options._more ? `<div class="opt-more-body">${body}</div>` : ''}
      </div>`;
  }

  // Values arrive from data attributes as strings. "20-50" sets a min and max together.
  function apply(options, key, raw) {
    if (key === 'size_window') {
      const [first, second] = String(raw).split('-').map(Number);
      options.min_kb = second ? first : 0;
      options.target_kb = second || first || 0;
      return;
    }
    options[key] = raw;
  }

  window.OptionsUI = { segmented, chips, compressGoal, apply };
})();
