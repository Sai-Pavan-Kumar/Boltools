/**
 * Tool settings described by the tools list, so a new tool ships through
 * Tool Store with its own settings screen and no app update.
 *
 * A tool entry may carry:
 *   settings: [
 *     { key, type: "text",   label, placeholder?, default?, max? },
 *     { key, type: "choice", label, default, choices: [{ value, label, hint? }] }
 *   ]
 *   ux:      { verb, noun, limits, before, namesOutput, minFiles, maxFiles }  (see tool_ux.js)
 *   accepts: ["jpg", "png", ...]  (file picker filter)
 * Older tools keep their hand-written screens in app.js; this is the fallback.
 */
const ToolSettings = (() => {
  const toolOf = (toolId) => (state.tools || []).find(t => t.id === toolId) || null;
  const schemaOf = (toolId) => {
    const tool = toolOf(toolId);
    return tool && Array.isArray(tool.settings) ? tool.settings : [];
  };

  function defaults(toolId) {
    const values = {};
    schemaOf(toolId).forEach(field => {
      values[field.key] = field.default ?? (field.type === 'choice' ? field.choices?.[0]?.value : '');
    });
    return values;
  }

  function textField(field, value) {
    const max = Number(field.max) > 0 ? ` maxlength="${Number(field.max)}"` : '';
    return `
      <div class="opt-field">
        <label class="opt-label" for="setting-${escapeAttr(field.key)}">${escapeHtml(field.label || field.key)}</label>
        <input id="setting-${escapeAttr(field.key)}" class="opt-input" type="text"${max}
          data-action="set-tool-text" data-key="${escapeAttr(field.key)}"
          placeholder="${escapeAttr(field.placeholder || '')}" value="${escapeAttr(value ?? '')}">
      </div>`;
  }

  function render(toolId, options) {
    return schemaOf(toolId).map(field => {
      const value = options[field.key];
      if (field.type === 'choice') {
        return OptionsUI.segmented({ key: field.key, label: field.label || field.key, current: value, options: field.choices || [] });
      }
      return textField(field, value);
    }).join('');
  }

  // "Images (*.jpg;*.png)" for the Windows file picker, from the tool's accepted types.
  function fileFilter(toolId) {
    const accepts = (toolOf(toolId)?.accepts || []).filter(ext => ext !== '*');
    if (!accepts.length) return ['All Files (*.*)'];
    return [`Supported files (${accepts.map(ext => `*.${ext}`).join(';')})`, 'All Files (*.*)'];
  }

  const ux = (toolId) => toolOf(toolId)?.ux || null;

  return { defaults, render, fileFilter, ux };
})();
