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
- Ubuntu Server LTS 24.04
- Root or sudo access
- Internet connection

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025
```

2. **Run the installation script:**
```bash
sudo ./scripts/install.sh
```

The installation script will automatically:
- Install Node.js, MariaDB, Mosquitto MQTT, and Nginx
- Configure all services and security settings
- Create database schema and default admin user
- Set up systemd services and firewall rules
- Generate secure configuration files

3. **Access the platform:**
- Open your browser and navigate to `http://your-server-ip`
- Login with default credentials:
  - Email: `admin@lxcloud.local`
  - Password: `admin123`
- **Important**: Change the default password immediately!

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
# Run the database setup script to create lxadmin user
npm run setup-db

# Or manually create the database user:
mysql -u root -p
CREATE DATABASE IF NOT EXISTS lxcloud;
CREATE USER IF NOT EXISTS 'lxadmin'@'localhost' IDENTIFIED BY 'lxadmin';
GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxadmin'@'localhost';
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
- `npm run setup-db` - Initialize database schema and create lxadmin user
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
DB_USER=lxadmin
DB_PASSWORD=lxadmin

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

### Common Issues

**HTTPS redirect preventing local network login:**
If you're getting HTTPS redirects that prevent login from your local network (192.168.x.x, 10.x.x.x), run the fix script:
```bash
sudo /opt/lxcloud/scripts/fix-https-redirect.sh
```

This commonly happens after running `certbot --nginx` which modifies the nginx configuration to force HTTPS redirects. The fix script restores HTTP access for local networks while maintaining SSL for external access.

**Service won't start:**
```bash
sudo journalctl -u lxcloud -n 50
```

**Database connection issues:**
```bash
sudo systemctl status mariadb
sudo mysql -u lxadmin -p lxcloud
# Or test the connection:
npm run test-db
```

**MQTT connection problems:**
```bash
sudo systemctl status mosquitto
mosquitto_pub -h localhost -u lxcloud_mqtt -P your_password -t test -m "hello"
```

**Permission issues:**
```bash
sudo chown -R lxcloud:lxcloud /opt/lxcloud
sudo chmod +x /opt/lxcloud/scripts/*.sh
```

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