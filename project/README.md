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

See `scripts/install.sh` for Ubuntu 22.04 LTS installation instructions.

## Version
Current Version: V1.0.0

## Architecture
- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: MariaDB
- **MQTT**: Mosquitto for controller communication
- **Frontend**: Modern HTML5/CSS3/JavaScript with Leaflet maps
- **Authentication**: JWT with 2FA support