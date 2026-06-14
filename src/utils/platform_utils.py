"""Cross-platform helpers (Windows / macOS / Linux).

Centralizes every OS-specific decision the app makes: where config lives,
where Moho and FFmpeg are found, how to suppress console windows when
spawning subprocesses, and how to reveal a file in the system file manager.
"""
import os
import sys
import subprocess
from pathlib import Path

# --- Platform detection ---------------------------------------------------
IS_WINDOWS = sys.platform.startswith("win") or os.name == "nt"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = not IS_WINDOWS and not IS_MACOS

# Project root (two levels up from src/utils/)
APP_ROOT = Path(__file__).resolve().parent.parent.parent


def platform_label() -> str:
    """Human-readable platform name for UI labels."""
    if IS_WINDOWS:
        return "Windows"
    if IS_MACOS:
        return "macOS"
    return "Linux"


def file_manager_name() -> str:
    """Name of the system file manager, for UI labels."""
    if IS_WINDOWS:
        return "Explorer"
    if IS_MACOS:
        return "Finder"
    return "File Manager"


def reveal_label() -> str:
    """Context-menu label for revealing a file in the file manager."""
    if IS_MACOS:
        return "Reveal in Finder"
    if IS_WINDOWS:
        return "Show in Explorer"
    return "Show in File Manager"


# --- Config directory -----------------------------------------------------
def config_dir() -> Path:
    """Per-user configuration directory, following each OS's conventions."""
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "MohoRenderFarm"
    if IS_MACOS:
        return Path.home() / "Library" / "Application Support" / "MohoRenderFarm"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "MohoRenderFarm"


# --- Moho executable ------------------------------------------------------
def default_moho_path() -> str:
    """Best-guess default install location of Moho per platform."""
    if IS_WINDOWS:
        return r"C:\Program Files\Moho 14\Moho.exe"
    if IS_MACOS:
        return "/Applications/Moho 14/Moho.app"
    return ""


def resolve_moho_executable(path: str) -> str:
    """Resolve a user-supplied Moho path to an actual runnable binary.

    On macOS the user typically points at the ``Moho.app`` bundle; the real
    command-line binary lives inside ``Contents/MacOS/``. On other platforms
    the path is returned unchanged.
    """
    if not path:
        return path
    if IS_MACOS and path.rstrip("/").endswith(".app") and os.path.isdir(path):
        macos_dir = os.path.join(path.rstrip("/"), "Contents", "MacOS")
        # Prefer a binary that matches the bundle name (e.g. Moho.app -> Moho)
        app_stem = os.path.splitext(os.path.basename(path.rstrip("/")))[0]
        candidate = os.path.join(macos_dir, app_stem)
        if os.path.isfile(candidate):
            return candidate
        # Fall back to the first executable file inside the bundle
        try:
            for name in sorted(os.listdir(macos_dir)):
                full = os.path.join(macos_dir, name)
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    return full
        except OSError:
            pass
    return path


def moho_exists(path: str) -> bool:
    """True if the (resolved) Moho executable exists on disk."""
    resolved = resolve_moho_executable(path)
    return bool(resolved) and os.path.exists(resolved)


# --- FFmpeg / FFprobe -----------------------------------------------------
def _bundled_binary(name: str) -> Path:
    exe = name + (".exe" if IS_WINDOWS else "")
    return APP_ROOT / "ffmpeg" / exe


def ffmpeg_path() -> str:
    """Path to ffmpeg: bundled binary if present, otherwise rely on PATH."""
    bundled = _bundled_binary("ffmpeg")
    if bundled.exists():
        return str(bundled)
    return "ffmpeg"


def ffprobe_path() -> str:
    """Path to ffprobe: bundled binary if present, otherwise rely on PATH."""
    bundled = _bundled_binary("ffprobe")
    if bundled.exists():
        return str(bundled)
    return "ffprobe"


# --- Subprocess helpers ---------------------------------------------------
def no_window_kwargs() -> dict:
    """subprocess kwargs that suppress a console window (Windows only)."""
    if IS_WINDOWS:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


# --- File manager integration --------------------------------------------
def open_in_file_manager(filepath: str) -> None:
    """Reveal a file or open a folder in the system file manager.

    Selects the file where supported (Explorer on Windows, Finder on macOS).
    """
    filepath = os.path.normpath(filepath)
    is_file = os.path.isfile(filepath)
    is_dir = os.path.isdir(filepath)
    folder = filepath if is_dir else os.path.dirname(filepath)

    try:
        if IS_WINDOWS:
            if is_file:
                subprocess.Popen(["explorer", "/select,", filepath])
            elif is_dir:
                subprocess.Popen(["explorer", filepath])
            elif os.path.exists(folder):
                subprocess.Popen(["explorer", folder])
        elif IS_MACOS:
            if is_file:
                subprocess.Popen(["open", "-R", filepath])
            elif os.path.exists(folder):
                subprocess.Popen(["open", folder])
        else:  # Linux and other Unix
            target = filepath if (is_file or is_dir) else folder
            if os.path.exists(target):
                subprocess.Popen(["xdg-open", target])
    except (OSError, ValueError):
        pass
