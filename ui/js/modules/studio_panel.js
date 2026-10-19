/**
 * Studio Panel: the right column of a tool screen.
 *
 * It only ever shows what the user needs for the step they are on:
 *   empty   -> a short note (settings would be noise before there are files)
 *   ready   -> settings + one Start button that names the exact action
 *   running -> the same settings, locked
 *   result  -> next steps that carry the new file into another tool
 */
(function () {
  let column = null;
  let toolId = '';
  let nextList = null;

  function mount(rightColumn, id) {
    column = rightColumn;
    toolId = id;
    const empty = document.createElement('div');
    empty.className = 'sp-empty sp-card';
    empty.innerHTML = `
      <span class="sp-eyebrow">Settings</span>
      <p class="sp-lead">Settings appear here after you add files, so you only see what matters for them.</p>
      <p class="sp-fine">Runs on this PC. Your files are never uploaded.</p>`;

    const next = document.createElement('div');
    next.className = 'sp-next sp-card';
    next.innerHTML = `
      <span class="sp-eyebrow">Next steps</span>
      <p class="sp-fine">Keep going with the file you just made. It opens in the next tool, ready to use.</p>
      <div class="sp-next-list"></div>`;
    nextList = next.querySelector('.sp-next-list');

    const lockNote = document.createElement('p');
    lockNote.className = 'sp-lock-note';
    lockNote.textContent = 'Settings are locked while Boltools works.';

    column.prepend(empty);
    column.append(next);
    document.getElementById('studio-inspector')?.append(lockNote);
    setPhase('empty');
  }

  function setPhase(phase) {
    if (column) column.dataset.phase = phase;
  }

  function refreshStart(fileCount) {
    const button = document.getElementById('studio-btn-execute');
    const label = document.getElementById('studio-btn-exec-label');
    const reason = document.getElementById('studio-start-reason');
    const blocked = ToolUX.blockedReason(toolId, fileCount);
    if (label) label.textContent = ToolUX.startLabel(toolId, fileCount);
    if (button) {
      button.disabled = Boolean(blocked);
      button.classList.toggle('sp-blocked', Boolean(blocked));
    }
    if (reason) reason.textContent = blocked;
  }

  // onOpen(toolId, files) moves the user into the suggested tool with the files loaded.
  function showNext(outputs, isAvailable, onOpen) {
    const steps = ToolUX.nextSteps(outputs, toolId, isAvailable);
    nextList.replaceChildren(...steps.map((step, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'sp-next-item';
      button.style.animationDelay = `${200 + index * 70}ms`;
      const title = document.createElement('strong');
      title.textContent = step.title;
      const why = document.createElement('span');
      why.textContent = step.why;
      button.append(title, why);
      button.addEventListener('click', () => onOpen(step.toolId, step.files));
      return button;
    }));
    column.classList.toggle('sp-no-next', steps.length === 0);
    setPhase('result');
  }

  window.StudioPanel = { mount, setPhase, refreshStart, showNext };
})();
