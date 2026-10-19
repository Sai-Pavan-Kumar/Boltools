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
    const wanted = String(requestedName || '').trim().toLowerCase();
    const got = fileNameOf(actualPath).toLowerCase();
    if (!wanted || !got || got === wanted || got === `${wanted}.pdf`) return '';
    const stem = wanted.replace(/\.[a-z0-9]+$/, '');
    return got.startsWith(stem) ? `A file named ${requestedName} already existed, so this one got a number.` : '';
  }

  window.RunStats = { build, renameNote };
})();
