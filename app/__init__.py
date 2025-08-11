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
    # Make this more robust for different deployment scenarios
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Ensure we're in the correct directory structure
    # Check for common deployment paths and fallback accordingly
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    # Verify template folder exists, if not try alternative paths
    if not os.path.exists(template_folder):
        print(f"Warning: Template folder not found at {template_folder}")
        # Try relative to current working directory
        alt_template_folder = os.path.join(os.getcwd(), 'templates')
        if os.path.exists(alt_template_folder):
            print(f"Found templates at current working directory: {alt_template_folder}")
            template_folder = alt_template_folder
            static_folder = os.path.join(os.getcwd(), 'static')
        else:
            # Try relative to the directory where run.py is located
            run_py_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if len(sys.argv) > 0 else os.getcwd()
            alt2_template_folder = os.path.join(run_py_dir, 'templates')
            if os.path.exists(alt2_template_folder):
                print(f"Found templates at run.py directory: {alt2_template_folder}")
                template_folder = alt2_template_folder
                static_folder = os.path.join(run_py_dir, 'static')
            else:
                print(f"Warning: Could not find templates folder. Tried:")
                print(f"  1. {os.path.join(project_root, 'templates')}")
                print(f"  2. {alt_template_folder}")
                print(f"  3. {alt2_template_folder}")
    
    print(f"Using template folder: {template_folder}")
    print(f"Template folder exists: {os.path.exists(template_folder)}")
    if os.path.exists(template_folder):
        auth_login_path = os.path.join(template_folder, 'auth', 'login.html')
        print(f"Auth login template exists: {os.path.exists(auth_login_path)}")
        if not os.path.exists(auth_login_path):
            print(f"Warning: auth/login.html not found at {auth_login_path}")
            # List available templates for debugging
            print("Available templates:")
            try:
                for root, dirs, files in os.walk(template_folder):
                    level = root.replace(template_folder, '').count(os.sep)
                    indent = ' ' * 2 * level
                    rel_path = os.path.relpath(root, template_folder)
                    print(f"{indent}{rel_path if rel_path != '.' else 'templates'}/ ")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
            except Exception as e:
                print(f"Error listing templates: {e}")
    
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