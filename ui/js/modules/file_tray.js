/**
 * File Tray: the list of files a tool will work on.
 *
 * Rows slide into place with a FLIP animation (measure, re-render, animate the
 * difference), so reordering and removing feel physical instead of jumping.
 * File names are user data and only ever reach the DOM through textContent.
 */
(function () {
  const ROW_EXIT_MS = 180;
  const FLIP_MS = 280;

  const KINDS = [
    { label: 'PDF', tone: 'pdf', exts: ['pdf'] },
    { label: 'IMG', tone: 'img', exts: ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tif', 'tiff', 'heic', 'avif'] },
    { label: 'VID', tone: 'vid', exts: ['mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'] },
    { label: 'AUD', tone: 'aud', exts: ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg'] },
    { label: 'SUB', tone: 'doc', exts: ['srt', 'vtt'] }
  ];

  function fileNameOf(path) {
    return String(path || '').split(/[\\/]/).pop();
  }

  function kindOf(path) {
    const ext = (fileNameOf(path).split('.').pop() || '').toLowerCase();
    return KINDS.find(kind => kind.exts.includes(ext)) || { label: ext.slice(0, 3).toUpperCase() || 'FILE', tone: 'doc' };
  }

  function describe(meta) {
    const parts = [];
    if (meta.size_bytes) parts.push(formatBytes(meta.size_bytes));
    if (meta.width && meta.height) parts.push(`${meta.width} × ${meta.height}`);
    if (meta.pages !== undefined && meta.pages !== null) parts.push(`${meta.pages} page${meta.pages === 1 ? '' : 's'}`);
    return parts.join(' · ');
  }

  function buildRow(path, index, meta, reorderable) {
    const kind = kindOf(path);
    const row = document.createElement('div');
    row.className = 'ft-row file-drag-item';
    row.dataset.fileIdx = String(index);
    row.dataset.path = path;
    row.style.animationDelay = `${Math.min(index, 8) * 35}ms`;
    if (reorderable) row.draggable = true;

    row.innerHTML = `
      ${reorderable ? `<span class="ft-grip" title="Drag to reorder" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>
      <span class="ft-order rs-mono"></span>` : ''}
      ${meta.thumb ? '<img class="ft-thumb" alt="">' : ''}
      <span class="ft-kind ft-kind-${kind.tone}"></span>
      <span class="ft-text"><span class="ft-name"></span><span class="ft-meta rs-mono"></span></span>
      <span class="ft-flag" hidden>Locked</span>
      <button type="button" class="ft-remove" data-action="remove-studio-file" data-file-idx="${index}" title="Remove file" aria-label="Remove file">${getIcon('x', 'w-3.5 h-3.5')}</button>`;

    const fileName = fileNameOf(path);
    row.querySelector('.ft-kind').textContent = kind.label;
    row.querySelector('.ft-name').textContent = fileName;
    row.querySelector('.ft-name').title = fileName;
    row.querySelector('.ft-meta').textContent = describe(meta) || (reorderable ? 'Reading file…' : '');
    if (reorderable) row.querySelector('.ft-order').textContent = String(index + 1);
    if (meta.is_locked) row.querySelector('.ft-flag').hidden = false;
    if (meta.thumb) row.querySelector('.ft-thumb').src = meta.thumb;
    return row;
  }

  function measure(list) {
    const boxes = new Map();
    list.querySelectorAll('.ft-row').forEach(row => {
      const box = row.getBoundingClientRect();
      boxes.set(row.dataset.path, { top: box.top, left: box.left });
    });
    return boxes;
  }

  // Rows that already existed glide from their old spot; new rows use the CSS entry animation.
  function playFlip(list, before) {
    list.querySelectorAll('.ft-row').forEach(row => {
      const old = before.get(row.dataset.path);
      if (!old) return;
      row.style.animation = 'none';
      const box = row.getBoundingClientRect();
      const dx = old.left - box.left;
      const dy = old.top - box.top;
      if (!dx && !dy) return;
      row.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }],
        { duration: FLIP_MS, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' });
    });
  }

  // layout "grid" is for files whose order does not matter (photos); "list" shows order.
  function render(list, files, { meta = {}, reorderable = false, layout = 'list' } = {}) {
    const before = measure(list);
    list.classList.toggle('ft-grid', layout === 'grid');
    list.replaceChildren(...files.map((path, index) => buildRow(path, index, meta[path] || {}, reorderable)));
    playFlip(list, before);
  }

  function animateRemoval(list, index, onDone) {
    const row = list.querySelector(`.ft-row[data-file-idx="${index}"]`);
    if (!row || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return onDone();
    row.classList.add('ft-leaving');
    setTimeout(onDone, ROW_EXIT_MS);
  }

  function clearDropMarks(list) {
    list.querySelectorAll('.ft-row').forEach(row => row.classList.remove('ft-drop-before', 'ft-drop-after', 'ft-dragging'));
  }

  // onMove(fromIndex, toIndex) is called with the final insert position.
  function bindReorder(list, onMove) {
    if (list._ftBound) return;
    list._ftBound = true;
    let fromIndex = null;

    list.addEventListener('dragstart', (event) => {
      const row = event.target.closest('.ft-row');
      if (!row) return;
      fromIndex = Number(row.dataset.fileIdx);
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', row.dataset.fileIdx);
      requestAnimationFrame(() => row.classList.add('ft-dragging'));
    });

    list.addEventListener('dragover', (event) => {
      const row = event.target.closest('.ft-row');
      if (!row || fromIndex === null) return;
      event.preventDefault();
      const rect = row.getBoundingClientRect();
      const before = event.clientY - rect.top < rect.height / 2;
      list.querySelectorAll('.ft-drop-before, .ft-drop-after').forEach(el => el.classList.remove('ft-drop-before', 'ft-drop-after'));
      row.classList.add(before ? 'ft-drop-before' : 'ft-drop-after');
    });

    list.addEventListener('drop', (event) => {
      const row = event.target.closest('.ft-row');
      if (!row || fromIndex === null) return;
      event.preventDefault();
      const target = Number(row.dataset.fileIdx);
      const insertAfter = row.classList.contains('ft-drop-after');
      let toIndex = insertAfter ? target + 1 : target;
      if (fromIndex < toIndex) toIndex -= 1;
      clearDropMarks(list);
      const source = fromIndex;
      fromIndex = null;
      if (toIndex !== source) onMove(source, toIndex);
    });

    list.addEventListener('dragend', () => {
      fromIndex = null;
      clearDropMarks(list);
    });
  }

  window.FileTray = { render, animateRemoval, bindReorder, kindOf };
})();
