import webview
import threading
import time

class DesktopAPI:
    def echo(self, text):
        return f"Python echoed: {text}"

api = DesktopAPI()
w = webview.create_window(
    "Test Bridge",
    html="""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <h1>Testing Bridge</h1>
  <script>
    window.addEventListener('pywebviewready', async () => {
      const resp = await window.pywebview.api.echo('Hello World');
      console.log('Result:', resp);
    });
  </script>
</body>
</html>""",
    js_api=api
)

def _close():
    time.sleep(2.5)
    w.destroy()

threading.Thread(target=_close, daemon=True).start()
webview.start()
print("IPC Test passed successfully!")
