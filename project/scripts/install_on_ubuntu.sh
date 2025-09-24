#!/usr/bin/env bash
set -euo pipefail

# Simple install script for Ubuntu Server LTS
# Usage (on remote server in /home/lxcloud):
#   chmod +x project/scripts/install_on_ubuntu.sh
#   sudo ./project/scripts/install_on_ubuntu.sh

PROJECT_DIR="/home/lxcloud/LXCloud_2025"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS="$PROJECT_DIR/project/requirements.txt"
RUN_CMD="python3 run.py"
LOGFILE="$PROJECT_DIR/run.log"

echo "Starting LXCloud install in $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "ERROR: project directory $PROJECT_DIR does not exist"
  exit 2
fi

# Update & basic packages
echo "Updating apt and installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git curl

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
echo "Activating virtualenv"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Upgrade pip and install requirements
echo "Upgrading pip and installing requirements"
python -m pip install --upgrade pip setuptools wheel
if [ -f "$REQUIREMENTS" ]; then
  pip install -r "$REQUIREMENTS"
else
  echo "WARNING: requirements file not found at $REQUIREMENTS"
fi

# Ensure file permissions
echo "Setting file permissions"
chown -R $(whoami):$(whoami) "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/project/run.py" || true

# Optionally copy example configs if not present
if [ -f "$PROJECT_DIR/project/database.conf.example" ] && [ ! -f "$PROJECT_DIR/project/database.conf" ]; then
  echo "Copying example database config"
  cp "$PROJECT_DIR/project/database.conf.example" "$PROJECT_DIR/project/database.conf"
fi

# Migrate DB if your project uses migration scripts
# (This project may use custom scripts; run them here if needed.)
# Example placeholder:
# if [ -f "$PROJECT_DIR/scripts/migrate_db.sh" ]; then
#   bash "$PROJECT_DIR/scripts/migrate_db.sh"
# fi

# Start the app in the background (for testing)
# You can replace this with a systemd unit for production.
echo "Starting application (background, logs -> $LOGFILE)"
cd "$PROJECT_DIR"
nohup "$VENV_DIR/bin/python" project/run.py > "$LOGFILE" 2>&1 &

sleep 1
if ps aux | grep -q "project/run.py"; then
  echo "Application started successfully (check $LOGFILE)"
else
  echo "Application failed to start; check $LOGFILE"
  tail -n 50 "$LOGFILE" || true
fi

echo "Install script finished."