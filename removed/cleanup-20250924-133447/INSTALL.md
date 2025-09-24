# LXCloud Installation and Usage Guide

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Controller Types](#controller-types)
- [MQTT Protocol](#mqtt-protocol)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## Overview

LXCloud is a comprehensive cloud dashboard platform designed for managing IoT controllers with real-time data visualization and analytics. The platform supports multiple controller types and provides a user-friendly interface for monitoring and managing connected devices.

### Key Features

- **Real-time Dashboard**: Live map view with controller locations and status
- **Multi-user Support**: User authentication with role-based access control
- **Controller Management**: Bind, configure, and monitor controllers
- **Data Visualization**: Real-time charts and analytics
- **MQTT Integration**: Reliable data collection from controllers
- **Extensible Architecture**: Support for custom controller types via addons
- **Responsive Design**: Modern, mobile-friendly interface

## Requirements

### System Requirements
- Ubuntu 22.04 LTS (recommended)
- Python 3.8 or higher
- MariaDB 10.5 or higher
- Mosquitto MQTT Broker
- Nginx (for production)
- 2GB RAM minimum (4GB recommended)
- 10GB disk space minimum

### Python Dependencies
All dependencies are listed in `requirements.txt` and will be installed automatically.

## Installation

### Automatic Installation (Recommended)

1. **Download the installation script**:
   ```bash
   sudo bash scripts/install.sh
   ```

2. **The script will automatically**:
   - Install all required system packages
   - Set up MariaDB database
   - Configure Mosquitto MQTT broker
   - Install Python dependencies
   - Configure Nginx reverse proxy
   - Create systemd service
   - Set up firewall rules

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JeffMolenaar/LXCloud_2025.git
   cd LXCloud_2025
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv mariadb-server mosquitto nginx
   ```

3. **Create Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure database**:
   ```bash
   sudo mysql -e "CREATE DATABASE lxcloud;"
   sudo mysql -e "CREATE USER 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud123';"
   sudo mysql -e "GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';"
   ```

5. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**:
   ```bash
   python run.py
   # The application will create tables automatically
   ```

### Docker Installation

1. **Using Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Database Configuration
DB_HOST=localhost
DB_USER=lxcloud
DB_PASSWORD=your_secure_password
DB_NAME=lxcloud

# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=lxcloud

# Security
SECRET_KEY=your_secret_key_here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### Default Admin Account

After installation, you can log in with:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change the default admin password immediately after first login!

## Usage

### Starting the Application

#### Development Mode
```bash
python run.py
```

#### Production Mode (with Gunicorn)
```bash
gunicorn --config config/gunicorn.conf.py run:app
```

#### System Service
```bash
sudo systemctl start lxcloud
sudo systemctl enable lxcloud
```

### Web Interface

Access the web interface at:
- **Local**: http://localhost/
- **Network**: http://your-server-ip/

### User Management

#### Regular Users Can:
- View their bound controllers on the dashboard
- Bind new controllers by serial number
- Rename and configure their controllers
- View controller data and analytics
- Manage their profile and enable 2FA

#### Super Admins Can:
- Access all user and controller data
- Manage user accounts (reset passwords, disable 2FA)
- Customize the UI (CSS, headers, footers)
- Manage controller addons
- View system-wide analytics

### Controller Management

1. **Binding a Controller**:
   - Go to Controllers → Bind Controller
   - Enter the controller's serial number
   - The controller must have reported to the server at least once

2. **Configuring Controllers**:
   - Click Edit on any controller
   - Set display name and location coordinates
   - Location enables map display

3. **Viewing Data**:
   - Click the chart icon to view real-time data
   - Data is updated automatically every 30 seconds

## Controller Types

### Supported Controller Types

#### 1. Speed Radar (`speedradar`)
- Measures vehicle speeds
- Counts traffic volume
- Detects speed violations
- **Data Fields**: `speed_kmh`, `vehicle_count`, `average_speed`, `violations`

#### 2. Weather Station (`weatherstation`)
- Environmental monitoring
- Weather data collection
- **Data Fields**: `temperature_c`, `humidity_percent`, `pressure_hpa`, `wind_speed_kmh`, `wind_direction`, `rainfall_mm`

#### 3. Beaufort Meter (`beaufortmeter`)
- Wind measurement
- Beaufort scale calculation
- **Data Fields**: `wind_speed_kmh`, `beaufort_scale`, `wind_direction`, `gust_speed_kmh`, `air_density`

#### 4. AI Camera (`aicamera`)
- Computer vision analysis
- People and vehicle counting
- Motion detection
- **Data Fields**: `people_count`, `vehicle_count`, `motion_detected`, `light_level`, `recording`, `storage_used_percent`, `alerts`

### Adding Custom Controller Types

Admins can add new controller types through the Addon Management interface:

1. Go to Admin → Addon Management
2. Click "New Addon"
3. Define controller type and data fields
4. Configure display format and update intervals

## MQTT Protocol

### Topic Structure

Controllers should publish data to:
```
{topic_prefix}/{serial_number}/data
{topic_prefix}/{serial_number}/status
```

Default topic prefix: `lxcloud`

### Data Message Format

```json
{
  "type": "speedradar",
  "data": {
    "speed_kmh": 65.5,
    "vehicle_count": 3,
    "average_speed": 58.2,
    "violations": 1
  },
  "latitude": 52.3676,
  "longitude": 4.9041,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Status Message Format

```json
{
  "online": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Testing with Simulator

Use the included controller simulator for testing:

```bash
python scripts/controller_simulator.py --broker localhost --port 1883
```

This will simulate 5 different controllers sending realistic data.

## API Documentation

### Authentication

All API endpoints require authentication. Include the session cookie from web login.

### Endpoints

#### GET `/api/controllers/status`
Get real-time status of all accessible controllers.

#### GET `/api/controllers/{id}/recent-data?hours=24`
Get recent data for a specific controller.

#### GET `/api/stats/overview`
Get system overview statistics.

### Example API Usage

```bash
# Get controller status
curl -X GET http://localhost/api/controllers/status \
  -H "Cookie: session=your_session_cookie"

# Get recent data
curl -X GET http://localhost/api/controllers/1/recent-data?hours=6 \
  -H "Cookie: session=your_session_cookie"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check MariaDB status
sudo systemctl status mariadb

# Test database connection
mysql -u lxcloud -p -h localhost lxcloud
```

#### 2. MQTT Connection Failed
```bash
# Check Mosquitto status
sudo systemctl status mosquitto

# Test MQTT connectivity
mosquitto_pub -h localhost -t test/topic -m "test message"
mosquitto_sub -h localhost -t test/topic
```

#### 3. Application Won't Start
```bash
# Check application logs
sudo journalctl -u lxcloud -f

# Check Python dependencies
pip install -r requirements.txt
```

#### 4. Controllers Not Appearing
- Verify MQTT broker is running
- Check controller is publishing to correct topics
- Ensure serial numbers are correct
- Check firewall settings for port 1883

### Log Files

- **Application logs**: `/var/log/lxcloud/`
- **Nginx logs**: `/var/log/nginx/`
- **System logs**: `journalctl -u lxcloud`
- **MQTT logs**: `/var/log/mosquitto/`

### Useful Commands

```bash
# Check service status
sudo systemctl status lxcloud

# Restart services
sudo systemctl restart lxcloud
sudo systemctl restart mosquitto
sudo systemctl restart nginx

# View live logs
sudo journalctl -u lxcloud -f

# Test MQTT
mosquitto_sub -h localhost -t 'lxcloud/+/data'

# Database backup
mysqldump -u lxcloud -p lxcloud > backup.sql
```

### Performance Optimization

#### For High Traffic
1. Increase Gunicorn workers: Edit `config/gunicorn.conf.py`
2. Optimize database: Add indexes for frequently queried fields
3. Enable Redis caching for session storage
4. Use connection pooling for database connections

#### For Many Controllers
1. Increase MQTT connection limits in `config/mosquitto.conf`
2. Implement data aggregation for historical storage
3. Use time-series database for analytics (InfluxDB)
4. Implement data retention policies

### Updating LXCloud

To update to the latest version:

```bash
sudo bash scripts/update.sh
```

The update script will:
- Create a backup of the current installation
- Download the latest version
- Preserve configuration and data
- Update dependencies
- Restart services

### Support

For technical support:
1. Check the logs for error messages
2. Verify all services are running
3. Test MQTT connectivity
4. Check database connectivity
5. Review configuration files

For bug reports or feature requests, please create an issue in the GitHub repository.