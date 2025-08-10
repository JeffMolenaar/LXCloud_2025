# LXCloud Integrated v2.0

> **Complete LXCloud Solution with MariaDB + MQTT + Enhanced Admin Interface**

LXCloud Integrated v2.0 combines the reliability of the simplified version with full database functionality, MQTT integration, and a comprehensive super admin interface for complete system control.

## 🎯 Key Features

### ✨ **Complete Integration**
- **📊 MariaDB Database** - Full relational database with comprehensive schema
- **📡 MQTT Support** - Real-time device communication and data collection  
- **🎨 Enhanced Admin UI** - Complete system management and customization
- **🔒 Secure Local Network** - HTTP-only access restricted to local IPs
- **⚡ Real-time Updates** - Socket.IO for live data and status updates

### 🛠️ **Super Admin Features**
- **👥 User Management** - Create, edit, delete users with role-based access
- **🎨 UI Customization** - Live CSS editor with theme templates and color pickers
- **🖥️ Controller Management** - Device registration, binding, and monitoring
- **⚙️ System Settings** - Configuration management and environment variables
- **📊 Real-time Monitoring** - Live system activity and MQTT message tracking
- **🔧 Database Tools** - Connection testing, migrations, and diagnostics

### 🔐 **Security Features**
- **Local Network Only** - Automatic external IP blocking (production mode)
- **Role-based Access** - Admin and user roles with proper middleware
- **Session Management** - Secure HTTP-only sessions with MariaDB storage
- **Password Security** - bcrypt hashing with configurable rounds
- **Rate Limiting** - Protection against brute force attacks

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm 8+
- Ubuntu/Debian Linux (for automatic setup)

### 1. **Automatic Setup** (Recommended)
```bash
# Clone repository
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025

# Run integrated setup (installs MariaDB + MQTT)
./scripts/setup-integrated.sh
```

### 2. **Start the Server**
```bash
npm start
```

### 3. **Access the System**
- **URL:** http://localhost:3000
- **Login:** admin@lxcloud.local / admin123

## 📋 Manual Setup

If automatic setup fails or you prefer manual configuration:

### Install MariaDB
```bash
sudo apt update
sudo apt install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Create database
sudo mysql -e "CREATE DATABASE lxcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud';"
sudo mysql -e "GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### Install MQTT Broker
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Configure Environment
```bash
cp .env.example .env
# Edit .env with your database and MQTT settings
```

### Install Dependencies & Start
```bash
npm install
npm start
```

## 🎨 Super Admin Interface

### User Management
- **Create Users:** Add new users with admin/user roles
- **Edit Users:** Modify user details, roles, and active status
- **Delete Users:** Remove users (with protection for current admin)
- **Real-time Updates:** Live user status and login tracking

### UI Customization
- **Page Selection:** Customize login, dashboard, admin, or global styles
- **Live CSS Editor:** Full-featured editor with syntax highlighting
- **Color Picker:** Visual tools for brand colors and themes
- **Theme Templates:** One-click dark, light, and modern themes
- **Font Controls:** Typography settings and Google Fonts integration
- **Live Preview:** See changes in real-time (coming soon)

### Controller Management
- **Device Registration:** Automatic MQTT device discovery
- **User Binding:** Assign controllers to specific users
- **Status Monitoring:** Real-time online/offline tracking
- **Data Visualization:** Live sensor data and historical charts

### System Tools
- **Database Management:** Connection testing, backup, migrations
- **MQTT Tools:** Message publishing, subscription monitoring
- **System Logs:** Real-time log viewing and filtering
- **Performance Monitoring:** Server metrics and resource usage

## 📡 MQTT Integration

### Automatic Device Discovery
```javascript
// Controllers automatically register via MQTT
Topic: lxcloud/controllers/{serial}/register
Payload: {
  "type": "speedradar|beaufortmeter|weatherstation|aicamera",
  "name": "Device Name",
  "latitude": 52.1234,
  "longitude": 4.5678
}
```

### Real-time Data Collection
```javascript
// Send sensor data
Topic: lxcloud/controllers/{serial}/data
Payload: {
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "temperature": 23.5,
    "humidity": 65,
    "speed": 45
  }
}
```

### Status Updates
```javascript
// Device status updates
Topic: lxcloud/controllers/{serial}/status
Payload: {
  "status": "online|offline",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=lxcloud
DB_USER=lxcloud
DB_PASSWORD=lxcloud

# MQTT Configuration
MQTT_BROKER_URL=mqtt://localhost:1883
MQTT_USERNAME=lxcloud_mqtt
MQTT_PASSWORD=mqtt_password
MQTT_TOPIC_PREFIX=lxcloud

# Security
SESSION_SECRET=your_secure_session_secret
JWT_SECRET=your_jwt_secret
BCRYPT_ROUNDS=12

# Application
NODE_ENV=production
PORT=3000
```

### Database Schema
The system automatically creates comprehensive tables:
- **users** - User accounts and authentication
- **controllers** - Device registration and management
- **controller_data** - Sensor data storage
- **ui_customizations** - Admin UI customizations
- **system_settings** - Application configuration
- **sessions** - User session management
- **audit_log** - Security and activity tracking

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Start server in another terminal
npm start

# Run integrated tests
node test-integrated.js
```

### Test Coverage
- ✅ HTTP server response and routing
- ✅ Local network access control
- ✅ External IP blocking (production)
- ✅ Authentication system
- ✅ Admin panel security
- ✅ Database integration
- ✅ MQTT connectivity
- ✅ Socket.IO real-time updates
- ✅ Static file serving
- ✅ API endpoint functionality

## 📊 System Requirements

### Minimum Requirements
- **CPU:** 1 core, 1 GHz
- **RAM:** 512 MB
- **Storage:** 1 GB free space
- **Network:** Local network access

### Recommended Requirements
- **CPU:** 2+ cores, 2+ GHz
- **RAM:** 2+ GB
- **Storage:** 10+ GB free space
- **Network:** Gigabit ethernet

### Supported Systems
- Ubuntu 20.04+ (Primary)
- Debian 10+ 
- CentOS 8+ (with manual setup)
- Other Linux distributions (manual setup required)

## 🔒 Security Considerations

### Network Security
- **Local Network Only:** External access blocked in production
- **HTTP-only:** Optimized for secure local network environments
- **Rate Limiting:** Protection against abuse and attacks

### Data Security
- **Password Hashing:** bcrypt with configurable rounds
- **Session Security:** Secure HTTP-only cookies
- **Database Security:** Prepared statements prevent SQL injection
- **Input Validation:** Comprehensive server-side validation

### Access Control
- **Role-based Security:** Admin and user roles with middleware
- **Route Protection:** Authentication required for sensitive areas
- **API Security:** Token-based authentication for API endpoints

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Check MariaDB status
sudo systemctl status mariadb

# Test connection manually
mysql -u lxcloud -plxcloud -e "USE lxcloud; SELECT 1;"

# Reset database (if needed)
sudo mysql -e "DROP DATABASE lxcloud;"
./scripts/setup-integrated.sh
```

### MQTT Connection Issues
```bash
# Check MQTT broker status
sudo systemctl status mosquitto

# Test MQTT manually
mosquitto_pub -h localhost -t test/topic -m "test"
mosquitto_sub -h localhost -t test/topic

# Check MQTT logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

### Permission Issues
```bash
# Fix file permissions
chmod 755 uploads data
chmod +x scripts/*.sh

# Check Node.js version
node --version  # Should be 18+
npm --version   # Should be 8+
```

## 📝 API Documentation

### Admin API Endpoints
```bash
# Test database connection
POST /admin/api/test-database

# Test MQTT connection  
POST /admin/api/test-mqtt

# Get system statistics
GET /admin/api/stats

# User management
POST /admin/api/users           # Create user
PUT /admin/api/users/:id        # Update user
DELETE /admin/api/users/:id     # Delete user

# UI customization
POST /admin/api/ui-customization

# System settings
POST /admin/api/system-settings
```

### Controller API
```bash
# Controller management
POST /admin/api/controllers/:id/bind     # Bind to user
DELETE /admin/api/controllers/:id        # Delete controller
```

## 🎯 Migration from Simple Version

### Automatic Migration
The integrated version automatically detects and migrates data from the simple version:

1. **User Data:** JSON users converted to MariaDB
2. **Settings:** Environment variables transferred
3. **File Structure:** Maintains compatibility

### Manual Migration (if needed)
```bash
# Backup simple version data
cp -r data data_backup

# Start integrated version
npm start

# Import users manually via admin panel if needed
```

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025
npm install
cp .env.example .env
npm run dev  # Development mode with nodemon
```

### Code Structure
```
├── server-integrated.js      # Main integrated server
├── config/
│   ├── database.js          # MariaDB configuration
│   └── logger.js            # Winston logging
├── controllers/
│   └── mqttController.js    # MQTT integration
├── routes/
│   └── admin-integrated.js  # Enhanced admin routes
├── views/admin/
│   ├── index-integrated.ejs # Super admin dashboard
│   ├── users-integrated.ejs # User management
│   └── ui-customization-integrated.ejs
└── scripts/
    └── setup-integrated.sh  # Automated setup
```

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation:** This README and inline comments
- **Issues:** GitHub Issues for bug reports
- **Discussions:** GitHub Discussions for questions

---

**LXCloud Integrated v2.0** - The complete IoT cloud management solution with full database integration, real-time MQTT communication, and comprehensive admin control.