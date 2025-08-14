from flask import Flask, request, jsonify
from flask_login import LoginManager
from flask_cors import CORS
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from app.models import db, User, UICustomization

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
        from config.database_config import get_database_config
        db_config = get_database_config()
        
        if db_config.test_connection():
            print("MariaDB/MySQL database connection successful")
        else:
            raise Exception("Database connection test failed")
    except Exception as e:
        print(f"MariaDB/MySQL connection failed: {e}")
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
    
    # Add template filter for local datetime formatting
    @app.template_filter('format_local_datetime')
    def format_local_datetime(datetime_obj):
        """Format datetime object for local display"""
        if datetime_obj:
            return datetime_obj.strftime('%m/%d %H:%M')
        return 'Never'

    # Add context processor for version and UI customizations
    @app.context_processor
    def inject_config():
        # Get UI customizations for the current page
        ui_customizations = {}
        try:
            customizations = UICustomization.query.all()
            for customization in customizations:
                ui_customizations[customization.page_name] = {
                    'header_config': customization.get_header_config(),
                    'footer_config': customization.get_footer_config(),
                    'logo_filename': getattr(customization, 'logo_filename', None),
                    'custom_css': customization.custom_css
                }
        except Exception as e:
            print(f"Warning: Could not load UI customizations: {e}")
            # Continue without UI customizations
        
        return dict(
            version=Config.get_version(),
            ui_customizations=ui_customizations,
            format_local_datetime=format_local_datetime
        )
    
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
    
    # Add global error handlers for API routes to ensure JSON responses
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors for API routes with JSON response"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Endpoint not found',
                'message': f'The requested endpoint {request.path} was not found.',
                'path': request.path,
                'method': request.method,
                'available_api_endpoints': {
                    'register_controller': 'POST /api/controllers/register',
                    'update_data': 'POST /api/controllers/{serial}/data',
                    'update_status': 'POST /api/controllers/{serial}/status',
                    'modify_controller': 'PUT /api/controllers/{serial}',
                    'get_controller': 'GET /api/controllers/{serial}',
                    'list_controllers': 'GET /api/controllers/list',
                    'debug': 'GET /api/controllers/debug'
                }
            }), 404
        # For non-API routes, use default HTML error page
        return error
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Handle 405 Method Not Allowed errors for API routes with JSON response"""
        if request.path.startswith('/api/'):
            # Clean the path by removing trailing whitespace, newlines, etc.
            clean_path = request.path.strip().rstrip('\n\r\t ')
            
            # Special handling for register endpoint with malformed URLs
            if clean_path == '/api/controllers/register' or clean_path.startswith('/api/controllers/register'):
                if request.method == 'POST':
                    # This should work, but might be hitting due to malformed URL
                    return jsonify({
                        'error': 'POST request failed due to malformed URL',
                        'message': f'POST method is supported for /api/controllers/register, but your request path "{request.path}" may have extra characters.',
                        'original_path': request.path,
                        'cleaned_path': clean_path,
                        'method': request.method,
                        'solution': 'Ensure your URL is exactly /api/controllers/register without trailing characters',
                        'allowed_methods': ['POST', 'GET'],
                        'hint': 'Check for trailing newlines, spaces, or other characters in your URL.'
                    }), 400  # Return 400 instead of 405 for malformed URL
                else:
                    return jsonify({
                        'error': 'Method not allowed',
                        'message': f'The method {request.method} is not allowed for endpoint /api/controllers/register.',
                        'path': clean_path,
                        'method': request.method,
                        'allowed_methods': ['POST', 'GET'],
                        'hint': 'Use POST method for registration or GET for registration information.'
                    }), 405
            
            # For other API endpoints
            return jsonify({
                'error': 'Method not allowed',
                'message': f'The method {request.method} is not allowed for endpoint {request.path}.',
                'path': request.path,
                'method': request.method,
                'allowed_methods': getattr(error, 'valid_methods', None) or ['GET', 'POST', 'PUT', 'DELETE'],
                'hint': 'Check the API documentation for supported methods on this endpoint.'
            }), 405
        # For non-API routes, use default HTML error page  
        return error
    
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
            
            # Add migration for logo_filename column if it doesn't exist
            try:
                # Try to add the column if it doesn't exist
                with db.engine.connect() as conn:
                    # Check if column exists first
                    result = conn.execute(db.text("PRAGMA table_info(ui_customization)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'logo_filename' not in columns:
                        print("Adding logo_filename column to ui_customization table...")
                        conn.execute(db.text("ALTER TABLE ui_customization ADD COLUMN logo_filename VARCHAR(255)"))
                        conn.commit()
                        print("Logo filename column added successfully")
            except Exception as e:
                print(f"Could not add logo_filename column (might already exist): {e}")
            
            # Add migration for timeout_seconds column if it doesn't exist
            try:
                # Try to add the column if it doesn't exist
                with db.engine.connect() as conn:
                    # Check if column exists first - handle both SQLite and MySQL
                    try:
                        if database_uri.startswith('sqlite'):
                            # SQLite: Use PRAGMA table_info
                            result = conn.execute(db.text("PRAGMA table_info(controllers)"))
                            columns = [row[1] for row in result.fetchall()]
                        else:
                            # MySQL: Use INFORMATION_SCHEMA
                            database_name = database_uri.split('/')[-1]
                            result = conn.execute(db.text(
                                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                "WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = 'controllers'"
                            ), {"db_name": database_name})
                            columns = [row[0] for row in result.fetchall()]
                    except Exception as e:
                        print(f"Could not check for timeout_seconds column: {e}")
                        columns = []
                    
                    if 'timeout_seconds' not in columns:
                        print("Adding timeout_seconds column to controllers table...")
                        conn.execute(db.text("ALTER TABLE controllers ADD COLUMN timeout_seconds INTEGER"))
                        conn.commit()
                        print("Timeout seconds column added successfully")
            except Exception as e:
                print(f"Could not add timeout_seconds column (might already exist): {e}")
            
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
