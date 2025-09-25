#!/usr/bin/env bash
# Ubuntu idempotent deploy script for LXCloud
# Usage: sudo bash ubuntu_deploy.sh [branch]
# This script pulls latest code, creates venv, installs deps, creates DB, and restarts systemd service.

set -euo pipefail
BRANCH=${1:-main}
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
VENVDIR="$PROJECT_DIR/.venv"
SERVICE_NAME=lxcloud

echo "Deploying LXCloud from branch: $BRANCH"
cd "$PROJECT_DIR"

# Ensure we are on the right branch and pull
if [ -d .git ]; then
  git fetch origin
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  echo "No .git found in $PROJECT_DIR. Please clone the repository first." >&2
  exit 1
fi

# Create venv if missing
if [ ! -d "$VENVDIR" ]; then
  python3 -m venv "$VENVDIR"
fi

# Activate venv and install dependencies
source "$VENVDIR/bin/activate"
python -m pip install --upgrade pip
pip install -r requirements.txt

# Ensure uploads folder exists and writable by service user
mkdir -p "$PROJECT_DIR/static/uploads"
chmod 775 "$PROJECT_DIR/static/uploads"

# Ensure environment variables file exists
ENV_FILE="$PROJECT_DIR/.env.deploy"
if [ ! -f "$ENV_FILE" ]; then
  echo "SECRET_KEY='change-me-in-production'" > "$ENV_FILE"
  echo "# You should set SQLALCHEMY_DATABASE_URI in this file for production" >> "$ENV_FILE"
  echo "Created $ENV_FILE with default values. Edit as needed." >&2
fi

# Source env file (do not export sensitive values here in logs)
set -a
. "$ENV_FILE"
set +a

# Run DB migrations / create tables as fallback
python - <<'PY'
from app import create_app
from app.models import db
app = create_app()
with app.app_context():
    try:
        db.create_all()
        print('Database tables ensured (create_all executed)')
    except Exception as e:
        print('Database create_all failed:', e)
PY

# Create systemd unit (if not exists) - copy example or instruct
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
if [ ! -f "$UNIT_PATH" ]; then
  echo "Systemd unit $UNIT_PATH not found. Creating example unit at $PROJECT_DIR/scripts/lxcloud.service.example"
  echo "Please review and copy it to $UNIT_PATH (sudo), then run: sudo systemctl daemon-reload && sudo systemctl enable --now ${SERVICE_NAME}"
fi

# Restart service if present
if systemctl list-units --full -all | grep -Fq "${SERVICE_NAME}.service"; then
  echo "Restarting ${SERVICE_NAME} service..."
  sudo systemctl daemon-reload
  sudo systemctl restart "${SERVICE_NAME}.service"
  sudo systemctl status "${SERVICE_NAME}.service" --no-pager
else
  echo "Service ${SERVICE_NAME} not managed by systemd. You can start app manually:"
  echo "Source $VENVDIR/bin/activate && FLASK_ENV=production SECRET_KEY=\"$SECRET_KEY\" python3 run.py &> lxcloud.log &"
fi

echo "Deploy script finished."