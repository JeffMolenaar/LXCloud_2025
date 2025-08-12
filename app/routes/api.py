from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Controller, ControllerData, User
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

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

# Controller API Endpoints (for controller devices to communicate)

@api_bp.route('/controllers/register', methods=['POST'])
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

@api_bp.route('/controllers/<serial_number>/data', methods=['POST'])
def update_controller_data(serial_number):
    """Update controller data"""
    try:
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

@api_bp.route('/controllers/<serial_number>/status', methods=['POST'])
def update_controller_status(serial_number):
    """Update controller status"""
    try:
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

@api_bp.route('/controllers/<serial_number>', methods=['PUT'])
def modify_controller(serial_number):
    """Modify controller configuration"""
    try:
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

@api_bp.route('/controllers/<serial_number>', methods=['GET'])
def get_controller_info(serial_number):
    """Get controller information"""
    try:
        serial_number = serial_number.strip().upper()
        
        controller = Controller.query.filter_by(serial_number=serial_number).first()
        if not controller:
            return jsonify({'error': 'Controller not found'}), 404
        
        return jsonify({
            'controller': controller.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get controller info: {str(e)}'}), 500

@api_bp.route('/controllers/list', methods=['GET'])
def list_all_controllers():
    """List all controllers (for testing - no authentication required)"""
    try:
        controllers = Controller.query.all()
        
        controller_list = []
        for controller in controllers:
            controller_list.append(controller.to_dict())
        
        return jsonify({
            'controllers': controller_list,
            'total': len(controller_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list controllers: {str(e)}'}), 500