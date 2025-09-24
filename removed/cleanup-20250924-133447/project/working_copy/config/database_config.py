"""
Database configuration utility for LXCloud
This module provides centralized database configuration that can be used by all scripts
"""
import os
import configparser
from typing import Dict, Optional


class DatabaseConfig:
    """Centralized database configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize database configuration
        
        Args:
            config_file: Path to database.conf file. If None, searches for it automatically.
        """
        self.config_file = config_file or self._find_config_file()
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Find database.conf file in common locations"""
        possible_locations = [
            'database.conf',  # Current directory
            os.path.join(os.path.dirname(__file__), '..', 'database.conf'),  # Parent directory
            os.path.join(os.path.dirname(__file__), '..', '..', 'database.conf'),  # Two levels up
            '/opt/LXCloud/database.conf',  # Common deployment location
            '/etc/lxcloud/database.conf',  # System configuration
            os.path.expanduser('~/.lxcloud/database.conf'),  # User configuration
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Set defaults
        defaults = {
            'host': 'localhost',
            'port': '3306',
            'user': 'lxcloud',
            'password': 'lxcloud123',
            'database': 'lxcloud',
            'charset': 'utf8mb4',
            'connect_timeout': '10',
            'autocommit': 'true',
            'sqlite_fallback': 'sqlite:///lxcloud_fallback.db',
            'pool_size': '5',
            'max_overflow': '10',
            'pool_recycle': '3600'
        }
        
        self.config.add_section('database')
        for key, value in defaults.items():
            self.config.set('database', key, value)
        
        # Load from config file if it exists
        if self.config_file and os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
            except Exception as e:
                print(f"Warning: Could not read config file {self.config_file}: {e}")
        
        # Override with environment variables (for backward compatibility)
        env_mappings = {
            'DB_HOST': 'host',
            'DB_PORT': 'port', 
            'DB_USER': 'user',
            'DB_PASSWORD': 'password',
            'DB_NAME': 'database',
            'SQLITE_FALLBACK_URI': 'sqlite_fallback'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value:
                self.config.set('database', config_key, env_value)
    
    def get(self, key: str, fallback: str = None) -> str:
        """Get a configuration value"""
        try:
            return self.config.get('database', key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, key: str, fallback: int = None) -> int:
        """Get a configuration value as integer"""
        try:
            return self.config.getint('database', key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_bool(self, key: str, fallback: bool = None) -> bool:
        """Get a configuration value as boolean"""
        try:
            return self.config.getboolean('database', key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_connection_params(self) -> Dict[str, any]:
        """Get database connection parameters as a dictionary"""
        return {
            'host': self.get('host'),
            'port': self.get_int('port'),
            'user': self.get('user'),
            'password': self.get('password'),
            'database': self.get('database'),
            'charset': self.get('charset'),
            'connect_timeout': self.get_int('connect_timeout'),
            'autocommit': self.get_bool('autocommit', True)
        }
    
    def get_sqlalchemy_uri(self) -> str:
        """Get SQLAlchemy database URI for MariaDB/MySQL"""
        params = self.get_connection_params()
        return f"mysql+pymysql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}?charset={params['charset']}"
    
    def get_sqlite_fallback_uri(self) -> str:
        """Get SQLite fallback URI"""
        return self.get('sqlite_fallback')
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            import pymysql
            params = self.get_connection_params()
            
            # Remove None values and convert types
            connection_params = {
                'host': params['host'],
                'port': params['port'],
                'user': params['user'],
                'password': params['password'],
                'database': params['database'],
                'charset': params['charset'],
                'connect_timeout': params['connect_timeout'],
                'autocommit': params['autocommit']
            }
            
            conn = pymysql.connect(**connection_params)
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def create_connection(self):
        """Create a PyMySQL database connection"""
        import pymysql
        params = self.get_connection_params()
        
        connection_params = {
            'host': params['host'],
            'port': params['port'],
            'user': params['user'],
            'password': params['password'],
            'database': params['database'],
            'charset': params['charset'],
            'connect_timeout': params['connect_timeout'],
            'autocommit': params['autocommit']
        }
        
        return pymysql.connect(**connection_params)
    
    def print_config(self):
        """Print current configuration (without password)"""
        print("Database Configuration:")
        print(f"  Host: {self.get('host')}")
        print(f"  Port: {self.get('port')}")
        print(f"  Database: {self.get('database')}")
        print(f"  User: {self.get('user')}")
        print(f"  Password: {'*' * len(self.get('password'))}")
        print(f"  Charset: {self.get('charset')}")
        print(f"  Connect Timeout: {self.get('connect_timeout')}")
        print(f"  SQLite Fallback: {self.get('sqlite_fallback')}")
        if self.config_file:
            print(f"  Config File: {self.config_file}")
        else:
            print("  Config File: Using defaults and environment variables")


# Global instance for easy access
db_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance"""
    return db_config


def test_database_connection() -> bool:
    """Test database connection using global config"""
    return db_config.test_connection()


def get_sqlalchemy_uri() -> str:
    """Get SQLAlchemy URI using global config"""
    return db_config.get_sqlalchemy_uri()


def get_sqlite_fallback_uri() -> str:
    """Get SQLite fallback URI using global config"""
    return db_config.get_sqlite_fallback_uri()


if __name__ == "__main__":
    # Command line utility for testing database configuration
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            print("Testing database connection...")
            config = DatabaseConfig()
            config.print_config()
            print()
            
            if config.test_connection():
                print("✅ Database connection successful!")
                sys.exit(0)
            else:
                print("❌ Database connection failed!")
                sys.exit(1)
        elif sys.argv[1] == "show":
            config = DatabaseConfig()
            config.print_config()
        elif sys.argv[1] == "uri":
            config = DatabaseConfig()
            print("SQLAlchemy URI:", config.get_sqlalchemy_uri())
            print("SQLite Fallback URI:", config.get_sqlite_fallback_uri())
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python database_config.py [test|show|uri]")
            sys.exit(1)
    else:
        print("Usage: python database_config.py [test|show|uri]")
        print("  test - Test database connection")
        print("  show - Show current configuration")
        print("  uri  - Show database URIs")