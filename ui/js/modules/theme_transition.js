/**
 * Theme switch as a circular reveal from the button that was pressed.
 *
 * Uses the browser's View Transitions: it snapshots the old screen once and
 * animates only a clip-path on the GPU, so it stays at 60 fps on slow PCs, unlike
 * fading hundreds of element colours. Reduced-motion users get an instant switch.
 */
const ThemeTransition = (() => {
  const DURATION_MS = 560;
  const EASING = 'cubic-bezier(0.22, 1, 0.36, 1)'; // fast start, long soft landing

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // Radius that reaches the farthest screen corner from (x, y).
  function coverRadius(x, y) {
    return Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
  }

  function originOf(el) {
    if (!el) return { x: window.innerWidth - 40, y: 34 };
    const box = el.getBoundingClientRect();
    return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
  }

  function spinIcon() {
    const icon = document.querySelector('#btn-theme-toggle svg');
    if (icon) icon.classList.add('theme-icon-enter');
  }

  function switchTo(theme, originEl) {
    if (theme === state.theme) return;
    if (!document.startViewTransition || prefersReducedMotion()) {
      applyTheme(theme);
      return;
    }
    const { x, y } = originOf(originEl);
    const root = document.documentElement;
    // Per-element colour fades would run inside the snapshot and look muddy.
    root.classList.add('theme-switching');
    const transition = document.startViewTransition(() => {
      applyTheme(theme);
      spinIcon();
    });
    transition.ready.then(() => {
      root.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${coverRadius(x, y)}px at ${x}px ${y}px)`] },
        { duration: DURATION_MS, easing: EASING, pseudoElement: '::view-transition-new(root)' }
      );
    }).catch(() => {});
    transition.finished.finally(() => root.classList.remove('theme-switching'));
  }

  return { switchTo };
})();
