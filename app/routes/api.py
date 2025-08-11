from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Controller, ControllerData, User
from datetime import datetime, timedelta

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