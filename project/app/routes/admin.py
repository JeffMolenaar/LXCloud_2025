from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
import os
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
    try:
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
    except Exception as e:
        db.session.rollback()
        print(f"Error in ui_customization: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading UI customization: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/ui-customization/<page_name>', methods=['POST'])
@login_required
@admin_required
def save_ui_customization(page_name):
    try:
        # Validate page_name
        valid_pages = ['dashboard', 'login', 'controllers', 'profile']
        if page_name not in valid_pages:
            flash(f'Invalid page name: {page_name}', 'error')
            return redirect(url_for('admin.ui_customization'))
        
        customization = UICustomization.query.filter_by(page_name=page_name).first()
        if not customization:
            customization = UICustomization(page_name=page_name)
            db.session.add(customization)
        
        customization.custom_css = request.form.get('custom_css', '')
        
        # Handle logo upload
        if 'logo_file' in request.files:
            logo_file = request.files['logo_file']
            if logo_file and logo_file.filename:
                try:
                    # Ensure uploads directory exists
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Secure the filename and save
                    filename = secure_filename(logo_file.filename)
                    if not filename:
                        flash('Invalid filename for logo upload', 'error')
                    else:
                        # Add timestamp to avoid conflicts
                        name, ext = os.path.splitext(filename)
                        filename = f"logo_{page_name}_{name}{ext}"
                        file_path = os.path.join(upload_dir, filename)
                        
                        logo_file.save(file_path)
                        customization.logo_filename = filename
                        flash(f'Logo uploaded successfully for {page_name}', 'success')
                except Exception as e:
                    print(f"Error uploading logo: {str(e)}")
                    flash(f'Error uploading logo: {str(e)}', 'error')
        
        # Header configuration
        try:
            header_config = {
                'height': request.form.get('header_height', '60px'),
                'logo_text': request.form.get('header_logo_text', 'LXCloud'),
                'background_color': request.form.get('header_bg_color', '#2c3e50'),
                'text_color': request.form.get('header_text_color', '#ffffff'),
                'logo_left_padding': request.form.get('logo_left_padding', '15px'),
                'logo_menu_spacing': request.form.get('logo_menu_spacing', '30px'),
                'user_button_right_padding': request.form.get('user_button_right_padding', '15px'),
                'use_custom_logo': customization.logo_filename is not None
            }
            customization.set_header_config(header_config)
        except Exception as e:
            print(f"Error setting header config: {str(e)}")
            flash(f'Error saving header configuration: {str(e)}', 'error')
        
        # Footer configuration
        try:
            footer_config = {
                'height': request.form.get('footer_height', '40px'),
                'text': request.form.get('footer_text', '© 2025 LXCloud'),
                'background_color': request.form.get('footer_bg_color', '#34495e'),
                'text_color': request.form.get('footer_text_color', '#ffffff')
            }
            customization.set_footer_config(footer_config)
        except Exception as e:
            print(f"Error setting footer config: {str(e)}")
            flash(f'Error saving footer configuration: {str(e)}', 'error')
        
        # Marker configuration
        try:
            controller_types = ['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera', 'default']
            marker_config = customization.get_marker_config()  # Get existing config to preserve uploaded icons
            
            for controller_type in controller_types:
                # Initialize if not exists
                if controller_type not in marker_config:
                    marker_config[controller_type] = {'online': {}, 'offline': {}}
                
                # Handle icon uploads for online state
                online_icon_file = request.files.get(f'marker_{controller_type}_online_icon_file')
                if online_icon_file and online_icon_file.filename:
                    try:
                        # Ensure uploads directory exists
                        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Secure the filename and save
                        filename = secure_filename(online_icon_file.filename)
                        if filename and filename.lower().endswith('.png'):
                            # Add timestamp and controller type to avoid conflicts
                            name, ext = os.path.splitext(filename)
                            icon_filename = f"marker_{controller_type}_online_{name}{ext}"
                            file_path = os.path.join(upload_dir, icon_filename)
                            
                            online_icon_file.save(file_path)
                            marker_config[controller_type]['online']['custom_icon'] = icon_filename
                            flash(f'Online icon uploaded successfully for {controller_type}', 'success')
                        else:
                            flash(f'Invalid file type for {controller_type} online icon. Only PNG files are allowed.', 'error')
                    except Exception as e:
                        print(f"Error uploading online icon for {controller_type}: {str(e)}")
                        flash(f'Error uploading online icon for {controller_type}: {str(e)}', 'error')
                
                # Handle icon uploads for offline state
                offline_icon_file = request.files.get(f'marker_{controller_type}_offline_icon_file')
                if offline_icon_file and offline_icon_file.filename:
                    try:
                        # Ensure uploads directory exists
                        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Secure the filename and save
                        filename = secure_filename(offline_icon_file.filename)
                        if filename and filename.lower().endswith('.png'):
                            # Add timestamp and controller type to avoid conflicts
                            name, ext = os.path.splitext(filename)
                            icon_filename = f"marker_{controller_type}_offline_{name}{ext}"
                            file_path = os.path.join(upload_dir, icon_filename)
                            
                            offline_icon_file.save(file_path)
                            marker_config[controller_type]['offline']['custom_icon'] = icon_filename
                            flash(f'Offline icon uploaded successfully for {controller_type}', 'success')
                        else:
                            flash(f'Invalid file type for {controller_type} offline icon. Only PNG files are allowed.', 'error')
                    except Exception as e:
                        print(f"Error uploading offline icon for {controller_type}: {str(e)}")
                        flash(f'Error uploading offline icon for {controller_type}: {str(e)}', 'error')
                
                # Update marker configuration with form data
                marker_config[controller_type]['online'].update({
                    'icon': request.form.get(f'marker_{controller_type}_online_icon', 'fas fa-microchip'),
                    'color': request.form.get(f'marker_{controller_type}_online_color', '#28a745'),
                    'size': request.form.get(f'marker_{controller_type}_online_size', '30')
                })
                marker_config[controller_type]['offline'].update({
                    'icon': request.form.get(f'marker_{controller_type}_offline_icon', 'fas fa-microchip'),
                    'color': request.form.get(f'marker_{controller_type}_offline_color', '#dc3545'),
                    'size': request.form.get(f'marker_{controller_type}_offline_size', '30')
                })
            
            customization.set_marker_config(marker_config)
        except Exception as e:
            print(f"Error setting marker config: {str(e)}")
            flash(f'Error saving marker configuration: {str(e)}', 'error')

        # Map (OpenStreetMap) configuration
        try:
            map_config = customization.get_map_config() if hasattr(customization, 'get_map_config') else {}
            # Read posted OSM fields
            osm_tile_source = request.form.get('osm_tile_source')
            osm_default_zoom = request.form.get('osm_default_zoom')
            osm_show_attribution = request.form.get('osm_show_attribution')
            osm_max_bounds = request.form.get('osm_max_bounds')

            if osm_tile_source is not None:
                map_config['tile_source'] = osm_tile_source
            if osm_default_zoom:
                try:
                    map_config['default_zoom'] = int(osm_default_zoom)
                except ValueError:
                    map_config['default_zoom'] = map_config.get('default_zoom', 12)
            if osm_show_attribution is not None:
                map_config['show_attribution'] = True if osm_show_attribution in ['true', 'True', '1'] else False
            if osm_max_bounds is not None:
                map_config['max_bounds'] = osm_max_bounds

            # Persist map configuration
            if hasattr(customization, 'set_map_config'):
                customization.set_map_config(map_config)
        except Exception as e:
            print(f"Error setting map config: {str(e)}")
            flash(f'Error saving map configuration: {str(e)}', 'error')
        
        db.session.commit()
        flash(f'UI customization for {page_name} saved successfully', 'success')
        return redirect(url_for('admin.ui_customization'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in save_ui_customization for {page_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error saving UI customization: {str(e)}', 'error')
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

@admin_bp.route('/api/marker-config')
def get_marker_config():
    """API endpoint to get marker configuration for dashboard"""
    dashboard_customization = UICustomization.query.filter_by(page_name='dashboard').first()
    
    if dashboard_customization:
        marker_config = dashboard_customization.get_marker_config()
    else:
        # Default configuration
        marker_config = {}
    
    # Ensure we have default values for all controller types
    controller_types = ['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera', 'default']
    default_icons = {
        'speedradar': 'fas fa-tachometer-alt',
        'beaufortmeter': 'fas fa-wind',
        'weatherstation': 'fas fa-cloud-sun',
        'aicamera': 'fas fa-camera',
        'default': 'fas fa-microchip'
    }
    
    for controller_type in controller_types:
        if controller_type not in marker_config:
            marker_config[controller_type] = {
                'online': {
                    'icon': default_icons[controller_type],
                    'color': '#28a745',
                    'size': '30'
                },
                'offline': {
                    'icon': default_icons[controller_type],
                    'color': '#dc3545',
                    'size': '30'
                }
            }
    
    return jsonify(marker_config)