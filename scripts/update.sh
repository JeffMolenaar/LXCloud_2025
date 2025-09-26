#!/usr/bin/env bash
set -euo pipefail

# Update script for LXCloud
# Safely sync changes from the cloned repo into the deployed installation.
# Usage: sudo ./scripts/update.sh [--install-dir /home/lxcloud/LXCloud] [--yes]

NONINTERACTIVE=false
# Use same defaults as install.sh
SERVICE_USER="lxcloud"
INSTALL_DIR="/home/$SERVICE_USER/LXCloud"
DEBUG_QUEUE_DIR="/home/$SERVICE_USER/debug_queue"

print_usage() {
    cat <<'USAGE'
Usage: sudo ./scripts/update.sh [--install-dir DIR] [--yes]

Options:
  --install-dir DIR   Force target installation directory (default: auto-detect)
  --yes               Run non-interactive (no prompts)
  --help              Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-dir)
            INSTALL_DIR="$2"; shift 2;;
        --yes)
            NONINTERACTIVE=true; shift;;
        --help)
            print_usage; exit 0;;
        *)
            echo "Unknown arg: $1"; print_usage; exit 1;;
    esac
done

# Determine script and repo roots
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# If the user didn't override INSTALL_DIR and a variant exists, prefer an existing path
if [ -z "${INSTALL_DIR:-}" ] || [ ! -d "$INSTALL_DIR" ]; then
    if [ -d "/home/$SERVICE_USER/LXCloud" ]; then
        INSTALL_DIR="/home/$SERVICE_USER/LXCloud"
    elif [ -d "/home/$SERVICE_USER/LXCloud_2025" ]; then
        INSTALL_DIR="/home/$SERVICE_USER/LXCloud_2025"
    fi
fi

echo "Repo root: $REPO_ROOT"
echo "Target install dir: $INSTALL_DIR"

if [ "$NONINTERACTIVE" = false ]; then
    read -p "Proceed with updating $INSTALL_DIR from repository at $REPO_ROOT? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted by user."; exit 1
    fi
fi

# Make sure target exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Target installation directory does not exist: $INSTALL_DIR"
    echo "Create it first or pass --install-dir to point to the correct install path.";
    exit 1
fi

# Backup important parts (templates, app, scripts) but exclude venv and large runtime files
TS=$(date +%s)
BACKUP="${INSTALL_DIR}.backup.${TS}.tar.gz"
echo "Creating backup (templates, app, scripts, config) -> $BACKUP"
tar --warning=no-file-changed -czf "$BACKUP" -C "$INSTALL_DIR" \
    templates app project scripts database.conf* database.conf || true

# Determine source directory to copy from (prefer project/ if present)
if [ -d "$REPO_ROOT/project" ]; then
    SRC="$REPO_ROOT/project/"
else
    SRC="$REPO_ROOT/"
fi

echo "Using source: $SRC"

# Helper: rsync with --chown if available
safe_rsync() {
    local src="$1"
    local dst="$2"
    if rsync --version >/dev/null 2>&1 && rsync --help 2>/dev/null | grep -q -- '--chown'; then
        rsync -a --delete --chown="$SERVICE_USER:$SERVICE_USER" --exclude='.git' --exclude='removed' --exclude='archive' "$src" "$dst/"
    else
        rsync -a --delete --exclude='.git' --exclude='removed' --exclude='archive' "$src" "$dst/"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$dst"
    fi
}

echo "Stopping service lxcloud (if present)"
if systemctl list-units --full -all | grep -q '^lxcloud.service'; then
    systemctl stop lxcloud || true
fi

echo "Syncing files to $INSTALL_DIR"
safe_rsync "$SRC" "$INSTALL_DIR"

# Ensure .github/copilot-instructions.md is present in the install dir so local operators
# and any automation can read the repo-specific Copilot instructions. Some deployments
# put code in `project/` (which excludes .github), so copy it explicitly if present.
if [ -f "$REPO_ROOT/.github/copilot-instructions.md" ]; then
    mkdir -p "$INSTALL_DIR/.github"
    cp "$REPO_ROOT/.github/copilot-instructions.md" "$INSTALL_DIR/.github/copilot-instructions.md"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.github"
fi

echo "Ensuring ownership"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" || true

# Ensure debug queue exists with correct ownership
mkdir -p "$DEBUG_QUEUE_DIR" || true
chown "$SERVICE_USER:$SERVICE_USER" "$DEBUG_QUEUE_DIR" || true
chmod 755 "$DEBUG_QUEUE_DIR" || true

# Make common scripts executable in the installed tree
if [ -d "$INSTALL_DIR/scripts" ]; then
    find "$INSTALL_DIR/scripts" -type f -name "*.sh" -exec chmod +x {} \; || true
fi

# Ensure database install script if present is executable
if [ -f "$INSTALL_DIR/database_install.sh" ]; then
    chmod +x "$INSTALL_DIR/database_install.sh" || true
fi

# Install/upgrade python requirements if venv exists
if [ -d "$INSTALL_DIR/venv" ]; then
    echo "Installing Python requirements into existing virtualenv..."
    sudo -u "$SERVICE_USER" -H bash -c "source '$INSTALL_DIR/venv/bin/activate' && python -m pip install --upgrade pip && pip install -r '$INSTALL_DIR/requirements.txt'"
else
    echo "No virtualenv found at $INSTALL_DIR/venv - skipping dependency install."
fi

# Run a quick create_app smoke-test to detect import-time errors early and ensure app
# will start correctly. We run as SERVICE_USER and print traceback if it fails.
if [ -d "$INSTALL_DIR/venv" ]; then
    echo "Running create_app smoke-test..."
    if sudo -u "$SERVICE_USER" -H bash -c "cd '$INSTALL_DIR' && source venv/bin/activate && python - <<PY
try:
    from app import create_app
    app = create_app()
    print('CREATE_APP_OK')
except Exception:
    import traceback
    traceback.print_exc()
    raise
PY"; then
        echo "create_app smoke-test passed"
    else
        echo "Warning: create_app smoke-test failed. Continuing but check logs." >&2
    fi
fi

echo "Restarting services and reloading systemd"
systemctl daemon-reload || true
if systemctl list-units --full -all | grep -q '^lxcloud.service'; then
    systemctl enable --now lxcloud || systemctl start lxcloud || true
fi

# Restart common system services that the application depends on to ensure changes
# take effect immediately on the host.
if systemctl list-units --full -all | grep -q '^nginx.service'; then
    systemctl restart nginx || true
fi
if systemctl list-units --full -all | grep -q '^mosquitto.service'; then
    systemctl restart mosquitto || true
fi

echo "Update complete. Recent lxcloud journal entries:"
journalctl -u lxcloud -n 200 --no-pager || true

echo "Run the create_app smoke-test manually or via:"
echo "  sudo -u lxcloud -H bash -c \"cd $INSTALL_DIR && source venv/bin/activate && python - <<'PY'\nfrom app import create_app\napp = create_app(); print('CREATE_APP_OK')\nPY\""

exit 0
