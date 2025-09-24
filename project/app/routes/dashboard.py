from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import db, Controller, ControllerData
from config.config import Config

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Get user's controllers or all controllers for admin
    if current_user.is_admin:
        controllers = Controller.query.all()
    else:
        controllers = Controller.query.filter_by(user_id=current_user.id).all()
    
    # Get controller statistics
    total_controllers = len(controllers)
    online_controllers = len([c for c in controllers if c.is_online])
    
    version = Config.get_version()
    
    return render_template('dashboard/index.html', 
                         controllers=controllers,
                         total_controllers=total_controllers,
                         online_controllers=online_controllers,
                         version=version)

@dashboard_bp.route('/map-data')
@login_required
def map_data():
    # Get controllers with location data
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
            'id': controller.id,
            'serial_number': controller.serial_number,
            'name': controller.name or controller.serial_number,
            'type': controller.controller_type,
            'latitude': controller.latitude,
            'longitude': controller.longitude,
            'is_online': controller.is_online,
            'last_seen': controller.last_seen.isoformat() if controller.last_seen else None
        })
    
    return jsonify(map_data)