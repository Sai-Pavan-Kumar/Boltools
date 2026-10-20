"""Windows notifications without extra libraries.

Uses the notification API built into Windows through PowerShell. A desktop app
may only show notifications under a name Windows knows, so the app registers
its ID (HKCU\\Software\\Classes\\AppUserModelId, no admin) and a boltools://
link so clicking a notification opens Boltools on Tool Store.
"""

import os
import subprocess
import sys
import winreg
from xml.sax.saxutils import escape

APP_ID = "TheSurfBoard.Boltools.App.1.0"  # same ID main.py gives the window
APP_NAME = "Boltools"
PROTOCOL = "boltools"
CREATE_NO_WINDOW = 0x08000000

_SCRIPT = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($env:BOLTOOLS_TOAST_XML)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:BOLTOOLS_TOAST_APP).Show($toast)
"""


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" "%1"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "main.py")
    return f'"{pythonw}" "{main_py}" --dev "%1"'


def register(icon_path: str = "") -> None:
    """Name, icon and click target for notifications. Safe to call on every start."""
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\AppUserModelId\{APP_ID}") as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            if icon_path and os.path.isfile(icon_path):
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, icon_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:Boltools")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROTOCOL}\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, _launch_command())
    except OSError as err:
        print(f"[toast] could not register notifications: {err}", file=sys.stderr)


def show(title: str, body: str, link: str = f"{PROTOCOL}://store") -> bool:
    xml = (f'<toast activationType="protocol" launch="{escape(link)}">'
           f'<visual><binding template="ToastGeneric"><text>{escape(title)}</text><text>{escape(body)}</text>'
           f'</binding></visual></toast>')
    env = dict(os.environ, BOLTOOLS_TOAST_XML=xml, BOLTOOLS_TOAST_APP=APP_ID)
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT],
                                env=env, capture_output=True, text=True, timeout=20, creationflags=CREATE_NO_WINDOW)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def announce_new_tools(tools) -> None:
    if not tools:
        return
    if len(tools) == 1:
        title = f"{tools[0].get('name', 'A new tool')} is available"
        body = "Download it from Tool Store whenever you like."
    else:
        title = f"{len(tools)} new tools are available"
        body = ", ".join(t.get("name", t["id"]) for t in tools[:3]) + ". Download them from Tool Store."
    show(title, body)
