#!/usr/bin/env python3
"""
Database utility script for LXCloud
Provides database management and testing utilities
"""
import sys
import os
from datetime import datetime
import secrets
import stat

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database_config import DatabaseConfig


def test_database():
    """Test database connection"""
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    config = DatabaseConfig()
    config.print_config()
    print()
    
    print("Testing connection...")
    if config.test_connection():
        print("✅ Database connection successful!")
        return True
    else:
        print("❌ Database connection failed!")
        print()
        print("Troubleshooting steps:")
        print("1. Check if MariaDB/MySQL is running:")
        print("   sudo systemctl status mariadb")
        print("2. Verify database credentials in database.conf or environment variables")
        print("3. Ensure the database and user exist")
        print("4. Check firewall settings if using remote database")
        return False


def show_config():
    """Show current database configuration"""
    print("📋 Database Configuration")
    print("=" * 40)
    
    config = DatabaseConfig()
    config.print_config()
    
    print()
    print("SQLAlchemy URIs:")
    print(f"  Primary: {config.get_sqlalchemy_uri()}")
    print(f"  Fallback: {config.get_sqlite_fallback_uri()}")


def create_database():
    """Create database and user (requires admin privileges)"""
    print("🔧 Creating Database and User")
    print("=" * 40)
    
    config = DatabaseConfig()
    
    # Get admin credentials
    import getpass
    admin_user = input("Enter MySQL/MariaDB admin username (default: root): ").strip() or "root"
    admin_password = getpass.getpass("Enter MySQL/MariaDB admin password: ")
    
    try:
        import pymysql
        
        # Connect as admin
        admin_conn = pymysql.connect(
            host=config.get('host'),
            port=config.get_int('port'),
            user=admin_user,
            password=admin_password,
            connect_timeout=10
        )
        
        cursor = admin_conn.cursor()
        
        # Create database
        db_name = config.get('database')
        print(f"Creating database: {db_name}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # Create user
        db_user = config.get('user')
        db_password = config.get('password')
        db_host = config.get('host')
        
        print(f"Creating user: {db_user}@{db_host}")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'{db_host}' IDENTIFIED BY '{db_password}'")
        
        # Grant privileges
        print(f"Granting privileges on {db_name} to {db_user}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'{db_host}'")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES")
        
        cursor.close()
        admin_conn.close()
        
        print("✅ Database and user created successfully!")
        
        # Test the new connection
        print("\nTesting new database connection...")
        if config.test_connection():
            print("✅ New database connection successful!")
        else:
            print("❌ Could not connect with new database credentials")
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False
    
    return True


def initialize_schema():
    """Initialize database schema using Flask application"""
    print("🏗️  Initializing Database Schema")
    print("=" * 40)
    
    try:
        from app import create_app
        from app.models import db
        import secrets
        
        app = create_app()
        with app.app_context():
            print("Creating all database tables...")
            db.create_all()
            print("✅ Database schema initialized successfully!")
            
            # Create default admin user
            from app.models import User
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@lxcloud.local',
                    full_name='System Administrator',
                    is_admin=True
                )
                # Generate a secure random password and save it to a file with strict permissions
                generated_password = secrets.token_urlsafe(12)
                admin_user.set_password(generated_password)
                db.session.add(admin_user)
                db.session.commit()

                cred_dir = '/etc/lxcloud'
                cred_path = os.path.join(cred_dir, 'admin_credentials')
                try:
                    os.makedirs(cred_dir, exist_ok=True)
                    with open(cred_path, 'w') as cf:
                        cf.write(f"username: admin\npassword: {generated_password}\n")
                    # Restrict permissions to owner only (root)
                    os.chmod(cred_path, 0o600)
                    # Ensure directory is root-owned and secure
                    os.chown(cred_dir, 0, 0)
                    os.chown(cred_path, 0, 0)
                    print(f"✅ Created default admin user 'admin'. Credentials saved to: {cred_path} (permissions 600)")
                except Exception as wf:
                    print(f"✅ Created default admin user 'admin'. Failed to write credentials file: {wf}")
            else:
                print("ℹ️  Admin user already exists")
                
    except Exception as e:
        print(f"❌ Failed to initialize schema: {e}")
        return False
    
    return True


def backup_database():
    """Create a backup of the database"""
    print("💾 Creating Database Backup")
    print("=" * 40)
    
    config = DatabaseConfig()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"lxcloud_backup_{timestamp}.sql"
    
    # Use mysqldump for backup
    import subprocess
    
    try:
        cmd = [
            'mysqldump',
            '-h', config.get('host'),
            '-P', str(config.get_int('port')),
            '-u', config.get('user'),
            f'-p{config.get("password")}',
            '--single-transaction',
            '--routines',
            '--triggers',
            config.get('database')
        ]
        
        print(f"Creating backup: {backup_file}")
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup created successfully: {backup_file}")
            
            # Show backup size
            size = os.path.getsize(backup_file)
            print(f"   Backup size: {size:,} bytes ({size/1024:.1f} KB)")
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ mysqldump command not found. Please install MySQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def restore_database(backup_file):
    """Restore database from backup"""
    print(f"📥 Restoring Database from {backup_file}")
    print("=" * 40)
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    config = DatabaseConfig()
    
    # Confirm restoration
    response = input(f"This will overwrite the current database '{config.get('database')}'. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Restoration cancelled")
        return False
    
    import subprocess
    
    try:
        cmd = [
            'mysql',
            '-h', config.get('host'),
            '-P', str(config.get_int('port')),
            '-u', config.get('user'),
            f'-p{config.get("password")}',
            config.get('database')
        ]
        
        print(f"Restoring from: {backup_file}")
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print("✅ Database restored successfully!")
            return True
        else:
            print(f"❌ Restoration failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ mysql command not found. Please install MySQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Restoration failed: {e}")
        return False


def migrate_database():
    """Apply database migrations to existing database"""
    print("🔄 Applying Database Migrations")
    print("=" * 40)
    
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        with app.app_context():
            print("Checking for required database migrations...")
            
            # Check if marker_config column exists in ui_customization table
            migration_needed = False
            
            try:
                # Try to describe the ui_customization table
                from sqlalchemy import text
                
                # Check if table exists first
                table_check = db.session.execute(text("SHOW TABLES LIKE 'ui_customization'"))
                if not table_check.fetchone():
                    print("ℹ️  ui_customization table does not exist, creating full schema...")
                    db.create_all()
                    print("✅ Database schema created successfully!")
                    return True
                
                # Check if marker_config column exists
                column_check = db.session.execute(text("DESCRIBE ui_customization"))
                columns = [row[0] for row in column_check.fetchall()]
                
                if 'marker_config' not in columns:
                    print("🔍 Found missing column: marker_config in ui_customization table")
                    migration_needed = True
                else:
                    print("✅ marker_config column already exists")
                
                if migration_needed:
                    print("📝 Adding marker_config column to ui_customization table...")
                    db.session.execute(text("ALTER TABLE ui_customization ADD COLUMN marker_config TEXT"))
                    db.session.commit()
                    print("✅ Successfully added marker_config column!")
                else:
                    print("ℹ️  No migrations needed - database is up to date")
                
                return True
                
            except Exception as e:
                # Handle SQLite or other database types
                if "no such table" in str(e).lower() or "doesn't exist" in str(e).lower():
                    print("ℹ️  Database tables don't exist, creating full schema...")
                    db.create_all()
                    print("✅ Database schema created successfully!")
                    return True
                else:
                    # For SQLite, check using different method
                    try:
                        from sqlalchemy import inspect
                        inspector = inspect(db.engine)
                        
                        if 'ui_customization' not in inspector.get_table_names():
                            print("ℹ️  ui_customization table does not exist, creating full schema...")
                            db.create_all()
                            print("✅ Database schema created successfully!")
                            return True
                        
                        columns = [col['name'] for col in inspector.get_columns('ui_customization')]
                        if 'marker_config' not in columns:
                            print("🔍 Found missing column: marker_config in ui_customization table")
                            db.session.execute(text("ALTER TABLE ui_customization ADD COLUMN marker_config TEXT"))
                            db.session.commit()
                            print("✅ Successfully added marker_config column!")
                        else:
                            print("✅ marker_config column already exists")
                        
                        return True
                        
                    except Exception as inner_e:
                        print(f"❌ Migration failed: {inner_e}")
                        return False
                        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def show_help():
    """Show help information"""
    print("LXCloud Database Utility")
    print("=" * 40)
    print()
    print("Usage: python database_utils.py [command]")
    print()
    print("Commands:")
    print("  test              Test database connection")
    print("  config            Show database configuration")
    print("  create            Create database and user (requires admin access)")
    print("  init              Initialize database schema")
    print("  migrate           Apply database migrations to existing database")
    print("  backup            Create database backup")
    print("  restore <file>    Restore database from backup file")
    print("  help              Show this help message")
    print()
    print("Examples:")
    print("  python database_utils.py test")
    print("  python database_utils.py create")
    print("  python database_utils.py migrate")
    print("  python database_utils.py backup")
    print("  python database_utils.py restore lxcloud_backup_20250101_120000.sql")
    print()


def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'test':
        success = test_database()
        sys.exit(0 if success else 1)
    elif command == 'config':
        show_config()
    elif command == 'create':
        success = create_database()
        sys.exit(0 if success else 1)
    elif command == 'init':
        success = initialize_schema()
        sys.exit(0 if success else 1)
    elif command == 'migrate':
        success = migrate_database()
        sys.exit(0 if success else 1)
    elif command == 'backup':
        success = backup_database()
        sys.exit(0 if success else 1)
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Please specify backup file to restore from")
            print("Usage: python database_utils.py restore <backup_file>")
            sys.exit(1)
        backup_file = sys.argv[2]
        success = restore_database(backup_file)
        sys.exit(0 if success else 1)
    elif command == 'help':
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()