/**
 * File Previews: show the result before anything runs, for tools where the
 * outcome is not obvious from the settings alone.
 *   Split  -> a page strip with the cut lines, "Makes 3 files"
 *   Rename -> a Now / After table
 * The rules here mirror the engines exactly (pdf_studio split ranges in
 * main.rs, batch_renamer/engine.py); change them together.
 */
(function () {
  const MAX_PAGES_SHOWN = 60;
  const MAX_RENAME_ROWS = 8;

  function splitGroups(totalPages, options) {
    const mode = options.split_mode || 'each_page';
    if (mode === 'each_page' || mode === 'every_n') {
      const size = mode === 'each_page' ? 1 : Math.max(1, parseInt(options.every_n, 10) || 1);
      const groups = [];
      for (let start = 1; start <= totalPages; start += size) groups.push([start, Math.min(totalPages, start + size - 1)]);
      return groups;
    }
    return String(options.ranges || '1-').split(',').map(part => part.trim()).filter(Boolean).flatMap(part => {
      const dash = part.indexOf('-');
      if (dash === -1) {
        const page = parseInt(part, 10);
        return page >= 1 && page <= totalPages ? [[page, page]] : [];
      }
      const start = parseInt(part.slice(0, dash), 10) || 1;
      const endText = part.slice(dash + 1).trim();
      const end = Math.min(totalPages, endText ? (parseInt(endText, 10) || totalPages) : totalPages);
      return start <= end && start <= totalPages ? [[start, end]] : [];
    });
  }

  function renderSplit(container, pages, options) {
    const groups = splitGroups(pages, options);
    const cuts = new Set(groups.map(([, end]) => end).filter(end => end < pages));
    const strip = document.createElement('div');
    strip.className = 'fp-strip';
    for (let page = 1; page <= Math.min(pages, MAX_PAGES_SHOWN); page += 1) {
      const sheet = document.createElement('span');
      sheet.className = 'fp-page';
      sheet.classList.toggle('fp-unused', !groups.some(([s, e]) => page >= s && page <= e));
      sheet.textContent = String(page);
      strip.append(sheet);
      if (cuts.has(page)) strip.append(Object.assign(document.createElement('span'), { className: 'fp-cut' }));
    }
    const caption = document.createElement('p');
    caption.className = 'fp-caption';
    caption.textContent = groups.length
      ? `Makes ${groups.length} file${groups.length === 1 ? '' : 's'}. Blue lines show the cuts.`
      : 'These page numbers are not in this PDF. Check the ranges.';
    container.replaceChildren(caption, strip);
    return groups.length;
  }

  function renamed(path, index, options) {
    const base = String(path).split(/[\\/]/).pop();
    const dot = base.lastIndexOf('.');
    const name = dot > 0 ? base.slice(0, dot) : base;
    const ext = dot > 0 ? base.slice(dot) : '';
    const rule = options.rule || 'Add Suffix';
    const text1 = options.text1 ?? '_v1';
    let next = name;
    if (rule.includes('Add Prefix')) next = `${text1}${name}`;
    else if (rule.includes('Add Suffix')) next = `${name}${text1}`;
    else if (rule.includes('Sequential Numbering')) next = `${name}_${String(index + 1).padStart(2, '0')}`;
    else if (rule.includes('Find & Replace')) next = text1 ? name.split(text1).join(options.text2 || '') : name;
    else if (rule.includes('Lowercase')) next = name.toLowerCase();
    else if (rule.includes('UPPERCASE')) next = name.toUpperCase();
    return { from: base, to: `${next}${ext}` };
  }

  function renderRename(container, files, options) {
    const table = document.createElement('div');
    table.className = 'fp-table';
    const head = document.createElement('div');
    head.className = 'fp-row fp-head';
    head.innerHTML = '<span>Now</span><span>After</span>';
    table.append(head);
    files.slice(0, MAX_RENAME_ROWS).forEach((path, index) => {
      const { from, to } = renamed(path, index, options);
      const row = document.createElement('div');
      row.className = 'fp-row';
      const before = document.createElement('span');
      before.textContent = from;
      const after = document.createElement('strong');
      after.textContent = to;
      row.classList.toggle('fp-same', from === to);
      row.append(before, after);
      table.append(row);
    });
    const caption = document.createElement('p');
    caption.className = 'fp-caption';
    const more = files.length - MAX_RENAME_ROWS;
    caption.textContent = `Preview. Nothing is renamed until you press the button.${more > 0 ? ` ${more} more not shown.` : ''}`;
    container.replaceChildren(caption, table);
  }

  // Returns a better Start label when the preview knows the real outcome, else ''.
  function render(container, toolId, files, options, meta) {
    if (!container) return '';
    if (toolId === 'pdf_split' && files.length === 1 && meta[files[0]] && meta[files[0]].pages) {
      const count = renderSplit(container, meta[files[0]].pages, options);
      if (count > 1) return `Split into ${count} files`;
      // One range means pulling pages out, so the button should say exactly that.
      const pages = FilePreviews.splitGroups(meta[files[0]].pages, options).reduce((sum, [start, end]) => sum + end - start + 1, 0);
      return count === 1 ? `Extract ${pages} page${pages === 1 ? '' : 's'}` : '';
    }
    if (toolId === 'system_batch_rename' && files.length) {
      renderRename(container, files, options);
      return '';
    }
    container.replaceChildren();
    return '';
  }

  window.FilePreviews = { render, splitGroups };
})();
