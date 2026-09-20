#!/usr/bin/env bash

set -euo pipefail

APP_NAME=viper-ultimate-tray

INSTALL_DIR="$HOME/.local/share/${APP_NAME}"
BIN_DIR="$HOME/.local/bin"

APPLICATIONS_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

APP_LAUNCHER="$BIN_DIR/viper-ultimate-tray"
UNINSTALL_LAUNCHER="$BIN_DIR/viper-ultimate-tray-uninstall"
DESKTOP_FILE="$APPLICATIONS_DIR/viper-ultimate-tray.desktop"
AUTOSTART_FILE="$AUTOSTART_DIR/viper-ultimate-tray.desktop"

DEPENDENCIES=(
    python
    pyside6
    kstatusnotifieritem
    python-gobject
    libnotify
    python-openrazer
    openrazer-daemon
)

info() {
    printf '%s\n' "$*"
}

check_passed() {
    printf '  ✓ %s\n' "$1"
}

check_failed() {
    printf '  ✗ %s\n' "$1" >&2
    exit 1
}

remove_file() {
    local file="$1"
    local description="$2"

    if [[ -e "$file" ]]; then
        rm -f "$file"
        check_passed "$description removed"
    else
        printf '  ✓ %s already absent\n' "$description"
    fi
}

remove_directory() {
    local directory="$1"
    local description="$2"

    if [[ -d "$directory" ]]; then
        rm -rf "$directory"
        check_passed "$description removed"
    else
        printf '  ✓ %s already absent\n' "$description"
    fi
}

# ---------------------------------------------------------------------------
# Target user and privileges
# ---------------------------------------------------------------------------

info "Checking system requirements..."

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    check_failed "Uninstaller must not be run as root."
fi

check_passed "Non-root user"

# ---------------------------------------------------------------------------
# Stop application
# ---------------------------------------------------------------------------

info ""
info "Stopping application..."

if pgrep -af 'python viper_ultimate_tray.py' >/dev/null 2>&1; then
    info "  Stopping Viper Ultimate Tray process..."

    while read -r pid _; do
        kill -TERM "$pid"
    done < <(pgrep -af 'python viper_ultimate_tray.py')

    for _ in {1..50}; do
        if ! pgrep -af 'python viper_ultimate_tray.py' >/dev/null 2>&1; then
            break
        fi
        sleep 0.1
    done

    if pgrep -af 'python viper_ultimate_tray.py' >/dev/null 2>&1; then
        info "  Process did not stop gracefully; forcing termination..."

        while read -r pid _; do
            kill -KILL "$pid"
        done < <(pgrep -af 'python viper_ultimate_tray.py')
    fi

    check_passed "Application stopped"
else
    check_passed "Application was not running"
fi

# ---------------------------------------------------------------------------
# Application files
# ---------------------------------------------------------------------------

info ""
info "Removing application files..."

remove_file \
    "$APP_LAUNCHER" \
    "Application launcher"

remove_file \
    "$DESKTOP_FILE" \
    "Desktop launcher"

remove_file \
    "$AUTOSTART_FILE" \
    "Autostart file"

remove_directory \
    "$INSTALL_DIR" \
    "Application runtime"

# ---------------------------------------------------------------------------
# Dependency removal commands
# ---------------------------------------------------------------------------

info ""
info "Optional dependency removal..."

info "The following commands can be used to remove the Viper Ultimate Tray dependencies individually:"
info ""

for package in "${DEPENDENCIES[@]}"; do
    printf '  sudo pacman -Rns %s\n' "$package"
done

info ""
info "OpenRazer may be used by other Razer devices or applications."
info "Review the dependency before removing it."
read -r -p "Press Enter to continue..."

# ---------------------------------------------------------------------------
# Final cleanup
# ---------------------------------------------------------------------------

info ""
info "Final cleanup..."

remove_file \
    "$UNINSTALL_LAUNCHER" \
    "Uninstall launcher"

info ""
info "Uninstallation completed successfully."
