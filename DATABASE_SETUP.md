# LXCloud Database Setup Guide

This guide covers setting up MariaDB/MySQL database for LXCloud with centralized configuration management.

## Quick Setup

The easiest way to set up the database is using the automated installation script:

```bash
# Make the script executable
chmod +x database_install.sh

# Run with default settings
./database_install.sh

# Run with custom settings
./database_install.sh --db-name mydb --db-user myuser --db-password mypass
```

## Manual Setup

### 1. Install MariaDB

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

#### CentOS/RHEL/Rocky:
```bash
sudo dnf install mariadb-server mariadb  # or yum on older systems
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

#### Arch Linux:
```bash
sudo pacman -S mariadb
sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

### 2. Secure MariaDB Installation

```bash
sudo mysql_secure_installation
```

Follow the prompts to:
- Set root password
- Remove anonymous users
- Disallow root login remotely
- Remove test database
- Reload privilege tables

### 3. Create Database and User

```bash
# Login to MariaDB as root
mysql -u root -p

# Create database and user
CREATE DATABASE lxcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud123';
GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Configuration

LXCloud uses a centralized database configuration system that supports multiple configuration sources:

### 1. Database Configuration File (Recommended)

Create a `database.conf` file in the project root:

```ini
# LXCloud Database Configuration
[database]
# Database connection settings
host = localhost
port = 3306
user = lxcloud
password = lxcloud123
database = lxcloud

# Connection settings
charset = utf8mb4
connect_timeout = 10
autocommit = true

# SQLite fallback (used when MariaDB is unavailable)
sqlite_fallback = sqlite:///lxcloud_fallback.db

# Connection pool settings (for production)
pool_size = 5
max_overflow = 10
pool_recycle = 3600
```

### 2. Environment Variables (Backward Compatible)

You can also use environment variables (useful for Docker deployments):

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=lxcloud
export DB_PASSWORD=lxcloud123
export DB_NAME=lxcloud
export SQLITE_FALLBACK_URI=sqlite:///lxcloud_fallback.db
```

### 3. .env File

Create a `.env` file (useful for development):

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=lxcloud
DB_PASSWORD=lxcloud123
DB_NAME=lxcloud
SQLITE_FALLBACK_URI=sqlite:///lxcloud_fallback.db
```

## Configuration Priority

The system loads configuration in this order (later sources override earlier ones):

1. Default values (built into the system)
2. `database.conf` file
3. Environment variables
4. Direct `SQLALCHEMY_DATABASE_URI` (highest priority)

## Database Utilities

LXCloud includes several database management utilities:

### Test Database Connection

```bash
# Test using the database configuration utility
python config/database_config.py test

# Or using the full database utilities
python database_utils.py test
```

### Show Current Configuration

```bash
# Show configuration without connecting
python config/database_config.py show

# Show configuration with connection test
python database_utils.py config
```

### Initialize Database Schema

```bash
# Initialize all tables and create default admin user
python database_utils.py init
```

### Database Backup and Restore

```bash
# Create backup
python database_utils.py backup

# Restore from backup
python database_utils.py restore lxcloud_backup_20250101_120000.sql
```

### Create Database and User (if you have admin access)

```bash
# Interactive database and user creation
python database_utils.py create
```

## Troubleshooting

### Connection Issues

1. **Check MariaDB Status:**
   ```bash
   sudo systemctl status mariadb
   ```

2. **Test Connection Manually:**
   ```bash
   mysql -u lxcloud -p -D lxcloud
   ```

3. **Check Configuration:**
   ```bash
   python config/database_config.py show
   ```

4. **Test LXCloud Connection:**
   ```bash
   python database_utils.py test
   ```

### Permission Issues

If you get "Access denied" errors:

1. **Verify User Exists:**
   ```sql
   SELECT User, Host FROM mysql.user WHERE User='lxcloud';
   ```

2. **Check Privileges:**
   ```sql
   SHOW GRANTS FOR 'lxcloud'@'localhost';
   ```

3. **Recreate User (as root):**
   ```sql
   DROP USER IF EXISTS 'lxcloud'@'localhost';
   CREATE USER 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud123';
   GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';
   FLUSH PRIVILEGES;
   ```

### SSL/TLS Issues

For production deployments, you may want to enable SSL:

```ini
[database]
# ... other settings ...
ssl = true
ssl_ca = /path/to/ca.pem
ssl_cert = /path/to/client-cert.pem
ssl_key = /path/to/client-key.pem
```

### Remote Database Connections

For remote database servers:

1. **Update Configuration:**
   ```ini
   [database]
   host = 192.168.1.100
   port = 3306
   # ... other settings ...
   ```

2. **Create Remote User:**
   ```sql
   CREATE USER 'lxcloud'@'%' IDENTIFIED BY 'lxcloud123';
   GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'%';
   FLUSH PRIVILEGES;
   ```

3. **Configure MariaDB for Remote Connections:**
   Edit `/etc/mysql/mariadb.conf.d/50-server.cnf`:
   ```
   bind-address = 0.0.0.0
   ```

4. **Restart MariaDB:**
   ```bash
   sudo systemctl restart mariadb
   ```

## Production Considerations

### Security

1. **Use Strong Passwords:**
   - Generate random passwords for database users
   - Store passwords securely (environment variables, vault systems)

2. **Limit User Privileges:**
   - Don't use root user for application connections
   - Grant only necessary privileges

3. **Network Security:**
   - Use SSL/TLS for remote connections
   - Restrict network access with firewalls

### Performance

1. **Connection Pooling:**
   ```ini
   [database]
   pool_size = 20
   max_overflow = 30
   pool_recycle = 3600
   ```

2. **Database Tuning:**
   - Configure MariaDB my.cnf for your workload
   - Monitor slow queries
   - Add indexes as needed

3. **Backup Strategy:**
   ```bash
   # Setup automated backups
   # Add to crontab:
   0 2 * * * cd /opt/LXCloud && python database_utils.py backup
   ```

### Monitoring

1. **Health Checks:**
   ```bash
   # Add to monitoring system
   python database_utils.py test
   ```

2. **Connection Monitoring:**
   - Monitor active connections
   - Set up alerts for connection failures

### High Availability

For production environments, consider:
- MariaDB Galera Cluster
- MySQL Group Replication
- Load balancers for database connections
- Automated failover systems

## Migration from SQLite

If you're migrating from SQLite to MariaDB:

1. **Export SQLite Data:**
   ```bash
   sqlite3 lxcloud.db .dump > sqlite_dump.sql
   ```

2. **Convert to MySQL Format:**
   - Edit the dump file to fix syntax differences
   - Or use migration tools like `sqlite3-to-mysql`

3. **Import to MariaDB:**
   ```bash
   mysql -u lxcloud -p lxcloud < converted_dump.sql
   ```

4. **Update Configuration:**
   - Create `database.conf` with MariaDB settings
   - Test the connection

## Docker Deployment

For Docker deployments, use environment variables:

```yaml
# docker-compose.yml
version: '3.8'
services:
  mariadb:
    image: mariadb:10.6
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: lxcloud
      MYSQL_USER: lxcloud
      MYSQL_PASSWORD: lxcloud123
    volumes:
      - mariadb_data:/var/lib/mysql
    
  lxcloud:
    build: .
    environment:
      DB_HOST: mariadb
      DB_USER: lxcloud
      DB_PASSWORD: lxcloud123
      DB_NAME: lxcloud
    depends_on:
      - mariadb

volumes:
  mariadb_data:
```

## Support

For additional support:
- Check LXCloud documentation
- Review MariaDB documentation
- Test configuration with provided utilities
- Check application logs for detailed error messages