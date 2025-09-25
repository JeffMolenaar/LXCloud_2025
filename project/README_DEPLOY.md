LXCloud - Ubuntu deploy & smoke-test

This README explains how to deploy LXCloud on Ubuntu (idempotent) and run the included smoke tests.

Quick steps (assumes you are on Ubuntu 22.04/24.04 and have python3 installed):

1. Clone repository and run deploy script

```bash
git clone <repo-url> lxcloud
cd lxcloud/project
sudo bash scripts/ubuntu_deploy.sh main
```

2. Edit the generated `.env.deploy` file in the project root and set `SECRET_KEY` and `SQLALCHEMY_DATABASE_URI` (if using MySQL). Be careful with secrets.

3. Start the app with systemd (see example unit in `scripts/lxcloud.service.example`)

```bash
sudo cp scripts/lxcloud.service.example /etc/systemd/system/lxcloud.service
sudo systemctl daemon-reload
sudo systemctl enable --now lxcloud.service
sudo journalctl -u lxcloud.service -f
```

4. Run smoke tests

```bash
# Ensure app runs on 127.0.0.1:5000
bash scripts/smoke_test.sh http://127.0.0.1:5000
```

5. Check smoke results in `project/scripts/smoke_results/` and share them when asking for debugging help.

Notes:
- The deploy script will create a Python virtual environment in `project/.venv`.
- The deploy script will create `.env.deploy` with a default SECRET_KEY if not present — replace it with a secure random value in production.
- If you are using MySQL/MariaDB, populate `SQLALCHEMY_DATABASE_URI` in `.env.deploy` and ensure MariaDB is reachable.
- All heavy debugging should be performed on Ubuntu; the repository includes tooling to make that simple.
