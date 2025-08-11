from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, Controller, ControllerData

controllers_bp = Blueprint('controllers', __name__)

@controllers_bp.route('/')
@login_required
def index():
    if current_user.is_admin:
        controllers = Controller.query.all()
        unbound_controllers = Controller.query.filter_by(user_id=None).all()
    else:
        controllers = Controller.query.filter_by(user_id=current_user.id).all()
        unbound_controllers = []
    
    return render_template('controllers/index.html', 
                         controllers=controllers,
                         unbound_controllers=unbound_controllers)

@controllers_bp.route('/bind', methods=['POST'])
@login_required
def bind_controller():
    serial_number = request.form['serial_number'].strip().upper()
    
    # Find controller by serial number
    controller = Controller.query.filter_by(serial_number=serial_number).first()
    
    if not controller:
        flash(f'Controller with serial number {serial_number} not found or never reported to server', 'error')
        return redirect(url_for('controllers.index'))
    
    if controller.user_id and not current_user.is_admin:
        flash('Controller is already bound to another user', 'error')
        return redirect(url_for('controllers.index'))
    
    # Bind controller to current user
    controller.user_id = current_user.id
    if not controller.name:
        controller.name = serial_number
    
    db.session.commit()
    flash(f'Controller {serial_number} has been bound successfully', 'success')
    return redirect(url_for('controllers.index'))

@controllers_bp.route('/<int:controller_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_controller(controller_id):
    controller = Controller.query.get_or_404(controller_id)
    
    # Check permissions
    if not current_user.is_admin and controller.user_id != current_user.id:
        flash('You do not have permission to edit this controller', 'error')
        return redirect(url_for('controllers.index'))
    
    if request.method == 'POST':
        controller.name = request.form['name']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        if latitude and longitude:
            try:
                controller.latitude = float(latitude)
                controller.longitude = float(longitude)
            except ValueError:
                flash('Invalid latitude or longitude values', 'error')
                return render_template('controllers/edit.html', controller=controller)
        
        db.session.commit()
        flash('Controller updated successfully', 'success')
        return redirect(url_for('controllers.index'))
    
    return render_template('controllers/edit.html', controller=controller)

@controllers_bp.route('/<int:controller_id>/unbind', methods=['POST'])
@login_required
def unbind_controller(controller_id):
    controller = Controller.query.get_or_404(controller_id)
    
    # Check permissions
    if not current_user.is_admin and controller.user_id != current_user.id:
        flash('You do not have permission to unbind this controller', 'error')
        return redirect(url_for('controllers.index'))
    
    controller.user_id = None
    db.session.commit()
    flash('Controller unbound successfully', 'success')
    return redirect(url_for('controllers.index'))

@controllers_bp.route('/<int:controller_id>/data')
@login_required
def view_data(controller_id):
    controller = Controller.query.get_or_404(controller_id)
    
    # Check permissions
    if not current_user.is_admin and controller.user_id != current_user.id:
        flash('You do not have permission to view this controller data', 'error')
        return redirect(url_for('controllers.index'))
    
    # Get recent data points
    data_points = ControllerData.query.filter_by(controller_id=controller_id)\
        .order_by(ControllerData.timestamp.desc())\
        .limit(100).all()
    
    return render_template('controllers/data.html', 
                         controller=controller,
                         data_points=data_points)

@controllers_bp.route('/<int:controller_id>/data/api')
@login_required
def api_data(controller_id):
    controller = Controller.query.get_or_404(controller_id)
    
    # Check permissions
    if not current_user.is_admin and controller.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get recent data points
    limit = request.args.get('limit', 50, type=int)
    data_points = ControllerData.query.filter_by(controller_id=controller_id)\
        .order_by(ControllerData.timestamp.desc())\
        .limit(limit).all()
    
    result = []
    for dp in data_points:
        result.append({
            'timestamp': dp.timestamp.isoformat(),
            'data': dp.get_data_dict()
        })
    
    return jsonify(result)