/**
 * Theme switch that feels like a room light.
 *  - To dark: the screen dims from the edges inward, like a lamp switching off.
 *  - To light: a soft glow blooms from the centre, then settles.
 *
 * Built on View Transitions: the browser snapshots both screens once and only
 * GPU properties are animated (mask, filter), so it stays smooth on slow PCs.
 * Reduced-motion users, and any browser error, get an instant switch.
 */
const ThemeTransition = (() => {
  const TO_DARK = { duration: 620, easing: 'cubic-bezier(0.45, 0, 0.2, 1)' };   // slow start, like a dimmer
  const TO_LIGHT = { duration: 680, easing: 'cubic-bezier(0.33, 1, 0.68, 1)' }; // visible bloom, soft landing
  const BLOOM_PEAK = 1.35; // how bright the old screen flares before the light theme takes over

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // Centre to farthest corner, plus the soft edge, so the mask fully clears the screen.
  function screenRadius() {
    return Math.hypot(window.innerWidth, window.innerHeight) / 2 + 240;
  }

  function animateToDark(root, radius) {
    root.animate({ '--hole': [`${radius}px`, '0px'] },
      { ...TO_DARK, pseudoElement: '::view-transition-new(root)' });
    root.animate({ filter: ['brightness(1)', 'brightness(0.6)'] },
      { ...TO_DARK, pseudoElement: '::view-transition-old(root)' });
  }

  function animateToLight(root, radius) {
    root.animate({ '--reveal': ['0px', `${radius}px`] },
      { ...TO_LIGHT, pseudoElement: '::view-transition-new(root)' });
    root.animate({ filter: ['brightness(1)', `brightness(${BLOOM_PEAK})`] },
      { ...TO_LIGHT, pseudoElement: '::view-transition-old(root)' });
  }

  function spinIcon() {
    const icon = document.querySelector('#btn-theme-toggle svg');
    if (icon) icon.classList.add('theme-icon-enter');
  }

  function switchTo(theme) {
    if (theme === state.theme) return;
    if (!document.startViewTransition || prefersReducedMotion()) {
      applyTheme(theme);
      return;
    }
    const root = document.documentElement;
    const toDark = theme === 'dark';
    // Picks the matching mask in theme_transition.css.
    root.dataset.themeSwitch = toDark ? 'to-dark' : 'to-light';
    // Per-element colour fades would run inside the snapshot and look muddy.
    root.classList.add('theme-switching');
    const cleanUp = () => {
      root.classList.remove('theme-switching');
      delete root.dataset.themeSwitch;
    };
    try {
      const transition = document.startViewTransition(() => {
        applyTheme(theme);
        spinIcon();
      });
      transition.ready
        .then(() => (toDark ? animateToDark : animateToLight)(root, screenRadius()))
        .catch(() => {});
      transition.finished.finally(cleanUp);
    } catch (err) {
      cleanUp();
      applyTheme(theme);
    }
  }

  return { switchTo };
})();
