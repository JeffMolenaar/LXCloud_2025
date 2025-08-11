# LXCloud Complete IoT Platform

A comprehensive IoT cloud management platform with MariaDB database integration, real-time MQTT communication, and enhanced super admin interface.

## 🚀 Quick Start

### One-Command Setup
```bash
./setup.sh
```

This single command installs and configures:
- ✅ MariaDB Database Server
- ✅ MQTT Broker (Mosquitto) 
- ✅ Node.js Dependencies
- ✅ Complete Admin Interface
- ✅ Real-time Socket.IO Communication
- ✅ Security Configuration

### Start the Platform
```bash
npm start
```

### Access the System
- **Web Interface:** http://localhost:3000
- **Admin Panel:** http://localhost:3000/admin

### Default Login
- **Email:** admin@lxcloud.local
- **Password:** admin123

## 📋 System Requirements

- Ubuntu/Debian Linux
- Node.js 18+
- Root/sudo access for initial setup

## 🔧 Features

### 📊 Database Integration
- Full MariaDB relational database
- Automatic schema creation and migrations
- Secure connection with prepared statements
- Data backup and recovery tools

### 📡 MQTT Communication
- Real-time device communication
- Automatic device discovery and registration
- Live data collection and monitoring
- Status tracking and diagnostics

### 🎨 Enhanced Admin Interface
- **User Management:** Create, edit, delete users with role-based access
- **UI Customization:** Live CSS editor with color pickers and themes
- **Device Management:** Controller binding and real-time monitoring
- **System Tools:** Database management and MQTT diagnostics

### 🔒 Security Features
- Local network access restriction
- Session management and rate limiting
- Password hashing with bcrypt
- Input validation and CSRF protection

## 📊 MQTT Topics

The platform uses these MQTT topic patterns:

- **Device Registration:** `lxcloud/controllers/{serial}/register`
- **Live Data Collection:** `lxcloud/controllers/{serial}/data`
- **Status Updates:** `lxcloud/controllers/{serial}/status`

## 🛠️ Maintenance

### Update System
```bash
./update.sh
```

### Manual Database Setup
```bash
node scripts/setup-database.js
```

### Test Components
```bash
npm test                              # Run full test suite
node scripts/test-database.js        # Test database connection
node scripts/test-mqtt-connection.js # Test MQTT broker
```

## 🏗️ Architecture

```
LXCloud Platform
├── server.js                 # Main application server
├── setup.sh                  # Complete installation script
├── update.sh                 # System update script
├── config/                   # Configuration modules
├── routes/                   # API and web routes
├── models/                   # Database models
├── controllers/              # Business logic
├── middleware/               # Express middleware
├── services/                 # External service integrations
├── views/                    # EJS templates
├── public/                   # Static assets
└── scripts/                  # Utility scripts
```

## 🔄 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/status` - Check authentication status

### Admin Panel
- `GET /admin` - Admin dashboard
- `POST /admin/users` - Create user
- `PUT /admin/users/:id` - Update user
- `DELETE /admin/users/:id` - Delete user
- `GET /admin/system` - System status

### Controllers
- `GET /controllers` - List all controllers
- `POST /controllers` - Register new controller
- `GET /controllers/:id` - Get controller details
- `PUT /controllers/:id` - Update controller

### Real-time Communication
- Socket.IO events for live updates
- MQTT message broadcasting
- System status notifications

## 🐛 Troubleshooting

### Service Status Check
```bash
sudo systemctl status mariadb    # Check database
sudo systemctl status mosquitto  # Check MQTT broker
```

### Reset Database
```bash
sudo mysql -e "DROP DATABASE lxcloud;"
node scripts/setup-database.js
```

### View Logs
```bash
tail -f logs/lxcloud.log        # Application logs
sudo tail -f /var/log/mysql/error.log  # Database logs
sudo tail -f /var/log/mosquitto/mosquitto.log  # MQTT logs
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Support

For issues and support:
1. Check the troubleshooting section above
2. Review log files for error details
3. Ensure all system requirements are met
4. Verify service status and connectivity

---

**LXCloud v2.0** - Complete IoT Cloud Management Platform