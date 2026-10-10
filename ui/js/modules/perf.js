/**
 * Dev-Only Performance HUD (?bench=1)
 * Monitors FPS, Long Tasks, DOM Node Count, and JS Heap.
 */

class PerfMonitor {
  constructor() {
    this.isActive = window.location.search.includes('bench=1');
    this.panel = null;
    this.fps = 60;
    this.longTasksCount = 0;
    this.maxFrameTime = 0;
    this._lastTime = performance.now();
    this._frames = 0;

    if (this.isActive) {
      this.init();
    }
  }

  init() {
    this._createPanel();
    this._observeLongTasks();
    this._startLoop();
  }

  _createPanel() {
    this.panel = document.createElement('div');
    this.panel.id = 'perf-hud-panel';
    this.panel.className = 'fixed bottom-4 right-4 z-50 p-3 bg-black/85 text-emerald-400 font-mono text-[11px] rounded-xl border border-emerald-500/30 shadow-2xl backdrop-blur-md pointer-events-none min-w-[190px] leading-relaxed';
    this.panel.innerHTML = `
      <div class="flex items-center justify-between border-b border-white/10 pb-1 mb-1 font-bold text-white">
        <span>PERF HUD</span>
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
      </div>
      <div class="flex justify-between"><span>FPS:</span><span id="hud-fps" class="text-white font-bold">60</span></div>
      <div class="flex justify-between"><span>DOM Nodes:</span><span id="hud-dom">0</span></div>
      <div class="flex justify-between"><span>JS Heap:</span><span id="hud-heap">0 MB</span></div>
      <div class="flex justify-between"><span>Long Tasks (>50ms):</span><span id="hud-long">0</span></div>
      <div class="flex justify-between"><span>Max Frame:</span><span id="hud-max-frame">0 ms</span></div>
    `;
    document.body.appendChild(this.panel);
  }

  _observeLongTasks() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              this.longTasksCount++;
              const el = document.getElementById('hud-long');
              if (el) el.innerText = this.longTasksCount;
            }
          }
        });
        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {}
    }
  }

  _startLoop() {
    const tick = () => {
      this._frames++;
      const now = performance.now();
      const delta = now - this._lastTime;

      if (delta >= 1000) {
        this.fps = Math.round((this._frames * 1000) / delta);
        this._frames = 0;
        this._lastTime = now;
        this._updateHUD();
      }

      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  _updateHUD() {
    if (!this.panel) return;
    const fpsEl = document.getElementById('hud-fps');
    const domEl = document.getElementById('hud-dom');
    const heapEl = document.getElementById('hud-heap');

    if (fpsEl) {
      fpsEl.innerText = this.fps;
      fpsEl.className = this.fps >= 55 ? 'text-emerald-400 font-bold' : (this.fps >= 30 ? 'text-amber-400 font-bold' : 'text-red-400 font-bold');
    }
    if (domEl) {
      const count = document.getElementsByTagName('*').length;
      domEl.innerText = count.toLocaleString();
      domEl.className = count <= 1500 ? 'text-emerald-400' : 'text-red-400 font-bold';
    }
    if (heapEl && performance.memory) {
      const heapMb = (performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(1);
      heapEl.innerText = `${heapMb} MB`;
    }
  }
}

const perfMonitor = new PerfMonitor();
window.boltoolsPerfMonitor = perfMonitor;
