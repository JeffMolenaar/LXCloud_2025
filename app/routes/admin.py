from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User, Controller, UICustomization, Addon

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Administrator access required', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    user_count = User.query.count()
    controller_count = Controller.query.count()
    online_controllers = Controller.query.filter_by(is_online=True).count()
    unbound_controllers = Controller.query.filter_by(user_id=None).count()
    
    return render_template('admin/index.html',
                         user_count=user_count,
                         controller_count=controller_count,
                         online_controllers=online_controllers,
                         unbound_controllers=unbound_controllers)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/reset-2fa', methods=['POST'])
@login_required
@admin_required
def reset_user_2fa(user_id):
    user = User.query.get_or_404(user_id)
    user.two_factor_enabled = False
    user.two_factor_secret = None
    db.session.commit()
    flash(f'2FA has been reset for user {user.username}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form['new_password']
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password has been reset for user {user.username}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin.users'))
    
    # Unbind all controllers
    for controller in user.controllers:
        controller.user_id = None
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/ui-customization')
@login_required
@admin_required
def ui_customization():
    pages = ['dashboard', 'login', 'controllers', 'profile']
    customizations = {}
    
    for page in pages:
        customization = UICustomization.query.filter_by(page_name=page).first()
        if not customization:
            customization = UICustomization(page_name=page)
            db.session.add(customization)
        customizations[page] = customization
    
    db.session.commit()
    return render_template('admin/ui_customization.html', customizations=customizations)

@admin_bp.route('/ui-customization/<page_name>', methods=['POST'])
@login_required
@admin_required
def save_ui_customization(page_name):
    customization = UICustomization.query.filter_by(page_name=page_name).first()
    if not customization:
        customization = UICustomization(page_name=page_name)
        db.session.add(customization)
    
    customization.custom_css = request.form.get('custom_css', '')
    
    # Header configuration
    header_config = {
        'height': request.form.get('header_height', '60px'),
        'logo_text': request.form.get('header_logo_text', 'LXCloud'),
        'background_color': request.form.get('header_bg_color', '#2c3e50'),
        'text_color': request.form.get('header_text_color', '#ffffff')
    }
    customization.set_header_config(header_config)
    
    # Footer configuration
    footer_config = {
        'height': request.form.get('footer_height', '40px'),
        'text': request.form.get('footer_text', '© 2025 LXCloud'),
        'background_color': request.form.get('footer_bg_color', '#34495e'),
        'text_color': request.form.get('footer_text_color', '#ffffff')
    }
    customization.set_footer_config(footer_config)
    
    db.session.commit()
    flash(f'UI customization for {page_name} saved successfully', 'success')
    return redirect(url_for('admin.ui_customization'))

@admin_bp.route('/addons')
@login_required
@admin_required
def addons():
    addons = Addon.query.all()
    return render_template('admin/addons.html', addons=addons)

@admin_bp.route('/addons/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_addon():
    if request.method == 'POST':
        addon = Addon(
            name=request.form['name'],
            controller_type=request.form['controller_type'],
            description=request.form.get('description', ''),
            is_active=True
        )
        
        # Basic configuration
        config = {
            'data_fields': request.form.get('data_fields', '').split(','),
            'display_format': request.form.get('display_format', 'table'),
            'update_interval': int(request.form.get('update_interval', 30))
        }
        addon.set_config(config)
        
        db.session.add(addon)
        db.session.commit()
        flash('Addon created successfully', 'success')
        return redirect(url_for('admin.addons'))
    
    controller_types = ['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera']
    return render_template('admin/new_addon.html', controller_types=controller_types)

@admin_bp.route('/addons/<int:addon_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_addon(addon_id):
    addon = Addon.query.get_or_404(addon_id)
    addon.is_active = not addon.is_active
    db.session.commit()
    status = 'activated' if addon.is_active else 'deactivated'
    flash(f'Addon {addon.name} has been {status}', 'success')
    return redirect(url_for('admin.addons'))

@admin_bp.route('/addons/<int:addon_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_addon(addon_id):
    addon = Addon.query.get_or_404(addon_id)
    name = addon.name
    db.session.delete(addon)
    db.session.commit()
    flash(f'Addon {name} has been deleted', 'success')
    return redirect(url_for('admin.addons'))