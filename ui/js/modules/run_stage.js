/**
 * Run Stage: the part of a tool screen that shows a job from "ready" to "done".
 *
 * Replaces the old progress bar + log box. One component for every tool, so a
 * run feels the same whether it merges PDFs or extracts audio. Owns its own
 * DOM; app.js only calls mount / start / progress / log / complete / fail.
 * Everything engine-provided is written with textContent (file names are user data).
 */
(function () {
  const RING_RADIUS = 52;
  const RING_LENGTH = 2 * Math.PI * RING_RADIUS;
  const ELAPSED_TICK_MS = 250;

  let root = null;
  let shownPercent = 0;
  let targetPercent = 0;
  let tweenFrame = null;
  let elapsedTimer = null;
  let startedAt = 0;
  let toolIdForRetry = '';
  let primaryButton = null;

  const $ = (sel) => (root ? root.querySelector(sel) : null);

  function template() {
    return `
      <div class="rs-idle">
        <span class="rs-summary"><span id="studio-summary-count">0 files</span><span class="rs-dot"></span><span id="studio-summary-size" class="rs-mono">0 B</span></span>
        <span class="rs-local" title="Your files are processed by this computer and never uploaded">
          <span class="rs-local-pulse"></span>Stays on this PC
        </span>
      </div>

      <div class="rs-active" aria-live="polite">
        <div class="rs-orb">
          <svg viewBox="0 0 120 120" class="rs-ring" aria-hidden="true">
            <circle class="rs-ring-track" cx="60" cy="60" r="${RING_RADIUS}"></circle>
            <circle class="rs-ring-fill" cx="60" cy="60" r="${RING_RADIUS}"
              stroke-dasharray="${RING_LENGTH}" stroke-dashoffset="${RING_LENGTH}"></circle>
            <path class="rs-check" d="M41 61 l13 13 l26 -28"></path>
            <path class="rs-cross" d="M46 46 L74 74 M74 46 L46 74"></path>
          </svg>
          <span class="rs-orbit" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="rs-pct rs-mono">0<small>%</small></span>
        </div>
        <div class="rs-copy">
          <p class="rs-status">Getting ready…</p>
          <p class="rs-sub"><span class="rs-elapsed rs-mono">0:00</span><span class="rs-dot"></span><span class="rs-sub-text">Working on this PC</span></p>
        </div>
        <button type="button" data-action="cancel-tool" class="rs-btn rs-btn-quiet rs-cancel">Cancel</button>
      </div>

      <div class="rs-result" aria-live="polite">
        <p class="rs-result-title"></p>
        <p class="rs-result-sub"></p>
        <div class="rs-stats"></div>
        <div class="rs-actions"></div>
      </div>

      <details class="rs-log">
        <summary>Details</summary>
        <div id="studio-log-box" class="rs-log-box rs-mono"></div>
      </details>
    `;
  }

  // The tool's own start button hides outside "idle": one clear next step at a time.
  function setState(state) {
    if (root) root.dataset.state = state;
    if (primaryButton) primaryButton.hidden = state !== 'idle';
  }

  function formatElapsed(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(totalSeconds % 60).padStart(2, '0');
    return `${minutes}:${seconds}`;
  }

  function formatDuration(ms) {
    if (ms < 1000) return `${Math.max(1, Math.round(ms))} ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)} s`;
    return formatElapsed(ms);
  }

  function stopTimers() {
    clearInterval(elapsedTimer);
    cancelAnimationFrame(tweenFrame);
    elapsedTimer = null;
    tweenFrame = null;
  }

  // The number eases toward the engine's value instead of jumping, so bursts of
  // updates (or a single 5% -> 100% leap on fast jobs) still read as smooth motion.
  function renderPercent() {
    const delta = targetPercent - shownPercent;
    shownPercent = Math.abs(delta) < 0.4 ? targetPercent : shownPercent + delta * 0.18;
    const fill = $('.rs-ring-fill');
    const label = $('.rs-pct');
    if (fill) fill.style.strokeDashoffset = String(RING_LENGTH * (1 - shownPercent / 100));
    if (label) label.firstChild.textContent = String(Math.round(shownPercent));
    tweenFrame = shownPercent === targetPercent ? null : requestAnimationFrame(renderPercent);
  }

  function setTarget(percent) {
    targetPercent = Math.max(targetPercent, Math.min(100, percent));
    if (!tweenFrame) tweenFrame = requestAnimationFrame(renderPercent);
  }

  // Cross-fades the status line so rapid engine messages don't flicker.
  function setStatus(text) {
    const el = $('.rs-status');
    if (!el || el.textContent === text) return;
    el.classList.remove('rs-swap');
    void el.offsetWidth;
    el.textContent = text;
    el.classList.add('rs-swap');
  }

  function cleanStatus(raw) {
    // Engines echo tool-internal prefixes ("qpdf: C:\...\temp.pdf: write progress: 51%").
    const text = String(raw || '').trim();
    if (/^qpdf:/i.test(text)) return 'Writing your file…';
    return text.length > 90 ? `${text.slice(0, 87)}…` : text;
  }

  function mount(container, toolId, startButton = null) {
    primaryButton = startButton;
    stopTimers();
    root = document.createElement('section');
    root.className = 'rs';
    root.innerHTML = template();
    container.replaceChildren(root);
    toolIdForRetry = toolId;
    setState('idle');
  }

  function start(fileCount) {
    if (!root) return;
    stopTimers();
    shownPercent = 0;
    targetPercent = 0;
    renderPercent();
    $('.rs-log-box').replaceChildren();
    root.classList.remove('rs-indeterminate');
    setStatus(fileCount > 1 ? `Getting ${fileCount} files ready…` : 'Getting your file ready…');
    startedAt = performance.now();
    elapsedTimer = setInterval(() => {
      const el = $('.rs-elapsed');
      if (el) el.textContent = formatElapsed(performance.now() - startedAt);
    }, ELAPSED_TICK_MS);
    setState('running');
  }

  function progress(percent, status) {
    if (!root || root.dataset.state !== 'running') return;
    const indeterminate = percent === undefined || percent < 0;
    root.classList.toggle('rs-indeterminate', indeterminate);
    if (!indeterminate) setTarget(percent);
    if (status) setStatus(cleanStatus(status));
  }

  function log(message) {
    const box = $('.rs-log-box');
    if (!box) return;
    const line = document.createElement('div');
    line.textContent = message;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  }

  function fileNameOf(path) {
    return String(path || '').split(/[\\/]/).pop();
  }

  function folderNameOf(path) {
    const parts = String(path || '').split(/[\\/]/);
    return parts.length > 1 ? parts[parts.length - 2] : '';
  }

  // Only facts the engine actually reported are shown; no invented numbers.
  function buildStats(stats, elapsedMs) {
    const items = [];
    const timeMs = stats && stats.total_time_ms !== undefined ? stats.total_time_ms : elapsedMs;
    items.push(['Time', formatDuration(timeMs)]);
    if (!stats) return items;
    if (stats.orig_size && stats.new_size) {
      const saved = Math.max(0, stats.orig_size - stats.new_size);
      items.push(['Size', `${formatBytes(stats.orig_size)} → ${formatBytes(stats.new_size)}`]);
      if (saved > 0) items.push(['Saved', `${Math.round((saved / stats.orig_size) * 100)}%`]);
    } else if (stats.total_bytes) {
      items.push(['Size', formatBytes(stats.total_bytes)]);
    }
    const pages = stats.total_pages ?? stats.output_pages;
    if (pages) items.push(['Pages', String(pages)]);
    if (stats.total_chunks) items.push(['Files', String(stats.total_chunks)]);
    return items;
  }

  function renderStats(items) {
    const box = $('.rs-stats');
    box.replaceChildren(...items.map(([label, value], index) => {
      const cell = document.createElement('div');
      cell.className = 'rs-stat';
      cell.style.animationDelay = `${120 + index * 70}ms`;
      const valueEl = document.createElement('strong');
      valueEl.textContent = value;
      const labelEl = document.createElement('span');
      labelEl.textContent = label;
      cell.append(valueEl, labelEl);
      return cell;
    }));
  }

  function renderActions(buttons) {
    $('.rs-actions').innerHTML = buttons.map(({ action, label, primary }) => `
      <button type="button" data-action="${action}" data-tool-id="${escapeAttr(toolIdForRetry)}"
        class="rs-btn ${primary ? 'rs-btn-primary' : 'rs-btn-quiet'}">${label}</button>`).join('');
  }

  function finish(state) {
    stopTimers();
    root.classList.remove('rs-indeterminate');
    setState(state);
  }

  function complete({ outputs, stats }) {
    if (!root) return;
    const elapsedMs = performance.now() - startedAt;
    targetPercent = 100;
    shownPercent = 100;
    renderPercent();
    finish('done');

    const files = (Array.isArray(outputs) ? outputs : [outputs]).filter(Boolean);
    const first = files[0] || '';
    const folder = folderNameOf(first);
    $('.rs-result-title').textContent = files.length > 1 ? `${files.length} files ready` : 'Your file is ready';
    $('.rs-result-sub').textContent = files.length > 1
      ? `Saved in ${folder || 'your output folder'}`
      : `${fileNameOf(first)}${folder ? ` · in ${folder}` : ''}`;
    renderStats(buildStats(stats, elapsedMs));
    renderActions([
      { action: 'open-output-file', label: files.length > 1 ? 'Open first file' : 'Open file', primary: true },
      { action: 'reveal-output-folder', label: 'Show in folder' },
      { action: 'run-stage-reset', label: 'Start over' }
    ]);
  }

  function humanError(message) {
    const text = String(message || '').replace(/^error:\s*/i, '').trim();
    if (/cancel/i.test(text)) return { title: 'Stopped', detail: 'Nothing was changed. Your original files are safe.' };
    if (/already running/i.test(text)) return { title: 'One thing at a time', detail: 'Another job is still finishing. Try again in a moment.' };
    return { title: 'That didn’t work', detail: text || 'The tool stopped unexpectedly. Your original files are safe.' };
  }

  function fail(message) {
    if (!root) return;
    const { title, detail } = humanError(message);
    const wasCancel = title === 'Stopped';
    finish(wasCancel ? 'stopped' : 'failed');
    $('.rs-result-title').textContent = title;
    $('.rs-result-sub').textContent = detail;
    $('.rs-stats').replaceChildren();
    renderActions([
      { action: 'studio-execute', label: wasCancel ? 'Run again' : 'Try again', primary: true },
      { action: 'run-stage-reset', label: 'Back' }
    ]);
    if (!wasCancel) log(`Error: ${detail}`);
  }

  function reset() {
    if (!root) return;
    finish('idle');
  }

  window.RunStage = { mount, start, progress, log, complete, fail, reset };
})();
