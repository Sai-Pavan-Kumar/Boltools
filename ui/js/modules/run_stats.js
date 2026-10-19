/**
 * Run Stats: turns what a finished run produced into the chips on the result card.
 * Numbers come from the engine or from files measured on disk by the bridge
 * (src/core/output_stats.py); nothing here is estimated.
 */
(function () {
  const fileNameOf = (path) => String(path || '').split(/[\\/]/).pop();
  const extOf = (path) => (fileNameOf(path).split('.').pop() || '').toUpperCase();

  function formatDuration(ms) {
    if (ms < 1000) return `${Math.max(1, Math.round(ms))} ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)} s`;
    const totalSeconds = Math.floor(ms / 1000);
    return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, '0')}`;
  }

  function formatChange(inputs, outputs) {
    const from = extOf(inputs[0]);
    const to = extOf(outputs[0]);
    return from && to && from !== to ? `${from} → ${to}` : '';
  }

  function build({ stats, outputs, inputs, mode, elapsedMs }) {
    const s = stats || {};
    const items = [];
    const before = s.orig_size || s.input_bytes;
    const after = s.new_size || s.output_bytes || s.total_bytes;
    // Before/after size only means something when shrinking is the point of the tool.
    const showsChange = before && after && mode === 'compress';
    if (after) items.push([showsChange ? 'Size' : 'Output', showsChange ? `${formatBytes(before)} → ${formatBytes(after)}` : formatBytes(after)]);
    if (showsChange) items.push(['Saved', after < before ? `${Math.round((1 - after / before) * 100)}%` : 'Already small']);
    const format = formatChange(inputs, outputs);
    if (format) items.push(['Format', format]);
    const pages = s.total_pages ?? s.output_pages;
    if (pages) items.push(['Pages', String(pages)]);
    if (outputs.length > 1) items.push(['Files', String(outputs.length)]);
    items.push(['Time', formatDuration(s.total_time_ms !== undefined ? s.total_time_ms : elapsedMs)]);
    return items;
  }

  // The engine picks "name (1).pdf" when the name is taken; say so instead of letting it surprise.
  function renameNote(requestedName, actualPath) {
    const stemOf = (name) => name.replace(/\.[a-z0-9]+$/, '');
    const wanted = stemOf(String(requestedName || '').trim().toLowerCase());
    const got = stemOf(fileNameOf(actualPath).toLowerCase());
    // Only "name (1)" style results mean the engine had to avoid an existing file.
    if (!wanted || !got.startsWith(`${wanted} (`)) return '';
    return `A file named ${requestedName} already existed, so this one got a number.`;
  }

  // RULES.md section 2: library names never reach the UI, whatever an engine prints.
  const BRANDED_NAMES = [
    [/ffmpeg|ffprobe/gi, 'Boltools Media Engine'],
    [/\b(qpdf|pikepdf|pypdfium2|pdfium|pymupdf|pypdf|fitz)\b/gi, 'PDF Document Core'],
    [/\b(pillow|PIL)\b/gi, 'Boltools Image Core']
  ];

  function brand(raw) {
    return BRANDED_NAMES.reduce((text, [pattern, name]) => text.replace(pattern, name), String(raw || ''));
  }

  function cleanStatus(raw) {
    const text = String(raw || '').trim();
    // qpdf echoes temp paths ("qpdf: C:\...\temp.pdf: write progress: 51%"); users don't need those.
    if (/^qpdf:/i.test(text)) return 'Writing your file…';
    const branded = brand(text);
    return branded.length > 80 ? `${branded.slice(0, 77)}…` : branded;
  }

  function statCells(items) {
    return items.map(([label, value], index) => {
      const cell = document.createElement('div');
      cell.className = 'th-stat';
      cell.style.animationDelay = `${380 + index * 70}ms`;
      const strong = document.createElement('strong');
      strong.textContent = value;
      const caption = document.createElement('span');
      caption.textContent = label;
      cell.append(strong, caption);
      return cell;
    });
  }

  function failedRows(failed) {
    return failed.map(({ file, reason }) => {
      const row = document.createElement('div');
      row.className = 'th-failed-row';
      const name = document.createElement('strong');
      name.textContent = fileNameOf(file);
      const why = document.createElement('span');
      why.textContent = brand(reason);
      row.append(name, why);
      return row;
    });
  }

  window.RunStats = { build, renameNote, brand, cleanStatus, statCells, failedRows };
})();
