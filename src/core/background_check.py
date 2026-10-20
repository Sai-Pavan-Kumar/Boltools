"""Daily "new tools" check while Boltools is closed (Settings switch, on by default).

On: one per-user Task Scheduler job runs `Boltools.exe --check-new-tools` once a
day (and at the next login if the PC was off). That run fetches the signed tools
list, shows one Windows notification per new tool, and exits; no window opens.
Off: the job is deleted, so nothing of Boltools runs in the background.
No admin rights are needed for a per-user job.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
from xml.sax.saxutils import escape

TASK_NAME = r"Boltools\New tools check"
PREFS_FILE = os.path.join(os.path.expanduser("~"), ".boltools", "preferences.json")
CHECK_ARG = "--check-new-tools"
SYNC_TIMEOUT_S = 30
CREATE_NO_WINDOW = 0x08000000

_TASK_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Tells you when a new Boltools tool is available. Turn off in Boltools Settings.</Description></RegistrationInfo>
  <Triggers>
    <CalendarTrigger><StartBoundary>2026-01-01T11:00:00</StartBoundary><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger>
  </Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <StartWhenAvailable>true</StartWhenAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
  </Settings>
  <Actions Context="Author"><Exec><Command>{command}</Command><Arguments>{arguments}</Arguments></Exec></Actions>
</Task>
"""


def _launch(root_dir: str):
    if getattr(sys, "frozen", False):
        return sys.executable, CHECK_ARG
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return pythonw, f'"{os.path.join(root_dir, "main.py")}" --dev {CHECK_ARG}'


def _schtasks(*args) -> bool:
    try:
        result = subprocess.run(["schtasks.exe", *args], capture_output=True, text=True,
                                timeout=30, creationflags=CREATE_NO_WINDOW)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def is_scheduled() -> bool:
    return _schtasks("/Query", "/TN", TASK_NAME)


def schedule(root_dir: str) -> bool:
    command, arguments = _launch(root_dir)
    xml = _TASK_XML.format(command=escape(command), arguments=escape(arguments))
    fd, path = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(fd, "w", encoding="utf-16") as f:
            f.write(xml)
        return _schtasks("/Create", "/TN", TASK_NAME, "/XML", path, "/F")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def unschedule() -> bool:
    return not is_scheduled() or _schtasks("/Delete", "/TN", TASK_NAME, "/F")


def is_enabled() -> bool:
    """The user's choice; on until they turn it off."""
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            return bool(json.load(f).get("background_check", True))
    except (OSError, ValueError):
        return True


def set_enabled(enabled: bool, root_dir: str) -> bool:
    prefs = {}
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as f:
            prefs = json.load(f)
    except (OSError, ValueError):
        pass
    prefs["background_check"] = bool(enabled)
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)
    return schedule(root_dir) if enabled else unschedule()


def sync_on_start(root_dir: str) -> None:
    """Keeps Windows in line with the switch; re-creating also follows the app to a new install folder."""
    threading.Thread(target=lambda: schedule(root_dir) if is_enabled() else unschedule(),
                     name="boltools-background-check", daemon=True).start()


def run_check(tool_store_service, new_tools, toast, icon_path: str = "") -> None:
    """The scheduled run: refresh the signed tools list, announce new tools once, exit."""
    done = threading.Event()
    tool_store_service.sync_manifest_async(on_complete=lambda *_: done.set())
    done.wait(SYNC_TIMEOUT_S)
    toast.register(icon_path)
    fresh = new_tools.take_unannounced((tool_store_service.cached_manifest or {}).get("tools", []))
    toast.announce_new_tools(fresh)
