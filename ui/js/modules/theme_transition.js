/**
 * Theme switch: the new theme spreads from the pressed button with a soft,
 * feathered edge, a faint brand-blue light ring rides that edge, and the old
 * screen sinks back a little (shrinks and dims) as if pushed away.
 *
 * Built on View Transitions: the browser snapshots both screens once and only
 * GPU properties are animated (mask, transform, filter), so it stays smooth on
 * slow PCs. Reduced-motion users, and any browser error, get an instant switch.
 */
const ThemeTransition = (() => {
  const DURATION_MS = 650;
  const EASING = 'cubic-bezier(0.22, 1, 0.36, 1)'; // quick start, long soft landing
  const FEATHER_PX = 64; // width of the soft edge; also where the ring sits
  const RING_FADE_START = 0.7; // the ring fades out over the last 30%

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // Radius that reaches the farthest screen corner from (x, y), plus the feather.
  function coverRadius(x, y) {
    const far = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    return far + FEATHER_PX;
  }

  function originOf(el) {
    if (!el) return { x: window.innerWidth - 40, y: 34 };
    const box = el.getBoundingClientRect();
    return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
  }

  // A full-size ring centred on the button; the transition scales it up from 0.
  function addRing(x, y, radius) {
    const ring = document.createElement('div');
    ring.className = 'theme-ring';
    ring.setAttribute('aria-hidden', 'true');
    const ringRadius = radius - FEATHER_PX / 2;
    Object.assign(ring.style, {
      left: `${x - ringRadius}px`,
      top: `${y - ringRadius}px`,
      width: `${ringRadius * 2}px`,
      height: `${ringRadius * 2}px`
    });
    document.body.appendChild(ring);
    return ring;
  }

  function animate(x, y, radius) {
    const root = document.documentElement;
    // fill: 'forwards' holds the last frame; without it the new screen snaps back to
    // hidden for a frame before the transition ends, which shows as a flash.
    const timing = { duration: DURATION_MS, easing: EASING, fill: 'forwards' };
    root.animate({ '--reveal': ['0px', `${radius}px`] },
      { ...timing, pseudoElement: '::view-transition-new(root)' });
    root.animate({ transform: ['scale(1)', 'scale(0.975)'], filter: ['brightness(1)', 'brightness(0.78)'] },
      { ...timing, pseudoElement: '::view-transition-old(root)' });
    root.animate({
      transform: ['scale(0)', 'scale(1)', 'scale(1)'],
      opacity: [0.9, 0.55, 0],
      offset: [0, RING_FADE_START, 1]
    }, { ...timing, pseudoElement: '::view-transition-new(theme-ring)' });
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
    const radius = coverRadius(x, y);
    const root = document.documentElement;
    root.style.setProperty('--vt-x', `${x}px`);
    root.style.setProperty('--vt-y', `${y}px`);
    // Behind the sinking old screen: its own background, so no light or dark rim shows.
    root.style.setProperty('--vt-old-bg', getComputedStyle(document.body).backgroundColor);
    // Per-element colour fades would run inside the snapshot and look muddy.
    root.classList.add('theme-switching');
    let ring = null;
    try {
      const transition = document.startViewTransition(() => {
        applyTheme(theme);
        ring = addRing(x, y, radius);
        spinIcon();
      });
      transition.ready.then(() => animate(x, y, radius)).catch(() => {});
      transition.finished.finally(() => {
        root.classList.remove('theme-switching');
        if (ring) ring.remove();
      });
    } catch (err) {
      root.classList.remove('theme-switching');
      applyTheme(theme);
    }
  }

  return { switchTo };
})();
