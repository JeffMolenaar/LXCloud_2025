# LXCloud Installation Guide for Ubuntu 22.04 LTS

This guide provides step-by-step instructions for installing LXCloud on Ubuntu Server LTS 22.04.

## Quick Installation

```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025
./scripts/install-ubuntu-22.04.sh
```

## System Requirements

- **Operating System**: Ubuntu Server LTS 22.04 (recommended)
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: Minimum 10GB free disk space
- **Network**: Internet connection for package downloads
- **User**: Regular user account with sudo privileges

## Pre-Installation Checklist

1. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Check Ubuntu Version**:
   ```bash
   lsb_release -a
   ```
   Should show "Ubuntu 22.04.x LTS"

3. **Verify Sudo Access**:
   ```bash
   sudo -v
   ```

4. **Check Available Space**:
   ```bash
   df -h
   ```

## Installation Process

### Step 1: Download LXCloud
```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git
cd LXCloud_2025
```

### Step 2: Run Installation Script
```bash
./scripts/install-ubuntu-22.04.sh
```

The installation script will:

1. **Clean up** any previous installations
2. **Install** system dependencies:
   - Node.js 18.x
   - MariaDB server
   - Mosquitto MQTT broker
   - Nginx web server
   - UFW firewall
3. **Configure** all services optimally for Ubuntu 22.04
4. **Create** database schema and default admin user
5. **Set up** systemd service for automatic startup
6. **Configure** nginx reverse proxy (HTTP only, no HTTPS redirect)
7. **Configure** firewall rules for local network access
8. **Test** all services and connectivity

### Step 3: Verify Installation
```bash
# Run comprehensive test suite
sudo /opt/lxcloud/../scripts/test-installation.sh

# Check system status
sudo /opt/lxcloud/status.sh

# View logs
sudo journalctl -u lxcloud -f
```

## Post-Installation Setup

### Access Your Installation

1. **Find your server IP**:
   ```bash
   hostname -I
   ```

2. **Access via web browser**:
   - Local: `http://localhost`
   - Network: `http://YOUR_SERVER_IP`

3. **Login with default credentials**:
   - Email: `admin@lxcloud.local`
   - Password: `admin123`

### Important Security Steps

1. **Change Default Password**:
   - Login to the web interface
   - Go to Profile Settings
   - Change the admin password immediately

2. **Enable HTTPS (Optional)**:
   ```bash
   sudo certbot --nginx
   ```

3. **Review Firewall Settings**:
   ```bash
   sudo ufw status
   ```

4. **Monitor System Logs**:
   ```bash
   sudo journalctl -u lxcloud -f
   ```

## Management Commands

### Service Management
```bash
# Check status of all services
sudo /opt/lxcloud/status.sh

# Restart LXCloud
sudo systemctl restart lxcloud

# Restart all services
sudo systemctl restart lxcloud nginx mariadb mosquitto

# View service logs
sudo journalctl -u lxcloud -f
sudo journalctl -u nginx -f
sudo journalctl -u mariadb -f
```

### Maintenance
```bash
# Create backup
sudo /opt/lxcloud/backup.sh

# Update LXCloud
sudo /opt/lxcloud/update.sh

# Run diagnostics
sudo /opt/lxcloud/diagnose.sh
```

## Troubleshooting

### Common Issues

#### "Unable to connect to server"

**Quick Fix**:
```bash
# Run diagnostics first
sudo /opt/lxcloud/diagnose.sh

# Restart all services
sudo systemctl restart lxcloud nginx mariadb mosquitto

# Check status
sudo /opt/lxcloud/status.sh
```

**Detailed Troubleshooting**:

1. **Check Services**:
   ```bash
   sudo systemctl status lxcloud nginx mariadb mosquitto
   ```

2. **Check Ports**:
   ```bash
   sudo ss -tlnp | grep -E ':(80|3000|1883|3306)'
   ```

3. **Test Connectivity**:
   ```bash
   curl http://localhost:3000/api/health
   curl http://localhost
   ```

4. **Check Logs**:
   ```bash
   sudo journalctl -u lxcloud -n 50
   ```

#### Database Connection Issues

```bash
# Test database connection
mysql -u lxcloud -plxcloud lxcloud -e "SELECT 1"

# Check MariaDB status
sudo systemctl status mariadb

# Restart MariaDB
sudo systemctl restart mariadb
```

#### MQTT Connection Issues

```bash
# Test MQTT
mosquitto_pub -h localhost -u lxcloud_mqtt -P [password] -t test -m hello

# Check Mosquitto status
sudo systemctl status mosquitto

# Check MQTT logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

#### Firewall Issues

```bash
# Check firewall status
sudo ufw status

# Allow HTTP traffic
sudo ufw allow 'Nginx Full'

# Allow application port for local networks
sudo ufw allow from 192.168.0.0/16 to any port 3000
```

### Getting Help

1. **Run Full Diagnostics**:
   ```bash
   sudo /opt/lxcloud/diagnose.sh
   ```

2. **Check System Resources**:
   ```bash
   htop
   df -h
   free -h
   ```

3. **View All Logs**:
   ```bash
   sudo journalctl -u lxcloud --since "1 hour ago"
   sudo journalctl -u nginx --since "1 hour ago"
   sudo journalctl -u mariadb --since "1 hour ago"
   ```

## Advanced Configuration

### SSL/TLS Setup

```bash
# Install Certbot (if not already installed)
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx

# Test SSL renewal
sudo certbot renew --dry-run
```

### Custom Configuration

- **Application config**: `/opt/lxcloud/.env`
- **Nginx config**: `/etc/nginx/sites-available/lxcloud`
- **Systemd service**: `/etc/systemd/system/lxcloud.service`
- **MQTT config**: `/etc/mosquitto/conf.d/lxcloud.conf`

### Performance Tuning

1. **Increase Connection Limits**:
   ```bash
   sudo nano /etc/nginx/sites-available/lxcloud
   # Adjust worker_connections and other parameters
   ```

2. **Database Optimization**:
   ```bash
   sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
   # Adjust buffer sizes and cache settings
   ```

3. **Monitor Resources**:
   ```bash
   htop
   iotop
   nethogs
   ```

## Backup and Recovery

### Creating Backups

```bash
# Create full backup
sudo /opt/lxcloud/backup.sh

# Manual database backup
mysqldump -u lxcloud -plxcloud lxcloud > backup.sql
```

### Restoring from Backup

```bash
# Restore database
mysql -u lxcloud -plxcloud lxcloud < backup.sql

# Restore application files
tar -xzf application_backup.tar.gz -C /opt/
```

## Updates

### Updating LXCloud

```bash
# Automatic update
sudo /opt/lxcloud/update.sh

# Manual update
cd /opt/lxcloud
sudo -u lxcloud git pull origin main
sudo -u lxcloud npm install --omit=dev
sudo systemctl restart lxcloud
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Reboot if kernel was updated
sudo reboot
```

## Support

For additional support:

1. Check the main README.md file
2. Review troubleshooting documentation
3. Run diagnostics: `sudo /opt/lxcloud/diagnose.sh`
4. Check GitHub issues: https://github.com/JeffMolenaar/LXCloud_2025/issues

## Version Information

- **LXCloud Version**: 1.0.0
- **Supported OS**: Ubuntu Server LTS 22.04
- **Node.js Version**: 18.x
- **Database**: MariaDB
- **Web Server**: Nginx
- **MQTT Broker**: Mosquitto