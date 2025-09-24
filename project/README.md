# LXCloud - Cloud Dashboard Platform

LXCloud is a comprehensive cloud dashboard platform for managing IoT controllers with real-time data visualization and analytics.

## Features

### For Regular Users
- **Dashboard**: Live map view with controller locations and status monitoring
- **Controller Management**: Bind controllers by serial number, rename, remove, and view data
- **User Management**: Profile management, 2FA support, account settings

### For Super Admins
- **Advanced Dashboard**: Full access to all controllers and users
- **User Administration**: Manage all users, reset 2FA, delete accounts
- **UI Customization**: Custom CSS, header/footer modification, map marker customization
- **Addon Management**: Add, remove, and edit controller type addons

## Supported Controller Types
- Speed Radar
- Beaufort Meter
- Weather Station
- AI Camera
- Extensible for future controller types

## Installation

See `scripts/install.sh` for Ubuntu 22.04/24.04 LTS installation instructions.

Important installer notes:

- The installer can automatically install MariaDB and create the application database and user. If your MariaDB root account requires a password, run the installer with the `MYSQL_ROOT_PASSWORD` environment variable, or you will be prompted interactively:

```bash
sudo MYSQL_ROOT_PASSWORD='YourRootPass' bash scripts/install.sh
```

- When the installer auto-generates the default `admin` user, the credentials are saved to `/etc/lxcloud/admin_credentials` with strict permissions (owner root, mode 600). The installer no longer prints plaintext admin credentials to stdout for security.

## Version

Current Version: V1.0.0

## Architecture

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: MariaDB
- **MQTT**: Mosquitto for controller communication
- **Frontend**: Modern HTML5/CSS3/JavaScript with Leaflet maps
- **Authentication**: JWT with 2FA support
