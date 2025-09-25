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

echo "Running DB migration: ensure ui_customization.map_config column exists (idempotent)"
cd "$PROJECT_DIR"
"$VENV_DIR/bin/python" - <<'PY'
import os
import sys
from pathlib import Path

# Ensure the 'project' package folder is importable (we run from PROJECT_DIR)
project_path = os.path.join(os.getcwd(), 'project')
if project_path not in sys.path:
  sys.path.insert(0, project_path)

try:
  from app import create_app
  from app.models import db
except Exception as e:
  print('Failed to import app package after adding project to sys.path:', e)
  raise

app = create_app()
with app.app_context():
  conn = db.engine.connect()
  try:
    url = app.config.get('SQLALCHEMY_DATABASE_URI', '') or ''
    # SQLite path
    if url.startswith('sqlite'):
      res = conn.execute(db.text("PRAGMA table_info(ui_customization)")).fetchall()
      cols = [r[1] for r in res]
      if 'map_config' not in cols:
        conn.execute(db.text("ALTER TABLE ui_customization ADD COLUMN map_config TEXT"))
        print('Added map_config column to ui_customization (sqlite)')
      else:
        print('map_config column already present (sqlite)')
    else:
      # Try MySQL/MariaDB via INFORMATION_SCHEMA
      try:
        db_name = url.rsplit('/', 1)[-1]
        res = conn.execute(db.text(
          "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
          "WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = 'ui_customization'"
        ), {"db_name": db_name}).fetchall()
        cols = [r[0] for r in res]
        if 'map_config' not in cols:
          conn.execute(db.text("ALTER TABLE ui_customization ADD COLUMN map_config TEXT"))
          print('Added map_config column to ui_customization (mysql)')
        else:
          print('map_config column already present (mysql)')
      except Exception as e:
        print('Could not determine MySQL schema or perform migration:', e)
  except Exception as e:
    print('Migration check failed or not needed:', e)
  finally:
    conn.close()
PY

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