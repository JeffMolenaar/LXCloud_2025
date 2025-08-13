from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Controller, ControllerData, User
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

# Add debug logging for routing issues
@api_bp.before_request
def log_request_info():
    """Log request details for debugging"""
    if request.path.startswith('/api/controllers'):
        print(f"API Request: {request.method} {request.path}")
        print(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
        print(f"User-Agent: {request.headers.get('User-Agent', 'Not set')}")
        print(f"Host: {request.headers.get('Host', 'Not set')}")
        if request.is_json:
            print(f"JSON data received: True")
        else:
            print(f"JSON data received: False")
            print(f"Raw data: {request.get_data(as_text=True)[:200]}")
    return None

@api_bp.route('/controllers/status')
@login_required
def controller_status():
    """Get real-time status of controllers"""
    if current_user.is_admin:
        controllers = Controller.query.all()
    else:
        controllers = Controller.query.filter_by(user_id=current_user.id).all()
    
    status_data = []
    for controller in controllers:
        status_data.append({
            'id': controller.id,
            'serial_number': controller.serial_number,
            'name': controller.name or controller.serial_number,
            'type': controller.controller_type,
            'is_online': controller.is_online,
            'last_seen': controller.last_seen.isoformat() if controller.last_seen else None
        })
    
    return jsonify(status_data)

@api_bp.route('/controllers/<int:controller_id>/recent-data')
@login_required
def controller_recent_data(controller_id):
    """Get recent data for a specific controller"""
    controller = Controller.query.get_or_404(controller_id)
    
    # Check permissions
    if not current_user.is_admin and controller.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    data_points = ControllerData.query.filter(
        ControllerData.controller_id == controller_id,
        ControllerData.timestamp >= since
    ).order_by(ControllerData.timestamp.desc()).all()
    
    result = []
    for dp in data_points:
        result.append({
            'timestamp': dp.timestamp.isoformat(),
            'data': dp.get_data_dict()
        })
    
    return jsonify(result)

@api_bp.route('/stats/overview')
@login_required
def stats_overview():
    """Get overview statistics"""
    if current_user.is_admin:
        total_controllers = Controller.query.count()
        online_controllers = Controller.query.filter_by(is_online=True).count()
        total_users = User.query.count()
        unbound_controllers = Controller.query.filter_by(user_id=None).count()
    else:
        user_controllers = Controller.query.filter_by(user_id=current_user.id)
        total_controllers = user_controllers.count()
        online_controllers = user_controllers.filter_by(is_online=True).count()
        total_users = None  # Regular users don't see this
        unbound_controllers = None
    
    return jsonify({
        'total_controllers': total_controllers,
        'online_controllers': online_controllers,
        'offline_controllers': total_controllers - online_controllers,
        'total_users': total_users,
        'unbound_controllers': unbound_controllers
    })

@api_bp.route('/map-data')
@login_required
def map_data():
    """Get map data for visualization from real controller database"""
    # Query controllers that have location data based on user permissions
    if current_user.is_admin:
        controllers = Controller.query.filter(
            Controller.latitude.isnot(None),
            Controller.longitude.isnot(None)
        ).all()
    else:
        controllers = Controller.query.filter(
            Controller.user_id == current_user.id,
            Controller.latitude.isnot(None),
            Controller.longitude.isnot(None)
        ).all()
    
    map_data = []
    for controller in controllers:
        map_data.append({
            "id": controller.id,
            "name": controller.name or controller.serial_number,
            "serial_number": controller.serial_number,
            "latitude": controller.latitude,
            "longitude": controller.longitude,
            "is_online": controller.is_online,
            "type": controller.controller_type,
            "last_seen": controller.last_seen.isoformat() if controller.last_seen else None
        })
    
    return jsonify(map_data)

# Controller API Endpoints (for controller devices to communicate)

@api_bp.route('/controllers/register', methods=['POST'], strict_slashes=False)
def register_controller():
    """Register a new controller device"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        serial_number = data.get('serial_number', '').strip().upper()
        controller_type = data.get('type', '').lower()
        
        if not serial_number:
            return jsonify({'error': 'serial_number is required'}), 400
        
        if not controller_type:
            return jsonify({'error': 'type is required'}), 400
        
        # Valid controller types
        valid_types = ['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera']
        if controller_type not in valid_types:
            return jsonify({'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'}), 400
        
        # Check if controller already exists
        existing_controller = Controller.query.filter_by(serial_number=serial_number).first()
        if existing_controller:
            # Update existing controller
            existing_controller.controller_type = controller_type
            existing_controller.is_online = True
            existing_controller.last_seen = datetime.utcnow()
            
            # Update location if provided
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if latitude is not None and longitude is not None:
                try:
                    existing_controller.latitude = float(latitude)
                    existing_controller.longitude = float(longitude)
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid latitude or longitude values'}), 400
            
            db.session.commit()
            
            return jsonify({
                'message': 'Controller updated successfully',
                'controller': existing_controller.to_dict()
            }), 200
        
        # Create new controller
        controller = Controller(
            serial_number=serial_number,
            controller_type=controller_type,
            name=data.get('name', serial_number),
            is_online=True,
            last_seen=datetime.utcnow()
        )
        
        # Set location if provided
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude is not None and longitude is not None:
            try:
                controller.latitude = float(latitude)
                controller.longitude = float(longitude)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid latitude or longitude values'}), 400
        
        db.session.add(controller)
        db.session.commit()
        
        return jsonify({
            'message': 'Controller registered successfully',
            'controller': controller.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@api_bp.route('/controllers/<serial_number>/data', methods=['POST'], strict_slashes=False)
def update_controller_data(serial_number):
    """Update controller data"""
    try:
        # Handle special reserved words that should not be treated as serial numbers
        if serial_number.lower() in ['register', 'list', 'debug']:
            return jsonify({
                'error': f'Invalid serial number. {serial_number.lower()} is a reserved endpoint.',
                'hint': f'Use POST for /api/controllers/register, GET for /api/controllers/list, or GET for /api/controllers/debug'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        serial_number = serial_number.strip().upper()
        
        # Find controller
        controller = Controller.query.filter_by(serial_number=serial_number).first()
        if not controller:
            return jsonify({'error': 'Controller not found. Register the controller first.'}), 404
        
        # Update controller status
        controller.is_online = True
        controller.last_seen = datetime.utcnow()
        
        # Update location if provided in data
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude is not None and longitude is not None:
            try:
                controller.latitude = float(latitude)
                controller.longitude = float(longitude)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid latitude or longitude values'}), 400
        
        # Store the data (remove metadata from stored data)
        controller_data = data.copy()
        # Remove metadata fields that shouldn't be stored in data
        for field in ['latitude', 'longitude', 'type', 'serial_number']:
            controller_data.pop(field, None)
        
        if controller_data:
            data_point = ControllerData(
                controller_id=controller.id,
                timestamp=datetime.utcnow()
            )
            data_point.set_data_dict(controller_data)
            db.session.add(data_point)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Data updated successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Data update failed: {str(e)}'}), 500

@api_bp.route('/controllers/<serial_number>/status', methods=['POST'], strict_slashes=False)
def update_controller_status(serial_number):
    """Update controller status"""
    try:
        # Handle special reserved words that should not be treated as serial numbers
        if serial_number.lower() in ['register', 'list', 'debug']:
            return jsonify({
                'error': f'Invalid serial number. {serial_number.lower()} is a reserved endpoint.',
                'hint': f'Use POST for /api/controllers/register, GET for /api/controllers/list, or GET for /api/controllers/debug'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        serial_number = serial_number.strip().upper()
        
        # Find controller
        controller = Controller.query.filter_by(serial_number=serial_number).first()
        if not controller:
            return jsonify({'error': 'Controller not found. Register the controller first.'}), 404
        
        # Update status
        online = data.get('online', True)
        controller.is_online = bool(online)
        controller.last_seen = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Status updated successfully',
            'status': 'online' if controller.is_online else 'offline'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Status update failed: {str(e)}'}), 500

@api_bp.route('/controllers/<serial_number>', methods=['PUT'], strict_slashes=False)
def modify_controller(serial_number):
    """Modify controller configuration"""
    try:
        # Handle special reserved words that should not be treated as serial numbers
        if serial_number.lower() in ['register', 'list', 'debug']:
            return jsonify({
                'error': f'Method not allowed. {serial_number.lower()} is a reserved endpoint.',
                'hint': f'Use POST for /api/controllers/register, GET for /api/controllers/list, or GET for /api/controllers/debug'
            }), 405
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        serial_number = serial_number.strip().upper()
        
        # Find controller
        controller = Controller.query.filter_by(serial_number=serial_number).first()
        if not controller:
            return jsonify({'error': 'Controller not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            controller.name = data['name']
        
        if 'type' in data:
            controller_type = data['type'].lower()
            valid_types = ['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera']
            if controller_type in valid_types:
                controller.controller_type = controller_type
            else:
                return jsonify({'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'}), 400
        
        if 'latitude' in data and 'longitude' in data:
            try:
                controller.latitude = float(data['latitude']) if data['latitude'] is not None else None
                controller.longitude = float(data['longitude']) if data['longitude'] is not None else None
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid latitude or longitude values'}), 400
        
        # Update last seen
        controller.last_seen = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Controller updated successfully',
            'controller': controller.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Controller update failed: {str(e)}'}), 500

@api_bp.route('/controllers/<serial_number>', methods=['GET'], strict_slashes=False)
def get_controller_info(serial_number):
    """Get controller information"""
    try:
        # Handle special reserved words that should not be treated as serial numbers
        if serial_number.lower() in ['register', 'list', 'debug']:
            return jsonify({
                'error': f'Method not allowed. {serial_number.lower()} is a reserved endpoint.',
                'hint': f'Use POST for /api/controllers/register, GET for /api/controllers/list, or GET for /api/controllers/debug'
            }), 405
        
        serial_number = serial_number.strip().upper()
        
        controller = Controller.query.filter_by(serial_number=serial_number).first()
        if not controller:
            return jsonify({'error': 'Controller not found'}), 404
        
        return jsonify({
            'controller': controller.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get controller info: {str(e)}'}), 500

@api_bp.route('/controllers/list', methods=['GET'], strict_slashes=False)
@login_required
def list_all_controllers():
    """List controllers based on user permissions"""
    try:
        if current_user.is_admin:
            controllers = Controller.query.all()
        else:
            controllers = Controller.query.filter_by(user_id=current_user.id).all()
        
        controller_list = []
        for controller in controllers:
            controller_list.append(controller.to_dict())
        
        return jsonify({
            'controllers': controller_list,
            'total': len(controller_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list controllers: {str(e)}'}), 500

# Add a specific route to catch GET requests to register endpoint
@api_bp.route('/controllers/register', methods=['GET'], strict_slashes=False)
def register_controller_get():
    """Handle GET requests to register endpoint with helpful error message"""
    request_host = request.headers.get('Host', 'unknown')
    is_docker_env = ':' not in request_host and request_host not in ['localhost', '127.0.0.1']
    
    if is_docker_env:
        correct_url = f"http://{request_host}/api/controllers/register"
    else:
        correct_url = f"http://{request_host}/api/controllers/register"
    
    return jsonify({
        'error': 'Method not allowed. Registration requires POST method.',
        'message': 'You are trying to GET the registration endpoint. Use POST instead.',
        'correct_method': 'POST',
        'correct_url': correct_url,
        'curl_example': f'curl -X POST {correct_url} -H "Content-Type: application/json" -d \'{{"serial_number": "250100.1.0625", "type": "speedradar", "name": "250100.1.0625", "latitude": 51.913071, "longitude": 5.713852}}\'',
        'required_headers': {
            'Content-Type': 'application/json'
        },
        'example_body': {
            'serial_number': '250100.1.0625',
            'type': 'speedradar',
            'name': '250100.1.0625',
            'latitude': 51.913071,
            'longitude': 5.713852
        }
    }), 405

# Handle method not allowed errors with a more specific route that doesn't conflict
@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors for API endpoints"""
    request_host = request.headers.get('Host', 'unknown')
    is_docker_env = ':' not in request_host and request_host not in ['localhost', '127.0.0.1']
    
    if is_docker_env:
        base_url = f"http://{request_host}"
    else:
        base_url = f"http://{request_host}"
    
    if request.path == '/api/controllers/register':
        return jsonify({
            'error': 'Method not allowed. Use POST method for controller registration.',
            'allowed_methods': ['POST'],
            'correct_url': f"{base_url}/api/controllers/register",
            'example': {
                'method': 'POST',
                'url': f"{base_url}/api/controllers/register",
                'content_type': 'application/json',
                'body': {
                    'serial_number': '250100.1.0625',
                    'type': 'speedradar',
                    'name': '250100.1.0625',
                    'latitude': 51.913071,
                    'longitude': 5.713852
                }
            }
        }), 405
    else:
        return jsonify({
            'error': 'Method not allowed for this endpoint.',
            'path': request.path,
            'method': request.method,
            'message': f'The endpoint {request.path} does not support {request.method} method.'
        }), 405

# Troubleshooting endpoint
@api_bp.route('/controllers/debug', methods=['GET', 'POST'], strict_slashes=False)
def debug_endpoint():
    """Debug endpoint to help troubleshoot API issues"""
    
    # Analyze the request to provide specific debugging info
    request_host = request.headers.get('Host', 'unknown')
    
    # Detect if running in Docker or standard setup
    is_docker_env = ':' not in request_host and request_host not in ['localhost', '127.0.0.1']
    
    # Provide appropriate URL guidance based on environment
    if is_docker_env:
        expected_register_url = f"http://{request_host}/api/controllers/register"
        port_guidance = f"DETECTED: Docker environment. Use port 80 (default HTTP): http://{request_host}"
        curl_command = f"curl -X POST http://{request_host}/api/controllers/register"
    else:
        expected_register_url = f"http://{request_host}/api/controllers/register"
        port_guidance = f"DETECTED: Development environment. Current URL is correct: http://{request_host}"
        curl_command = f"curl -X POST http://{request_host}/api/controllers/register"
    
    # Check if this is a GET request to register endpoint (common mistake)
    routing_issue = ""
    if request.path == '/api/controllers/debug' and request.args.get('test_register'):
        routing_issue = "TEST: You're correctly reaching the debug endpoint"
    
    return jsonify({
        'message': 'API endpoints are working correctly',
        'method': request.method,
        'path': request.path,
        'full_url': request.url,
        'environment_analysis': {
            'host_header': request_host,
            'detected_environment': 'Docker (port 80)' if is_docker_env else 'Development (custom port)',
            'port_guidance': port_guidance,
            'correct_register_url': expected_register_url
        },
        'headers': {
            'content-type': request.headers.get('Content-Type'),
            'user-agent': request.headers.get('User-Agent'),
            'host': request.headers.get('Host')
        },
        'json_received': request.is_json,
        'data_received': bool(request.get_data()),
        'routing_diagnosis': {
            'register_endpoint_test': 'POST /api/controllers/register should work',
            'common_mistake': 'GET /api/controllers/register returns Method Not Allowed (this is correct)',
            'route_collision_protection': 'Reserved words (register, list, debug) are protected from serial number conflicts'
        },
        'available_endpoints': {
            'register_controller': {
                'method': 'POST',
                'url': '/api/controllers/register',
                'description': 'Register a new controller or update existing one'
            },
            'update_data': {
                'method': 'POST', 
                'url': '/api/controllers/{serial}/data',
                'description': 'Send sensor data from controller'
            },
            'update_status': {
                'method': 'POST',
                'url': '/api/controllers/{serial}/status', 
                'description': 'Update controller online/offline status'
            },
            'modify_controller': {
                'method': 'PUT',
                'url': '/api/controllers/{serial}',
                'description': 'Modify controller configuration'
            },
            'get_controller': {
                'method': 'GET',
                'url': '/api/controllers/{serial}',
                'description': 'Get controller information'
            },
            'list_controllers': {
                'method': 'GET',
                'url': '/api/controllers/list',
                'description': 'List all controllers'
            }
        },
        'troubleshooting_steps': {
            'step_1': f'Verify you are using: {expected_register_url}',
            'step_2': 'Ensure method is POST (not GET)',
            'step_3': 'Set Content-Type: application/json header',
            'step_4': 'Send valid JSON in request body',
            'step_5': 'Check server logs for detailed error info'
        },
        'curl_example': {
            'command': curl_command,
            'headers': '-H "Content-Type: application/json"',
            'data': '-d \'{"serial_number": "250100.1.0625", "type": "speedradar", "name": "250100.1.0625", "latitude": 51.913071, "longitude": 5.713852}\'',
            'full_example': curl_command + ' -H "Content-Type: application/json" -d \'{"serial_number": "250100.1.0625", "type": "speedradar", "name": "250100.1.0625", "latitude": 51.913071, "longitude": 5.713852}\''
        }
    }), 200
