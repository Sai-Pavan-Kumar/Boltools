/**
 * Run Stage: plays a tool's job inside the file area itself.
 *
 * The files the user added become document cards that act out the operation
 * (merge stacks them, compress squeezes, split fans out, convert re-labels),
 * and the finished file lands in the same spot with its actions. The point is
 * that the user watches *their* files being worked on, not an abstract bar.
 * Engine text and file names only reach the DOM through textContent.
 */
(function () {
  const MAX_CARDS = 5;
  const CARD_GAP_PX = 112;
  const STACK_DELAY_MS = 520;
  const ELAPSED_TICK_MS = 250;

  const MODE_BY_TOOL = {
    pdf_merge: 'merge',
    pdf_split: 'split',
    pdf_compress: 'compress',
    image_webp_compress: 'compress',
    video_compressor: 'compress',
    media_audio_extractor: 'extract',
    pdf_converter: 'convert',
    system_batch_rename: 'rename',
    subtitle_animator: 'subtitle'
  };

  const VERB_BY_MODE = {
    merge: 'Merging', split: 'Splitting', compress: 'Compressing', extract: 'Pulling audio from',
    convert: 'Converting', rename: 'Renaming', subtitle: 'Captioning', transform: 'Processing'
  };

  // Each tool acts out its own job; this is the extra scenery that sells it.
  const FX_BY_MODE = {
    compress: '<i class="th-clamp th-clamp-top"></i><i class="th-clamp th-clamp-bottom"></i>',
    extract: `<div class="th-wave">${'<i></i>'.repeat(9)}</div>`,
    subtitle: '<div class="th-caption"><i>Your</i><i>words,</i><i>on</i><i>screen</i></div>'
  };

  let root = null;
  let pane = null;
  let primaryButton = null;
  let toolId = '';
  let mode = 'transform';
  let shownPercent = 0;
  let targetPercent = 0;
  let tweenFrame = null;
  let elapsedTimer = null;
  let stackTimer = null;
  let startedAt = 0;
  let inputFiles = [];

  const $ = (sel) => (root ? root.querySelector(sel) : null);
  const fileNameOf = (path) => String(path || '').split(/[\\/]/).pop();
  const folderNameOf = (path) => String(path || '').split(/[\\/]/).slice(-2, -1)[0] || '';

  function template() {
    return `
      <div class="th-scene" aria-hidden="true">
        <div class="th-halo"></div>
        <div class="th-fx"></div>
        <div class="th-cards"></div>
        <div class="th-results"></div>
      </div>
      <div class="th-copy" aria-live="polite">
        <p class="th-title"></p>
        <p class="th-sub"><span class="th-pct rs-mono"></span><span class="th-elapsed">0:00</span></p>
      </div>
      <div class="th-stats"></div>
      <div class="th-actions"></div>
      <details class="th-log"><summary>Details</summary><div id="studio-log-box" class="th-log-box rs-mono"></div></details>
    `;
  }

  function setState(state) {
    if (!root) return;
    root.dataset.state = state;
    if (pane) pane.classList.toggle('th-on', state !== 'idle');
    if (primaryButton) primaryButton.hidden = state !== 'idle';
  }

  function stopTimers() {
    clearInterval(elapsedTimer);
    clearTimeout(stackTimer);
    cancelAnimationFrame(tweenFrame);
    elapsedTimer = stackTimer = tweenFrame = null;
  }

  function makeCard(path, tag = null) {
    const kind = FileTray.kindOf(path);
    const card = document.createElement('div');
    card.className = `th-card th-tone-${kind.tone}`;
    card.innerHTML = '<span class="th-fold"></span><span class="th-kind"></span><span class="th-lines"><i></i><i></i><i></i></span><span class="th-name"></span>';
    card.querySelector('.th-kind').textContent = tag || kind.label;
    card.querySelector('.th-name').textContent = fileNameOf(path);
    return card;
  }

  // Cards sit in a row first, then (for merge) slide into one slightly fanned stack.
  function placeCards(cards, layout) {
    const mid = (cards.length - 1) / 2;
    cards.forEach((card, index) => {
      const offset = index - mid;
      const stacked = layout === 'stack';
      card.style.setProperty('--x', `${stacked ? offset * 6 : offset * CARD_GAP_PX}px`);
      card.style.setProperty('--y', `${stacked ? -index * 4 : 0}px`);
      card.style.setProperty('--r', `${stacked ? offset * 4 : offset * 2}deg`);
      card.style.setProperty('--d', `${index * 60}ms`);
    });
  }

  function buildCards(files) {
    const shown = files.slice(0, MAX_CARDS);
    const cards = shown.map(path => makeCard(path));
    const hidden = files.length - shown.length;
    if (hidden > 0) {
      const more = document.createElement('span');
      more.className = 'th-more';
      more.textContent = `+${hidden}`;
      cards[cards.length - 1].appendChild(more);
    }
    $('.th-cards').replaceChildren(...cards);
    placeCards(cards, 'row');
    if (mode === 'merge' && cards.length > 1) {
      stackTimer = setTimeout(() => placeCards(cards, 'stack'), STACK_DELAY_MS);
    }
  }

  function formatElapsed(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, '0')}`;
  }

  function formatDuration(ms) {
    if (ms < 1000) return `${Math.max(1, Math.round(ms))} ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)} s`;
    return formatElapsed(ms);
  }

  // Eases toward the engine's number so bursty updates still read as one smooth climb.
  function renderPercent() {
    const delta = targetPercent - shownPercent;
    shownPercent = Math.abs(delta) < 0.4 ? targetPercent : shownPercent + delta * 0.18;
    const label = $('.th-pct');
    if (label) label.textContent = `${Math.round(shownPercent)}%`;
    tweenFrame = shownPercent === targetPercent ? null : requestAnimationFrame(renderPercent);
  }

  function setTitle(text) {
    const el = $('.th-title');
    if (!el || el.textContent === text) return;
    el.classList.remove('th-swap');
    void el.offsetWidth;
    el.textContent = text;
    el.classList.add('th-swap');
  }

  function cleanStatus(raw) {
    const text = String(raw || '').trim();
    // qpdf echoes temp paths ("qpdf: C:\...\temp.pdf: write progress: 51%"); users don't need those.
    if (/^qpdf:/i.test(text)) return 'Writing your file…';
    return text.length > 80 ? `${text.slice(0, 77)}…` : text;
  }

  function mount(container, id, startButton = null) {
    stopTimers();
    pane = container;
    primaryButton = startButton;
    toolId = id;
    mode = MODE_BY_TOOL[id] || 'transform';
    root = document.createElement('section');
    root.className = 'th';
    root.dataset.mode = mode;
    root.innerHTML = template();
    container.appendChild(root);
    setState('idle');
  }

  function start(files) {
    if (!root) return;
    stopTimers();
    shownPercent = targetPercent = 0;
    root.classList.add('th-indeterminate');
    $('.th-pct').textContent = '';
    $('.th-log-box').replaceChildren();
    $('.th-results').replaceChildren();
    $('.th-stats').replaceChildren();
    $('.th-fx').innerHTML = FX_BY_MODE[mode] || '';
    inputFiles = files.slice();
    renderActions([{ action: 'cancel-tool', label: 'Cancel', tone: 'quiet' }]);
    buildCards(files);
    const count = files.length;
    setTitle(`${VERB_BY_MODE[mode]} ${count > 1 ? `${count} files` : fileNameOf(files[0])}…`);
    startedAt = performance.now();
    elapsedTimer = setInterval(() => {
      const el = $('.th-elapsed');
      if (el) el.textContent = formatElapsed(performance.now() - startedAt);
    }, ELAPSED_TICK_MS);
    setState('running');
  }

  function progress(percent, status) {
    if (!root || root.dataset.state !== 'running') return;
    const indeterminate = percent === undefined || percent < 0;
    root.classList.toggle('th-indeterminate', indeterminate);
    if (!indeterminate) {
      targetPercent = Math.max(targetPercent, Math.min(100, percent));
      if (!tweenFrame) tweenFrame = requestAnimationFrame(renderPercent);
    }
    if (status && !/^(complete|initializing engine)/i.test(status)) setTitle(cleanStatus(status));
  }

  function log(message) {
    const box = $('.th-log-box');
    if (!box) return;
    const line = document.createElement('div');
    line.textContent = message;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  }

  window.RunStage = { mount, start, progress, log, complete, fail, reset };

  // ── Endings ────────────────────────────────────────────────────────────────
  function renderActions(buttons) {
    $('.th-actions').innerHTML = buttons.map(({ action, label, tone }) => `
      <button type="button" data-action="${action}" data-tool-id="${escapeAttr(toolId)}"
        class="th-btn th-btn-${tone}">${label}</button>`).join('');
  }

  const extOf = (path) => (fileNameOf(path).split('.').pop() || '').toUpperCase();

  function formatChange(outputs) {
    const from = extOf(inputFiles[0]);
    const to = extOf(outputs[0]);
    return from && to && from !== to ? `${from} → ${to}` : '';
  }

  // Numbers come from the engine or from the files on disk (bridge output_stats); never guessed.
  function buildStats(stats, outputs, elapsedMs) {
    const s = stats || {};
    const items = [];
    const before = s.orig_size || s.input_bytes;
    const after = s.new_size || s.output_bytes || s.total_bytes;
    const showsChange = before && after && mode === 'compress';
    if (after) items.push([showsChange ? 'Size' : 'Output', showsChange ? `${formatBytes(before)} → ${formatBytes(after)}` : formatBytes(after)]);
    if (mode === 'compress' && before && after) {
      items.push(['Saved', after < before ? `${Math.round((1 - after / before) * 100)}%` : 'Already small']);
    }
    const format = formatChange(outputs);
    if (format) items.push(['Format', format]);
    const pages = s.total_pages ?? s.output_pages;
    if (pages) items.push(['Pages', String(pages)]);
    if (outputs.length > 1) items.push(['Files', String(outputs.length)]);
    items.push(['Time', formatDuration(s.total_time_ms !== undefined ? s.total_time_ms : elapsedMs)]);
    return items;
  }

  function renderStats(items) {
    $('.th-stats').replaceChildren(...items.map(([label, value], index) => {
      const cell = document.createElement('div');
      cell.className = 'th-stat';
      cell.style.animationDelay = `${380 + index * 70}ms`;
      const strong = document.createElement('strong');
      strong.textContent = value;
      const caption = document.createElement('span');
      caption.textContent = label;
      cell.append(strong, caption);
      return cell;
    }));
  }

  function landResults(files) {
    const shown = files.slice(0, MAX_CARDS);
    const cards = shown.map(path => makeCard(path));
    cards.forEach(card => card.insertAdjacentHTML('beforeend', '<span class="th-check"></span>'));
    $('.th-results').replaceChildren(...cards);
    placeCards(cards, cards.length > 1 ? 'row' : 'stack');
  }

  function finish(state) {
    stopTimers();
    root.classList.remove('th-indeterminate');
    setState(state);
  }

  function complete({ outputs, stats }) {
    if (!root) return;
    const elapsedMs = performance.now() - startedAt;
    finish('done');
    const files = (Array.isArray(outputs) ? outputs : [outputs]).filter(Boolean);
    landResults(files);
    const folder = folderNameOf(files[0]);
    $('.th-pct').textContent = '';
    setTitle(files.length > 1 ? `${files.length} files ready` : 'Your file is ready');
    $('.th-elapsed').textContent = files.length > 1
      ? `Saved in ${folder || 'your output folder'}`
      : `${fileNameOf(files[0])}${folder ? ` · in ${folder}` : ''}`;
    renderStats(buildStats(stats, files, elapsedMs));
    renderActions([
      { action: 'open-output-file', label: files.length > 1 ? 'Open first file' : 'Open file', tone: 'primary' },
      { action: 'reveal-output-folder', label: 'Show in folder', tone: 'quiet' },
      { action: 'run-stage-reset', label: 'Start over', tone: 'quiet' }
    ]);
  }

  function fail(message) {
    if (!root) return;
    const text = String(message || '').replace(/^error:\s*/i, '').trim();
    const cancelled = /cancel/i.test(text);
    finish(cancelled ? 'stopped' : 'failed');
    $('.th-pct').textContent = '';
    setTitle(cancelled ? 'Stopped' : 'That didn’t work');
    $('.th-elapsed').textContent = cancelled
      ? 'Nothing was changed. Your files are safe.'
      : (text || 'The tool stopped unexpectedly. Your files are safe.');
    renderActions([
      { action: 'studio-execute', label: cancelled ? 'Run again' : 'Try again', tone: 'primary' },
      { action: 'run-stage-reset', label: 'Back to files', tone: 'quiet' }
    ]);
    if (!cancelled) log(`Error: ${text}`);
  }

  function reset() {
    if (root) finish('idle');
  }
})();
