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
    # Get the project root directory with robust path resolution
    # Try multiple approaches to find the correct project root
    
    # Method 1: Standard approach - parent of app directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    # Method 2: Fallback - check current working directory
    if not os.path.exists(template_folder):
        cwd_project_root = os.getcwd()
        cwd_template_folder = os.path.join(cwd_project_root, 'templates')
        cwd_static_folder = os.path.join(cwd_project_root, 'static')
        
        if os.path.exists(cwd_template_folder):
            print(f"Template folder not found at {template_folder}, using fallback: {cwd_template_folder}")
            project_root = cwd_project_root
            template_folder = cwd_template_folder
            static_folder = cwd_static_folder
    
    # Method 3: Last resort - check common deployment paths
    if not os.path.exists(template_folder):
        deployment_paths = ['/opt/LXCloud', '/app', os.path.expanduser('~/LXCloud')]
        for deployment_root in deployment_paths:
            deployment_template_folder = os.path.join(deployment_root, 'templates')
            deployment_static_folder = os.path.join(deployment_root, 'static')
            
            if os.path.exists(deployment_template_folder):
                print(f"Template folder not found at {template_folder}, using deployment path: {deployment_template_folder}")
                project_root = deployment_root
                template_folder = deployment_template_folder
                static_folder = deployment_static_folder
                break
    
    # Final validation and debugging info
    print(f"Project root: {project_root}")
    print(f"Template folder: {template_folder}")
    print(f"Template folder exists: {os.path.exists(template_folder)}")
    if os.path.exists(template_folder):
        auth_template = os.path.join(template_folder, 'auth', 'login.html')
        print(f"Auth login template exists: {os.path.exists(auth_template)}")
        # Additional check: verify the template is readable
        try:
            with open(auth_template, 'r') as f:
                f.read(1)  # Read first character to test readability
            print(f"Auth login template is readable")
        except Exception as e:
            print(f"Auth login template exists but is not readable: {e}")
    
    if not os.path.exists(template_folder):
        print(f"ERROR: Template folder not found. Debugging info:")
        print(f"  - Current working directory: {os.getcwd()}")
        print(f"  - __file__: {__file__}")
        print(f"  - Absolute __file__: {os.path.abspath(__file__)}")
        print(f"  - Directory contents at project_root:")
        try:
            project_contents = os.listdir(project_root)
            print(f"    {project_contents}")
        except Exception as e:
            print(f"    Could not list directory: {e}")
        raise RuntimeError(f"Template folder not found. Tried: {template_folder}")
    
    # Validate critical templates exist
    critical_templates = [
        'auth/login.html',
        'auth/register.html',
        'base.html'
    ]
    
    missing_templates = []
    for template in critical_templates:
        template_path = os.path.join(template_folder, template)
        if not os.path.exists(template_path):
            missing_templates.append(template)
    
    if missing_templates:
        print(f"WARNING: Critical templates are missing:")
        for template in missing_templates:
            print(f"  - {template}")
        print(f"This may cause template loading errors. Please check installation.")
    
    # Ensure template_folder is absolute path for Flask
    template_folder = os.path.abspath(template_folder)
    static_folder = os.path.abspath(static_folder)
    
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
    
    # Add custom error handler for template not found
    @app.errorhandler(500)
    def internal_error(error):
        # Check if this is a TemplateNotFound error
        if hasattr(error, 'original_exception'):
            from jinja2.exceptions import TemplateNotFound
            if isinstance(error.original_exception, TemplateNotFound):
                template_name = error.original_exception.name
                print(f"Template not found: {template_name}")
                print(f"Template loader search paths:")
                for loader in app.jinja_env.list_templates():
                    print(f"  Available template: {loader}")
                print(f"Template folder configured as: {app.template_folder}")
                print(f"Template folder exists: {os.path.exists(app.template_folder)}")
                # Check specific template
                template_path = os.path.join(app.template_folder, template_name)
                print(f"Looking for template at: {template_path}")
                print(f"Template file exists: {os.path.exists(template_path)}")
        return str(error), 500
    
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