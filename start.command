#!/bin/bash
#
# Moho Render Farm launcher for macOS (and Linux).
#
# On first run this creates a local virtual environment (.venv) and installs
# the GUI dependencies (PyQt6 and the networking libraries). Subsequent runs
# reuse it and start instantly. Double-click in Finder, or run from a terminal.
#
set -u

# Resolve the directory this script lives in (handles spaces and symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

pause_on_exit() {
    # Keep the Terminal window open so the user can read any error message
    echo ""
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
}

# --- Locate a Python 3 interpreter ---------------------------------------
PYBIN=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
            PYBIN="$(command -v "$cand")"
            break
        fi
    fi
done

if [ -z "$PYBIN" ]; then
    echo "ERROR: Python 3 was not found."
    echo "Install it from https://www.python.org/downloads/ (or 'brew install python' on macOS),"
    echo "then run this launcher again."
    pause_on_exit
    exit 1
fi

VENV="$DIR/.venv"
VPY="$VENV/bin/python"

# --- Create the virtual environment on first run -------------------------
if [ ! -x "$VPY" ]; then
    echo "First-time setup: creating a virtual environment..."
    if ! "$PYBIN" -m venv "$VENV"; then
        echo "ERROR: Failed to create the virtual environment."
        pause_on_exit
        exit 1
    fi
fi

# --- Ensure GUI dependencies are installed -------------------------------
if ! "$VPY" -c "import PyQt6.QtWidgets" >/dev/null 2>&1; then
    echo "Installing dependencies (this may take a minute)..."
    "$VPY" -m pip install --upgrade pip >/dev/null 2>&1 || true
    if [ -f "$DIR/requirements.txt" ]; then
        INSTALL_TARGET=(-r "$DIR/requirements.txt")
    else
        INSTALL_TARGET=(PyQt6 requests Flask)
    fi
    if ! "$VPY" -m pip install "${INSTALL_TARGET[@]}"; then
        echo "ERROR: Failed to install dependencies. Check your internet connection."
        pause_on_exit
        exit 1
    fi
fi

# --- Launch --------------------------------------------------------------
exec "$VPY" "$DIR/main.py" "$@"
