from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from app.models import db, User

def create_app():
    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # Try to detect if MySQL is available and fallback to SQLite if not
    original_config = Config()
    mysql_uri = original_config.SQLALCHEMY_DATABASE_URI
    sqlite_uri = original_config.SQLITE_FALLBACK_URI
    
    # Test database connectivity before initializing
    database_uri = mysql_uri
    try:
        print("Testing database connectivity...")
        import pymysql
        # Parse the MySQL URI to get connection parameters
        import re
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(.+)', mysql_uri)
        if match:
            user, password, host, database = match.groups()
            # Test connection
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            conn.close()
            print("MySQL database connection successful")
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        print("Falling back to SQLite database")
        database_uri = sqlite_uri
    
    # Set the final database URI
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Add context processor for version
    @app.context_processor
    def inject_config():
        return dict(version=Config.get_version())
    
    # Register blueprints
    try:
        from app.routes.auth import auth_bp
        from app.routes.dashboard import dashboard_bp
        from app.routes.controllers import controllers_bp
        from app.routes.users import users_bp
        from app.routes.admin import admin_bp
        from app.routes.api import api_bp
    except ImportError as e:
        print(f"Import error: {e}")
        raise
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(controllers_bp, url_prefix='/controllers')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        try:
            print("Initializing database...")
            db.create_all()
            print("Database initialized successfully")
            
            # Create default admin user if it doesn't exist
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@lxcloud.local',
                    full_name='System Administrator',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("Created default admin user: admin/admin123")
                
        except Exception as e:
            print(f"Database initialization failed: {e}")
            print("Application will continue but database functionality may be limited")
    
    return app