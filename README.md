# LXCloud - IoT Controller Management Platform

LXCloud is a comprehensive cloud-based dashboard platform for managing IoT controllers and visualizing their data. The platform supports real-time data collection via MQTT, user management with 2FA, and an extensible architecture for future enhancements.

## Features

### Core Platform Features
- **Real-time Dashboard** with live controller status monitoring
- **Interactive Map View** showing controller locations and status
- **User Authentication** with JWT and optional 2FA (TOTP)
- **Role-based Access Control** (regular users vs administrators)
- **MQTT Integration** for real-time controller data collection
- **WebSocket Support** for live UI updates
- **Responsive Web Interface** built with Bootstrap 5

### Supported Controller Types
- **Speed Radar** - Vehicle speed and traffic monitoring
- **Beaufort Meter** - Wind speed and direction measurement
- **Weather Station** - Comprehensive weather data collection
- **AI Camera** - Intelligent video monitoring and analysis
- **Extensible Architecture** for future controller types

### User Features
- **Controller Management**: Bind, configure, and monitor controllers
- **Dashboard**: Real-time status overview with mini-map
- **Map View**: Interactive map showing all controller locations
- **Profile Management**: Update personal information and security settings
- **Two-Factor Authentication**: Enhanced security with TOTP support

### Administrator Features
- **System-wide Controller Management**: View and manage all controllers
- **User Administration**: Manage user accounts, reset passwords, disable 2FA
- **UI Customization**: Customize interface appearance (planned)
- **Addon Management**: Extensible plugin system (planned)
- **System Monitoring**: Comprehensive platform oversight

## Technology Stack

### Backend
- **Node.js** with Express.js framework
- **MariaDB** database with connection pooling
- **MQTT.js** for IoT device communication
- **Socket.IO** for real-time web updates
- **JWT** authentication with refresh tokens
- **Speakeasy** for 2FA implementation
- **Winston** for comprehensive logging

### Frontend
- **EJS** templating engine
- **Bootstrap 5** for responsive UI
- **FontAwesome** for icons
- **Leaflet.js** for interactive maps
- **Socket.IO Client** for real-time updates

### Security & Infrastructure
- **Helmet.js** for security headers
- **Rate Limiting** for API protection
- **Input Validation** with express-validator
- **Nginx** reverse proxy configuration
- **Systemd** service management

## Quick Start

### Prerequisites
- Ubuntu Server LTS 22.04 (recommended and tested)
- Regular user account with sudo privileges
- Internet connection
- At least 2GB RAM and 10GB disk space

### 🚀 One-Command Installation

1. **Clone the repository:**
```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025
```

2. **Run the Ubuntu 22.04 LTS installation script:**
```bash
./scripts/install-ubuntu-22.04.sh
```

**Alternative:** For other Ubuntu versions, try:
```bash
./scripts/install-new.sh
```

### ✨ What the installer does automatically:

- **🧹 Cleans up** any previous LXCloud installations
- **📦 Installs** Node.js 18.x, MariaDB, Mosquitto MQTT, and Nginx (optimized for Ubuntu 22.04)
- **🔧 Configures** all services with optimal settings for Ubuntu 22.04 LTS
- **🗄️ Creates** database schema and default admin user
- **🔐 Sets up** systemd services and firewall rules
- **🔑 Generates** secure JWT secrets and passwords
- **🌐 Configures** Nginx with local network optimizations (no HTTPS redirect)
- **✅ Verifies** all services are running correctly
- **🔧 Creates** maintenance and diagnostic scripts

### 🌐 Access Your Installation

After installation completes:

- **Web Interface:** `http://your-server-ip`
- **Default Credentials:**
  - Email: `admin@lxcloud.local`
  - Password: `admin123`

**⚠️ IMPORTANT:** Change the default password immediately after first login!

### 🔧 Post-Installation Management

The installer creates helpful management scripts:

```bash
# Check system status and health
sudo /opt/lxcloud/status.sh

# Run comprehensive diagnostics
sudo /opt/lxcloud/diagnose.sh

# Test installation completely
sudo /opt/lxcloud/../scripts/test-installation.sh

# View live logs
sudo journalctl -u lxcloud -f

# Update LXCloud
sudo /opt/lxcloud/update.sh

# Create backup
sudo /opt/lxcloud/backup.sh

# Restart services
sudo systemctl restart lxcloud
```

### Post-Installation Setup

1. **Configure SSL/TLS (recommended):**
```bash
sudo certbot --nginx
```

2. **Update admin credentials:**
- Login to the web interface
- Go to Profile Settings
- Change password and email address
- Enable 2FA for enhanced security

## Controller Integration

### MQTT Topics
Controllers communicate using the following MQTT topic structure:

```
lxcloud/controllers/{serial_number}/register  - Controller registration
lxcloud/controllers/{serial_number}/data      - Data transmission
lxcloud/controllers/{serial_number}/status    - Status updates
```

### Registration Message Format
```json
{
  "type": "weatherstation",
  "latitude": 52.5200,
  "longitude": 13.4050,
  "name": "Weather Station 001"
}
```

### Data Message Format
```json
{
  "data": {
    "temperature": 23.5,
    "humidity": 65,
    "pressure": 1013.25
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Status Message Format
```json
{
  "status": "online",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Development

### Local Development Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your local settings
```

3. **Set up database:**
```bash
# Run the database setup script to create lxcloud user
npm run setup-db

# Or manually create the database user:
mysql -u root -p
CREATE DATABASE IF NOT EXISTS lxcloud;
CREATE USER IF NOT EXISTS 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud';
GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

4. **Test database connection:**
```bash
npm run test-db
```

5. **Start development server:**
```bash
npm run dev
```

### Available Scripts
- `npm start` - Start production server
- `npm run dev` - Start development server with nodemon
- `npm test` - Run test suite
- `npm run setup-db` - Initialize database schema and create lxcloud user
- `npm run init-db` - Automated database setup for localhost (bash script)
- `npm run test-db` - Test database connection

## Updating

To update LXCloud to the latest version:

```bash
sudo /opt/lxcloud/update.sh
```

The update script will:
- Create a backup of the current installation
- Pull latest changes from Git
- Update dependencies
- Run database migrations
- Restart services
- Clean up old backups

## Configuration

### Environment Variables
Key configuration options in `.env`:

```env
# Database
DB_HOST=localhost
DB_NAME=lxcloud
DB_USER=lxcloud
DB_PASSWORD=lxcloud

# MQTT
MQTT_BROKER_URL=mqtt://localhost:1883
MQTT_USERNAME=lxcloud_mqtt
MQTT_PASSWORD=your_mqtt_password

# Security
JWT_SECRET=your_jwt_secret
SESSION_SECRET=your_session_secret
```

### Service Management
```bash
# View logs
sudo journalctl -u lxcloud -f

# Restart service
sudo systemctl restart lxcloud

# Check status
sudo systemctl status lxcloud
```

## Architecture

### Database Schema
The platform uses a comprehensive database schema with the following key tables:
- `users` - User accounts and authentication
- `controllers` - IoT device registry
- `controller_data` - Time-series data from devices
- `sessions` - User session management
- `ui_customizations` - Interface customization settings
- `addons` - Extensible plugin system

### Security Features
- **Password Hashing** with bcrypt (configurable rounds)
- **JWT Authentication** with refresh tokens
- **Rate Limiting** on sensitive endpoints
- **Input Validation** on all user inputs
- **CSRF Protection** via session tokens
- **Security Headers** via Helmet.js

### Real-time Architecture
- **MQTT Broker** receives data from IoT controllers
- **Node.js Service** processes MQTT messages
- **Database** stores controller data and state
- **WebSocket** pushes updates to connected clients
- **Frontend** updates UI in real-time

## Troubleshooting

### Common Issues and Solutions

#### 🔌 "Unable to connect to server"

**Symptoms:** Browser shows connection errors, timeouts, or "This site can't be reached"

**Quick Fix (Most Common):**
```bash
# Run the comprehensive test script first
sudo /opt/lxcloud/../scripts/test-installation.sh

# If tests fail, restart all services
sudo systemctl restart lxcloud nginx mariadb mosquitto

# Check status
sudo /opt/lxcloud/status.sh
```

**Detailed Troubleshooting:**

1. **Services not running:**
   ```bash
   # Check service status
   sudo /opt/lxcloud/status.sh
   
   # Check individual services
   sudo systemctl status lxcloud nginx mariadb mosquitto
   
   # Restart failed services
   sudo systemctl restart lxcloud nginx mariadb mosquitto
   ```

2. **Database connection issues:**
   ```bash
   # Test database connection
   mysql -u lxcloud -plxcloud lxcloud -e "SELECT 1"
   
   # If connection fails, check MariaDB
   sudo systemctl status mariadb
   sudo journalctl -u mariadb -n 20
   
   # Restart MariaDB
   sudo systemctl restart mariadb
   ```

3. **Application startup issues:**
   ```bash
   # Check application logs
   sudo journalctl -u lxcloud -n 50
   
   # Check if port 3000 is in use
   sudo ss -tlnp | grep :3000
   
   # Restart LXCloud service
   sudo systemctl restart lxcloud
   ```

4. **Firewall blocking connections:**
   ```bash
   # Check firewall status
   sudo ufw status
   
   # Allow HTTP traffic
   sudo ufw allow 'Nginx Full'
   
   # Allow application port for local networks
   sudo ufw allow from 192.168.0.0/16 to any port 3000
   ```

5. **Nginx configuration issues:**
   ```bash
   # Test nginx configuration
   sudo nginx -t
   
   # Check nginx status
   sudo systemctl status nginx
   
   # Restart nginx
   sudo systemctl restart nginx
   ```

6. **Wrong IP address:**
   ```bash
   # Find your server's IP
   hostname -I
   
   # Try accessing via localhost first
   curl http://localhost
   
   # Test API endpoint
   curl http://localhost:3000/api/health
   ```

7. **Node.js/NPM issues:**
   ```bash
   # Check Node.js version
   node --version
   
   # Should be v18.x or higher
   # If not, reinstall Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

8. **Run comprehensive diagnostics:**
   ```bash
   # This will check everything
   sudo /opt/lxcloud/diagnose.sh
   ```

#### 🗄️ Database Connection Issues

**Symptoms:** Error messages about database connections in logs

**Solutions:**
```bash
# Check MariaDB status
sudo systemctl status mariadb

# Test database connection
mysql -u lxcloud -plxcloud lxcloud -e "SELECT 1"

# Restart MariaDB
sudo systemctl restart mariadb

# Check if database exists
mysql -u root -e "SHOW DATABASES"
```

#### 📡 MQTT Connection Problems

**Symptoms:** MQTT connection errors in logs, controllers not appearing

**Solutions:**
```bash
# Check Mosquitto status
sudo systemctl status mosquitto

# Test MQTT connection
mosquitto_pub -h localhost -u lxcloud_mqtt -P [password] -t test -m "hello"

# Check MQTT logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Restart Mosquitto
sudo systemctl restart mosquitto
```

#### 🔐 Permission Issues

**Symptoms:** File permission errors, service start failures

**Solutions:**
```bash
# Fix file ownership
sudo chown -R lxcloud:lxcloud /opt/lxcloud

# Fix script permissions
sudo chmod +x /opt/lxcloud/*.sh

# Fix log directory permissions
sudo mkdir -p /opt/lxcloud/logs
sudo chown lxcloud:lxcloud /opt/lxcloud/logs
```

#### 🌐 HTTPS Redirect Issues

**Symptoms:** Getting redirected to HTTPS when trying to access via HTTP

**Solutions:**

The new installer prevents this issue, but if you still experience it:

```bash
# Check nginx configuration
sudo nginx -t

# Ensure no HTTPS redirects for local networks
sudo grep -r "return.*https" /etc/nginx/sites-available/

# Restart nginx
sudo systemctl restart nginx
```

#### 🚨 Emergency Recovery

If the system is completely broken:

1. **Complete reinstall:**
   ```bash
   cd LXCloud_2025
   ./scripts/install-new.sh
   ```

2. **Restore from backup:**
   ```bash
   # List available backups
   ls -la /opt/lxcloud/backups/
   
   # Restore database
   mysql -u lxcloud -plxcloud lxcloud < /opt/lxcloud/backups/database_YYYYMMDD_HHMMSS.sql
   ```

3. **Check system resources:**
   ```bash
   # Check disk space
   df -h
   
   # Check memory usage
   free -h
   
   # Check system load
   top
   ```

#### 📋 Getting Help

1. **Check system status:**
   ```bash
   sudo /opt/lxcloud/status.sh
   ```

2. **Collect diagnostic information:**
   ```bash
   # System info
   uname -a
   cat /etc/os-release
   
   # Service logs
   sudo journalctl -u lxcloud --no-pager -n 50
   sudo journalctl -u nginx --no-pager -n 50
   sudo journalctl -u mariadb --no-pager -n 50
   
   # Network info
   ss -tlnp | grep -E ':(80|443|3000|1883|3306)'
   ```

3. **Common commands for troubleshooting:**
   ```bash
   # Test web interface
   curl -I http://localhost:3000/api/health
   
   # Test database
   mysql -u lxcloud -plxcloud -e "SELECT 1"
   
   # Test MQTT
   mosquitto_pub -h localhost -u lxcloud_mqtt -P [password] -t test -m hello
   
   # Check file permissions
   ls -la /opt/lxcloud/
   ```

### Performance Optimization

If you experience slow performance:

1. **Monitor resource usage:**
   ```bash
   htop
   iotop
   nethogs
   ```

2. **Optimize database:**
   ```bash
   # From the admin panel, or manually:
   mysql -u lxcloud -plxcloud lxcloud -e "OPTIMIZE TABLE users, controllers, controller_data"
   ```

3. **Clean up old data:**
   ```bash
   # Clean old logs
   sudo journalctl --vacuum-time=7d
   
   # Clean old backups
   find /opt/lxcloud/backups -name "*.sql" -mtime +30 -delete
   ```

For additional help, check the project's GitHub issues or create a new issue with your diagnostic information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and documentation:
- Check the troubleshooting section above
- Review the logs: `sudo journalctl -u lxcloud -f`
- Open an issue on GitHub

## Version History

- **v1.0.0** - Initial release with core functionality
  - User authentication and management
  - Controller binding and monitoring
  - Real-time dashboard and map view
  - MQTT integration
  - Admin panel basics