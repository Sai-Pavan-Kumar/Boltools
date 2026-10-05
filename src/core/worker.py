"""Thread-safe background execution engine for Boltools.

Ensures heavy I/O, compression, or transcoding jobs run on isolated
background threads, preventing UI lockups and 'Not Responding' states.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional
import tkinter as tk

class AsyncWorker:
    """Singleton executor pool for background tasks with UI callback marshaling."""
    
    _instance: Optional['AsyncWorker'] = None
    
    def __new__(cls, max_workers: int = 4):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="BoltoolsWorker")
        return cls._instance

    def run_task(
        self,
        widget: tk.Widget,
        task_func: Callable[..., Any],
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        *args,
        **kwargs
    ) -> Future:
        """Runs task_func in background and marshals callbacks back to the Tk thread safely."""
        
        def _wrapper():
            try:
                result = task_func(*args, **kwargs)
                if on_success:
                    # Marshal to Tkinter main thread
                    widget.after(0, lambda: on_success(result))
            except Exception as exc:
                if on_error:
                    # Marshal error to Tkinter main thread
                    widget.after(0, lambda: on_error(exc))
                else:
                    print(f"[Boltools Worker Error] Unhandled background error: {exc}")

        return self.executor.submit(_wrapper)

    def shutdown(self):
        """Clean shutdown of background threads."""
        self.executor.shutdown(wait=False, cancel_futures=True)
