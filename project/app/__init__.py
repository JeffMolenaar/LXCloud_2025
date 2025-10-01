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
            print(
                f"Template folder not found at {template_folder}, "
                f"using fallback: {cwd_template_folder}"
            )
            project_root = cwd_project_root
            template_folder = cwd_template_folder
            static_folder = cwd_static_folder
    
    # Method 3: Last resort - check common deployment paths
    if not os.path.exists(template_folder):
        deployment_paths = [
            '/home/lxcloud/LXCloud', '/app', os.path.expanduser('~/LXCloud')
        ]
        for deployment_root in deployment_paths:
            deployment_template_folder = os.path.join(deployment_root, 'templates')
            deployment_static_folder = os.path.join(deployment_root, 'static')
            
            if os.path.exists(deployment_template_folder):
                print(
                    f"Template folder not found at {template_folder}, "
                    f"using deployment path: {deployment_template_folder}"
                )
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
            print("Auth login template is readable")
        except Exception as e:
            print(f"Auth login template exists but is not readable: {e}")
    
    if not os.path.exists(template_folder):
        print("ERROR: Template folder not found. Debugging info:")
        print(f"  - Current working directory: {os.getcwd()}")
        print(f"  - __file__: {__file__}")
        print(f"  - Absolute __file__: {os.path.abspath(__file__)}")
        print("  - Directory contents at project_root:")
        try:
            project_contents = os.listdir(project_root)
            print(f"    {project_contents}")
        except Exception as e:
            print(f"    Could not list directory: {e}")
        raise RuntimeError(
            f"Template folder not found. Tried: {template_folder}"
        )
    
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
    
    # Use MariaDB database configuration
    original_config = Config()
    mysql_uri = original_config.SQLALCHEMY_DATABASE_URI
    
    # Test database connectivity
    database_uri = mysql_uri
    try:
        print("Testing MariaDB database connectivity...")
        from config.database_config import get_database_config
        db_config = get_database_config()
        
        if db_config.test_connection():
            print("MariaDB database connection successful")
        else:
            raise Exception("MariaDB connection test failed")
    except Exception as e:
        print(f"MariaDB connection failed: {e}")
        print("ERROR: MariaDB is required for this application!")
        print("Please ensure MariaDB is running and the database 'lxcloud' exists.")
        raise Exception("Database connection failed - MariaDB required")
    
    # Set the MariaDB database URI
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Initialize debug reporting
    from app.debug_reporter import debug_reporter
    debug_reporter.init_app(app)
    
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
        global_custom_css = None
        login_config = {}
        
        try:
            customizations = UICustomization.query.all()
            for customization in customizations:
                ui_customizations[customization.page_name] = {
                    'header_config': customization.get_header_config(),
                    'footer_config': customization.get_footer_config(),
                    'logo_filename': getattr(customization, 'logo_filename', None),
                    'custom_css': customization.custom_css
                }
            
            # Get global custom CSS from the configuration
            global_config = UICustomization.get_config()
            global_custom_css = global_config.get('custom_css')
            
            # Get login configuration
            login_customization = UICustomization.query.filter_by(page_name='__login__').first()
            if login_customization:
                login_config = login_customization.get_login_config()
                # Fallback for JSON parsing
                if not login_config and login_customization.map_config:
                    try:
                        import json
                        login_config = json.loads(login_customization.map_config)
                    except (json.JSONDecodeError, TypeError):
                        login_config = {}
            
        except Exception as e:
            print(f"Warning: Could not load UI customizations: {e}")
            # Continue without UI customizations
        
        return dict(
            version=Config.get_version(),
            ui_customizations=ui_customizations,
            global_custom_css=global_custom_css,
            login_config=login_config,
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
        
        # Import debug route for testing
        import sys
        debug_route_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug_route.py')
        if os.path.exists(debug_route_path):
            sys.path.insert(0, os.path.dirname(debug_route_path))
            from debug_route import debug_bp
        
    except ImportError as e:
        print(f"Import error: {e}")
        raise
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(controllers_bp, url_prefix='/controllers')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Favicon route to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        favicon_path = os.path.join(app.static_folder, 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(
                app.static_folder, 'favicon.ico', 
                mimetype='image/vnd.microsoft.icon'
            )
        # Return empty response with 204 (No Content) if no favicon
        from flask import make_response
        response = make_response('', 204)
        return response
    
    # Register debug blueprint if available
    try:
        app.register_blueprint(debug_bp, url_prefix='/debug')
    except NameError:
        pass  # debug_bp not available
    
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
            
            # NOTE: All DDL migrations removed to prevent metadata locks
            # Tables created via db.create_all() from model definitions
            # All columns defined in models.py are automatically created
            print("Database schema created from model definitions")

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
            print(
                "Application will continue but database "
                "functionality may be limited"
            )
    
    return app
