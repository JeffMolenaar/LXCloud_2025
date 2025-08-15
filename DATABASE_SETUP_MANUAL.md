# LXCloud Database Setup Guide

This guide explains how to manually set up the MariaDB database for LXCloud.

## Prerequisites

- Ubuntu 22.04 LTS or similar Linux distribution
- Root or sudo access

## Step 1: Install MariaDB

```bash
sudo apt update
sudo apt install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

## Step 2: Secure MariaDB Installation

```bash
sudo mysql_secure_installation
```

Follow the prompts to:
- Set a root password
- Remove anonymous users
- Disallow root login remotely
- Remove test database
- Reload privilege tables

## Step 3: Create LXCloud Database and User

Connect to MariaDB as root:

```bash
sudo mysql -u root -p
```

Run these SQL commands:

```sql
CREATE DATABASE IF NOT EXISTS lxcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud';
GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Step 4: Test the Connection

Test that you can connect with the LXCloud user:

```bash
mysql -u lxcloud -plxcloud -h localhost -P 3306 -D lxcloud -e 'SELECT 1;'
```

If this command runs without errors, your database is ready.

## Step 5: Run LXCloud Installation

Now you can run the LXCloud installation script:

```bash
sudo ./scripts/install.sh
```

The installation script will test the database connection and create the necessary configuration files.

## Troubleshooting

### Connection Refused
- Check if MariaDB is running: `sudo systemctl status mariadb`
- Check if MariaDB is listening: `sudo netstat -tlnp | grep 3306`

### Access Denied
- Verify the username and password are correct
- Check user exists: `sudo mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='lxcloud';"`
- Check user permissions: `sudo mysql -u root -p -e "SHOW GRANTS FOR 'lxcloud'@'localhost';"`

### Database Does Not Exist
- Check database exists: `sudo mysql -u root -p -e "SHOW DATABASES;"`
- Recreate the database if needed using the SQL commands above

## Alternative Database Configuration

If you want to use different database credentials, you can specify them when running the database setup:

```bash
./database_setup_manual.sh --db-name mydb --db-user myuser --db-password mypass
```

## Remote Database

To use a remote MariaDB server:

```bash
./database_setup_manual.sh --db-host 192.168.1.100 --db-user lxcloud --db-password lxcloud
```

Make sure the remote server allows connections from your LXCloud server and the user has appropriate permissions.