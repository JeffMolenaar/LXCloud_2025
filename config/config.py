import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
                             f'mysql+pymysql://{os.environ.get("DB_USER", "lxcloud")}:{os.environ.get("DB_PASSWORD", "lxcloud123")}@{os.environ.get("DB_HOST", "localhost")}/{os.environ.get("DB_NAME", "lxcloud")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLite fallback database path
    SQLITE_FALLBACK_URI = os.environ.get('SQLITE_FALLBACK_URI') or 'sqlite:///lxcloud_fallback.db'
    
    # MQTT
    MQTT_ENABLED = os.environ.get('MQTT_ENABLED', 'true').lower() == 'true'
    MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST') or 'localhost'
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT') or 1883)
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME') or ''
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD') or ''
    MQTT_TOPIC_PREFIX = os.environ.get('MQTT_TOPIC_PREFIX') or 'lxcloud'
    
    # Controller Status Management
    CONTROLLER_OFFLINE_TIMEOUT = int(os.environ.get('CONTROLLER_OFFLINE_TIMEOUT') or 300)  # 5 minutes in seconds
    CONTROLLER_STATUS_CHECK_INTERVAL = int(os.environ.get('CONTROLLER_STATUS_CHECK_INTERVAL') or 60)  # 1 minute in seconds
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Version
    VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
    
    @staticmethod
    def get_version():
        try:
            with open(Config.VERSION_FILE, 'r') as f:
                return f.read().strip()
        except:
            return 'V1.0.0'