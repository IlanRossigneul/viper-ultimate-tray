#!/usr/bin/env bash

set -euo pipefail

APP_NAME=viper-ultimate-tray
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_DIR="$HOME/.local/share/${APP_NAME}"
BIN_DIR="$HOME/.local/bin"

DEPENDENCIES=(
    python
    pyside6
    qt6-svg
    kstatusnotifieritem
    python-gobject
    libnotify
    python-openrazer
    noto-fonts
)

AUR_DEPENDENCIES=(
    polychromatic
)

INPUT_REMAPPER_PACKAGES=(
    input-remapper
    input-remapper-git
    input-remapper-bin
)

INPUT_REMAPPER_INSTALL_PACKAGE="input-remapper-git"

declare -A MIN_VERSIONS=(
    [python]="3.11"
    [pyside6]="6.6"
    [qt6-svg]="6.6"
    [kstatusnotifieritem]="6.0"
    [python-gobject]="3.44"
    [libnotify]="0.8.0"
    [python-openrazer]="3.12.2"
)

OPENRAZER_DAEMON="openrazer-daemon"
OPENRAZER_DAEMON_MIN_VERSION="3.12.2"

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

require_command() {
    if command -v "$1" >/dev/null 2>&1; then
        check_passed "$2"
    else
        check_failed "$2"
    fi
}

require_file() {
    if [[ -f "$ROOT/$1" ]]; then
        check_passed "$2"
    else
        check_failed "$2"
    fi
}

check_dependency() {
    local package="$1"
    local minimum="${MIN_VERSIONS[$package]:-}"
    local installed

    if ! pacman -Q "$package" >/dev/null 2>&1; then
        if [[ -n "$minimum" ]]; then
            printf '  ✗ %s (missing, requires >= %s)\n' \
                "$package" "$minimum"
        else
            printf '  ✗ %s (missing)\n' "$package"
        fi
        return 1
    fi

    installed="$(pacman -Q "$package" | awk '{print $2}')"

    if [[ -n "$minimum" ]]; then
        if (( $(vercmp "$installed" "$minimum") < 0 )); then
            printf '  ✗ %s %s (requires >= %s)\n' \
                "$package" "$installed" "$minimum"
            return 1
        fi
    fi

    printf '  ✓ %s %s\n' "$package" "$installed"
}

# ---------------------------------------------------------------------------
# Target user and privileges
# ---------------------------------------------------------------------------

info "Checking system requirements..."

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    check_failed "Installer must not be run as root."
fi
check_passed "Non-root user"

# ---------------------------------------------------------------------------
# Operating system
# ---------------------------------------------------------------------------

if [[ ! -r /etc/os-release ]]; then
    check_failed "Reading /etc/os-release"
fi

# shellcheck disable=SC1091
source /etc/os-release

if [[ "${ID:-}" == "arch" || " ${ID_LIKE:-} " =~ [[:space:]]arch[[:space:]] ]]; then
    check_passed "Arch Linux / Arch-based distribution"
else
    check_failed "Arch Linux / Arch-based distribution"
fi

# ---------------------------------------------------------------------------
# KDE Plasma version
# ---------------------------------------------------------------------------

if ! command -v plasmashell >/dev/null 2>&1; then
    check_failed "KDE Plasma 6 or newer"
fi

PLASMA_VERSION="$(plasmashell --version 2>/dev/null | sed -n 's/.* //p')"

if [[ -z "$PLASMA_VERSION" ]]; then
    check_failed "KDE Plasma 6 or newer"
fi

PLASMA_MAJOR="${PLASMA_VERSION%%.*}"

if [[ "$PLASMA_MAJOR" =~ ^[0-9]+$ ]] && (( PLASMA_MAJOR >= 6 )); then
    check_passed "KDE Plasma $PLASMA_VERSION"
else
    check_failed "KDE Plasma 6 or newer"
fi

# ---------------------------------------------------------------------------
# Required installation tools
# ---------------------------------------------------------------------------

require_command pacman "pacman"
require_command paru "paru"
require_command sudo "sudo"
require_command vercmp "vercmp"

# ---------------------------------------------------------------------------
# User installation directories
# ---------------------------------------------------------------------------

if mkdir -p "$BIN_DIR" && [[ -w "$BIN_DIR" ]]; then
    check_passed "User binary directory"
else
    check_failed "User binary directory"
fi

if mkdir -p "$HOME/.local/share" && [[ -w "$HOME/.local/share" ]]; then
    check_passed "User data directory"
else
    check_failed "User data directory"
fi

# ---------------------------------------------------------------------------
# Source tree
# ---------------------------------------------------------------------------

if [[ -d "$ROOT/src" ]]; then
    check_passed "Source directory"
else
    check_failed "Source directory"
fi

require_file "src/start.sh" "Application startup script"
require_file "src/viper_ultimate_tray.py" "Application entry point"

for directory in \
    app \
    battery \
    battery_logs \
    config \
    icons \
    notifications \
    razer \
    ui
do
    if [[ -d "$ROOT/src/$directory" ]]; then
        check_passed "Source directory: src/$directory"
    else
        check_failed "Source directory: src/$directory"
    fi
done

info ""
info "Installation requirements are satisfied."

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

info ""
info "Checking dependencies..."

dependencies_satisfied=0

for package in "${DEPENDENCIES[@]}"; do
    if ! check_dependency "$package"; then
        dependencies_satisfied=1
    fi
done

openrazer_refresh_required=0

if ! pacman -Q "$OPENRAZER_DAEMON" >/dev/null 2>&1; then
    printf '  ✗ %s (missing, requires >= %s)\n' \
        "$OPENRAZER_DAEMON" "$OPENRAZER_DAEMON_MIN_VERSION"
    dependencies_satisfied=1
    openrazer_refresh_required=1
else
    openrazer_installed="$(
        pacman -Q "$OPENRAZER_DAEMON" | awk '{print $2}'
    )"

    if (( $(vercmp "$openrazer_installed" "$OPENRAZER_DAEMON_MIN_VERSION") < 0 )); then
        printf '  ✗ %s %s (requires >= %s)\n' \
            "$OPENRAZER_DAEMON" \
            "$openrazer_installed" \
            "$OPENRAZER_DAEMON_MIN_VERSION"

        dependencies_satisfied=1
        openrazer_refresh_required=1
    else
        printf '  ✓ %s %s\n' \
            "$OPENRAZER_DAEMON" \
            "$openrazer_installed"
    fi
fi

if (( dependencies_satisfied == 0 )); then
    info ""
    info "Dependencies are satisfied."
else
    info ""
    info "Installing dependencies..."

    sudo pacman --needed -S \
        "${DEPENDENCIES[@]}" \
        "$OPENRAZER_DAEMON"

    info ""
    info "Rechecking dependencies..."

    for package in "${DEPENDENCIES[@]}"; do
        if ! check_dependency "$package"; then
            check_failed "Dependency validation failed: $package"
        fi
    done

    openrazer_installed="$(
        pacman -Q "$OPENRAZER_DAEMON" | awk '{print $2}'
    )"

    if (( $(vercmp "$openrazer_installed" "$OPENRAZER_DAEMON_MIN_VERSION") < 0 )); then
        check_failed "OpenRazer daemon validation failed"
    fi

    printf '  ✓ %s %s\n' \
        "$OPENRAZER_DAEMON" \
        "$openrazer_installed"

    info ""
    info "Dependencies installed successfully."

    if (( openrazer_refresh_required )); then
        info ""
        info "Refreshing OpenRazer..."

        sudo udevadm control --reload-rules
        sudo udevadm trigger
        systemctl --user restart openrazer-daemon.service

        info "OpenRazer refreshed successfully."
    fi
fi

# ---------------------------------------------------------------------------
# AUR dependencies
# ---------------------------------------------------------------------------

info ""
info "Checking AUR dependencies..."

aur_dependencies_satisfied=0

for package in "${AUR_DEPENDENCIES[@]}"; do
    if ! pacman -Q "$package" >/dev/null 2>&1; then
        printf '  ✗ %s (missing)\n' "$package"
        aur_dependencies_satisfied=1
    else
        installed="$(pacman -Q "$package" | awk '{print $2}')"
        printf '  ✓ %s %s\n' "$package" "$installed"
    fi
done

if (( aur_dependencies_satisfied == 0 )); then
    info ""
    info "AUR dependencies are satisfied."
else
    info ""
    info "Installing AUR dependencies..."

    paru -S --needed "${AUR_DEPENDENCIES[@]}"

    info ""
    info "Rechecking AUR dependencies..."

    for package in "${AUR_DEPENDENCIES[@]}"; do
        if ! pacman -Q "$package" >/dev/null 2>&1; then
            check_failed "AUR dependency validation failed: $package"
        fi

        installed="$(pacman -Q "$package" | awk '{print $2}')"
        printf '  ✓ %s %s\n' "$package" "$installed"
    done

    info ""
    info "AUR dependencies installed successfully."
fi

# ---------------------------------------------------------------------------
# Input Remapper
# ---------------------------------------------------------------------------

info ""
info "Checking Input Remapper..."

input_remapper_package=""

for package in "${INPUT_REMAPPER_PACKAGES[@]}"; do
    if pacman -Q "$package" >/dev/null 2>&1; then
        input_remapper_package="$package"
        break
    fi
done

if [[ -n "$input_remapper_package" ]]; then
    installed="$(pacman -Q "$input_remapper_package" | awk '{print $2}')"
    printf '  ✓ %s %s\n' "$input_remapper_package" "$installed"
else
    printf '  ✗ Input Remapper (missing)\n'

    info ""
    info "Installing Input Remapper..."
    paru -S --needed "$INPUT_REMAPPER_INSTALL_PACKAGE"

    info ""
    info "Rechecking Input Remapper..."

    for package in "${INPUT_REMAPPER_PACKAGES[@]}"; do
        if pacman -Q "$package" >/dev/null 2>&1; then
            input_remapper_package="$package"
            break
        fi
    done

    if [[ -z "$input_remapper_package" ]]; then
        check_failed "Input Remapper validation failed"
    fi

    installed="$(pacman -Q "$input_remapper_package" | awk '{print $2}')"
    printf '  ✓ %s %s\n' "$input_remapper_package" "$installed"

    info ""
    info "Input Remapper installed successfully."
fi

# ---------------------------------------------------------------------------
# Application runtime
# ---------------------------------------------------------------------------

info ""
info "Installing application runtime..."

MODEL_FILE="$INSTALL_DIR/battery_logs/battery_charge_model.json"
SAMPLES_FILE="$INSTALL_DIR/battery_logs/battery_charge_samples.json"
ARCHIVE_DIRECTORY="$INSTALL_DIR/battery_logs/archive/"
MODEL_BACKUP=""
SAMPLES_BACKUP=""
ARCHIVE_BACKUP=""

if pgrep -af 'python viper_ultimate_tray.py' >/dev/null 2>&1; then
    info "  Stopping existing Viper Ultimate Tray process..."

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
fi

if [[ -f "$MODEL_FILE" ]]; then
    MODEL_BACKUP="$(mktemp)"
    cp "$MODEL_FILE" "$MODEL_BACKUP"
    info "  ✓ Existing model preserved"
fi

if [[ -f "$SAMPLES_FILE" ]]; then
    SAMPLES_BACKUP="$(mktemp)"
    cp "$SAMPLES_FILE" "$SAMPLES_BACKUP"
    info "  ✓ Existing samples preserved"
fi

if [[ -d "$ARCHIVE_DIRECTORY" ]]; then
    ARCHIVE_BACKUP="$(mktemp -d)"
    cp -r "$ARCHIVE_DIRECTORY/." "$ARCHIVE_BACKUP/"
    info "  ✓ Existing archive preserved"
fi

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp -a "$ROOT/src/." "$INSTALL_DIR/"

cp "$ROOT/uninstall.sh" "$INSTALL_DIR/uninstall.sh"

chmod 755 "$INSTALL_DIR/uninstall.sh"

if [[ -n "$MODEL_BACKUP" ]]; then
    mkdir -p "$INSTALL_DIR/battery_logs"
    cp "$MODEL_BACKUP" "$INSTALL_DIR/battery_logs/battery_charge_model.json"
    rm -f "$MODEL_BACKUP"
fi

if [[ -n "$SAMPLES_BACKUP" ]]; then
    mkdir -p "$INSTALL_DIR/battery_logs"
    cp "$SAMPLES_BACKUP" "$INSTALL_DIR/battery_logs/battery_charge_samples.json"
    rm -f "$SAMPLES_BACKUP"
fi

if [[ -n "$ARCHIVE_BACKUP" ]]; then
    mkdir -p "$INSTALL_DIR/battery_logs/archive"
    cp -r "$ARCHIVE_BACKUP/." "$INSTALL_DIR/battery_logs/archive/"
    rm -rf "$ARCHIVE_BACKUP"
fi

chmod 755 "$INSTALL_DIR/start.sh"

printf '  ✓ Runtime installed in %s\n' "$INSTALL_DIR"

info ""
info "Application runtime installed successfully."

# ---------------------------------------------------------------------------
# Application wrappers
# ---------------------------------------------------------------------------

info ""
info "Installing application wrappers..."

mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/viper-ultimate-tray" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$INSTALL_DIR/start.sh" "\$@"
EOF

chmod 755 "$BIN_DIR/viper-ultimate-tray"

printf '  ✓ Application launcher installed in %s\n' \
    "$BIN_DIR/viper-ultimate-tray"

cat "$ROOT/uninstall.sh" > "$BIN_DIR/viper-ultimate-tray-uninstall"

chmod 755 "$BIN_DIR/viper-ultimate-tray-uninstall"

printf '  ✓ Uninstall wrapper installed in %s\n' \
    "$BIN_DIR/viper-ultimate-tray-uninstall"

info ""
info "Application wrappers installed successfully."

# ---------------------------------------------------------------------------
# Desktop launcher
# ---------------------------------------------------------------------------

info ""
info "Installing desktop launcher..."

APPLICATIONS_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$APPLICATIONS_DIR/viper-ultimate-tray.desktop"

mkdir -p "$APPLICATIONS_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Viper Ultimate Tray
Comment=Viper Ultimate tray indicator
Exec=viper-ultimate-tray
Icon=$INSTALL_DIR/icons/menu/mouse.svg
Terminal=false
Categories=Utility;
EOF

chmod 644 "$DESKTOP_FILE"

kbuildsycoca6 >/dev/null 2>&1

printf '  ✓ Desktop launcher installed in %s\n' \
    "$DESKTOP_FILE"

info ""
info "Desktop launcher installed successfully."

# ---------------------------------------------------------------------------
# Application autostart
# ---------------------------------------------------------------------------

info ""
info "Configuring application autostart..."

AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/viper-ultimate-tray.desktop"
AUTOSTART_ENABLED=0

while true; do
    read -r -p \
        "Start Viper Ultimate Tray automatically with your session? [Y/n] " \
        AUTOSTART_CHOICE

    case "${AUTOSTART_CHOICE,,}" in
        ""|y|yes)
            mkdir -p "$AUTOSTART_DIR"

            cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Viper Ultimate Tray
Comment=Viper Ultimate tray indicator
Exec=$BIN_DIR/viper-ultimate-tray
Icon=$INSTALL_DIR/icons/menu/mouse.svg
Terminal=false
EOF

            chmod 644 "$AUTOSTART_FILE"

            AUTOSTART_ENABLED=1

            printf '  ✓ Autostart enabled in %s\n' \
                "$AUTOSTART_FILE"
            break
            ;;

        n|no)
            rm -f "$AUTOSTART_FILE"

            AUTOSTART_ENABLED=0

            printf '  ✓ Autostart disabled\n'
            break
            ;;

        *)
            printf '  ✗ Invalid choice. Please answer Y or N.\n'
            ;;
    esac
done

info ""
info "Autostart configuration applied successfully."

# ---------------------------------------------------------------------------
# Installation verification
# ---------------------------------------------------------------------------

info ""
info "Verifying installation..."

if [[ -d "$INSTALL_DIR" ]]; then
    printf '  ✓ Application runtime directory exists\n'
else
    check_failed "Application runtime directory does not exist"
fi

for required_file in \
    "$INSTALL_DIR/viper_ultimate_tray.py" \
    "$INSTALL_DIR/start.sh" \
    "$INSTALL_DIR/config/paths.py"
do
    if [[ -f "$required_file" ]]; then
        printf '  ✓ %s exists\n' "$(basename "$required_file")"
    else
        check_failed "Required runtime file is missing: $required_file"
    fi
done

if [[ -x "$INSTALL_DIR/start.sh" ]]; then
    printf '  ✓ start.sh is executable\n'
else
    check_failed "start.sh is not executable"
fi

if [[ -x "$HOME/.local/bin/viper-ultimate-tray" ]]; then
    printf '  ✓ Application wrapper exists and is executable\n'
else
    check_failed "Application wrapper is missing or not executable"
fi

if [[ -x "$HOME/.local/bin/viper-ultimate-tray-uninstall" ]]; then
    printf '  ✓ Uninstall wrapper exists and is executable\n'
else
    check_failed "Uninstall wrapper is missing or not executable"
fi

DESKTOP_FILE="$HOME/.local/share/applications/viper-ultimate-tray.desktop"

if [[ -f "$DESKTOP_FILE" ]]; then
    printf '  ✓ Desktop launcher exists\n'
else
    check_failed "Desktop launcher is missing"
fi

AUTOSTART_FILE="$HOME/.config/autostart/viper-ultimate-tray.desktop"

if (( AUTOSTART_ENABLED )); then
    if [[ -f "$AUTOSTART_FILE" ]]; then
        printf '  ✓ Autostart file exists\n'
    else
        check_failed "Autostart file is missing"
    fi
else
    if [[ ! -e "$AUTOSTART_FILE" ]]; then
        printf '  ✓ Autostart is disabled\n'
    else
        check_failed "Autostart file exists although autostart is disabled"
    fi
fi

info ""
info "Installation verification completed successfully."

info ""
info "Installation completed successfully."

info "Viper Ultimate Tray is ready to use."
