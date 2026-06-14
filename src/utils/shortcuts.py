"""Shortcuts and startup integration (cross-platform).

Windows: .lnk shortcuts (Desktop / Start Menu / Taskbar) + registry Run key.
macOS:   a .command launcher on the Desktop + a LaunchAgent for login startup.
Linux:   not implemented (functions return False / no-op).

Features that have no equivalent on the current OS simply return False so the
GUI can hide or disable the corresponding controls.
"""
import os
import sys
import subprocess
from pathlib import Path

try:
    import winreg  # Windows only
except ImportError:  # macOS / Linux
    winreg = None

from src.utils import platform_utils as plat

APP_NAME = "Moho Render Farm"
APP_ROOT = Path(__file__).parent.parent.parent
START_BAT = str(APP_ROOT / "start.bat")
START_COMMAND = str(APP_ROOT / "start.command")
PYTHON_EXE = str(APP_ROOT / "python" / "pythonw.exe")
MAIN_PY = str(APP_ROOT / "main.py")

STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_REG_NAME = "MohoRenderFarm"

# macOS LaunchAgent
LAUNCH_AGENT_LABEL = "com.mohorenderfarm.app"


# =========================================================================
# Windows helpers (.lnk via PowerShell)
# =========================================================================

def _create_shortcut(shortcut_path: str) -> bool:
    """Create a Windows .lnk shortcut using PowerShell."""
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{PYTHON_EXE}"; '
        f'$s.Arguments = "main.py"; '
        f'$s.WorkingDirectory = "{APP_ROOT}"; '
        f'$s.Description = "{APP_NAME}"; '
        f'$s.Save()'
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=15,
        )
        return result.returncode == 0
    except Exception:
        return False


def _remove_shortcut(shortcut_path: str) -> bool:
    """Remove a shortcut file if it exists."""
    try:
        p = Path(shortcut_path)
        if p.exists():
            p.unlink()
        return True
    except Exception:
        return False


# =========================================================================
# macOS helpers (.command launcher + LaunchAgent)
# =========================================================================

def _mac_command_contents() -> str:
    """A small launcher that defers to the project's start.command if present."""
    if os.path.exists(START_COMMAND):
        return f'#!/bin/bash\nexec "{START_COMMAND}"\n'
    # Fallback: run directly with the current interpreter
    return f'#!/bin/bash\ncd "{APP_ROOT}"\nexec "{sys.executable}" "{MAIN_PY}"\n'


def _create_mac_command(path: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(_mac_command_contents())
        os.chmod(path, 0o755)
        return True
    except Exception:
        return False


def _launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def _launch_agent_path() -> Path:
    return _launch_agents_dir() / f"{LAUNCH_AGENT_LABEL}.plist"


def _launch_agent_plist() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCH_AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{MAIN_PY}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{APP_ROOT}</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
'''


# =========================================================================
# Desktop shortcut
# =========================================================================

def _desktop_dir() -> Path:
    if plat.IS_WINDOWS:
        return Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
    return Path.home() / "Desktop"


def _desktop_path() -> str:
    ext = ".lnk" if plat.IS_WINDOWS else ".command"
    return str(_desktop_dir() / f"{APP_NAME}{ext}")


def has_desktop_shortcut() -> bool:
    if plat.IS_LINUX:
        return False
    return Path(_desktop_path()).exists()


def add_desktop_shortcut() -> bool:
    if plat.IS_WINDOWS:
        return _create_shortcut(_desktop_path())
    if plat.IS_MACOS:
        return _create_mac_command(_desktop_path())
    return False


def remove_desktop_shortcut() -> bool:
    if plat.IS_LINUX:
        return False
    return _remove_shortcut(_desktop_path())


# =========================================================================
# Start Menu (Windows only)
# =========================================================================

def _start_menu_path() -> str:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    folder = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return str(folder / f"{APP_NAME}.lnk")


def has_start_menu_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return Path(_start_menu_path()).exists()


def add_start_menu_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return _create_shortcut(_start_menu_path())


def remove_start_menu_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return _remove_shortcut(_start_menu_path())


# =========================================================================
# Taskbar Pin (Windows only)
# =========================================================================

def _taskbar_pins_path() -> str:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    folder = Path(appdata) / "Microsoft" / "Internet Explorer" / "Quick Launch" / "User Pinned" / "TaskBar"
    return str(folder / f"{APP_NAME}.lnk")


def has_taskbar_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return Path(_taskbar_pins_path()).exists()


def add_taskbar_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return _create_shortcut(_taskbar_pins_path())


def remove_taskbar_shortcut() -> bool:
    if not plat.IS_WINDOWS:
        return False
    return _remove_shortcut(_taskbar_pins_path())


# =========================================================================
# Run on startup / login
# =========================================================================

def has_startup_entry() -> bool:
    if plat.IS_WINDOWS:
        if winreg is None:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, STARTUP_REG_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False
    if plat.IS_MACOS:
        return _launch_agent_path().exists()
    return False


def add_startup_entry() -> bool:
    """Add app to startup (Windows registry / macOS LaunchAgent)."""
    if plat.IS_WINDOWS:
        if winreg is None:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, STARTUP_REG_NAME, 0, winreg.REG_SZ,
                              f'"{PYTHON_EXE}" "{MAIN_PY}"')
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    if plat.IS_MACOS:
        try:
            _launch_agents_dir().mkdir(parents=True, exist_ok=True)
            plist_path = _launch_agent_path()
            plist_path.write_text(_launch_agent_plist(), encoding="utf-8")
            # Best-effort registration with launchd
            try:
                subprocess.run(["launchctl", "load", str(plist_path)],
                               capture_output=True, timeout=10)
            except Exception:
                pass
            return True
        except Exception:
            return False
    return False


def remove_startup_entry() -> bool:
    """Remove app from startup (Windows registry / macOS LaunchAgent)."""
    if plat.IS_WINDOWS:
        if winreg is None:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, STARTUP_REG_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    if plat.IS_MACOS:
        try:
            plist_path = _launch_agent_path()
            try:
                subprocess.run(["launchctl", "unload", str(plist_path)],
                               capture_output=True, timeout=10)
            except Exception:
                pass
            if plist_path.exists():
                plist_path.unlink()
            return True
        except Exception:
            return False
    return False
