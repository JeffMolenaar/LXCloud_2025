from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
import os
import time
import json
import datetime
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
    
    return render_template(
        'admin/index.html',
        user_count=user_count,
        controller_count=controller_count,
        online_controllers=online_controllers,
        unbound_controllers=unbound_controllers,
    )

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
@admin_bp.route('/ui-customization/<page_name>')
@login_required
@admin_required
def ui_customization(page_name='dashboard'):
    try:
        # Normaliseer login alias naar '__login__'
        if page_name == 'login':
            return redirect(url_for(
                'admin.ui_customization', page_name='__login__'
            ))

        pages = ['dashboard', '__login__', 'controllers', 'profile']
        customizations = {}

        # Zorg dat basispagina's bestaan
        for page in pages:
            customization = UICustomization.query.filter_by(
                page_name=page
            ).first()
            if not customization:
                customization = UICustomization(page_name=page)
                db.session.add(customization)
            customizations[page] = customization

        # Haal huidige pagina customization altijd rechtstreeks uit DB
        current_customization = UICustomization.query.filter_by(
            page_name=page_name
        ).first()
        if not current_customization:
            current_customization = UICustomization(page_name=page_name)
            db.session.add(current_customization)
        
        # Haal login_config op voor de __login__ pagina
        login_config = {}
        if page_name == '__login__':
            login_config = current_customization.get_login_config()
        
        db.session.commit()
        return render_template(
            'admin/ui_customization.html',
            customizations=customizations,
            page_name=page_name,
            customization=current_customization,
            login_config=login_config
        )
    except Exception as e:
        db.session.rollback()
        print(f"Error in ui_customization: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading UI customization: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/ui-customization/bulk-upload', methods=['POST'])
@login_required
@admin_required
def bulk_upload_icons():
    """Handle bulk icon uploads for markers"""
    try:
        page_name = request.form.get('page_name', 'dashboard')
        
        customization = UICustomization.query.filter_by(page_name=page_name).first()
        if not customization:
            customization = UICustomization(page_name=page_name)
            db.session.add(customization)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(base_dir, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        uploaded_files = []
        
        # Process each uploaded file
        for key in request.files:
            file = request.files[key]
            if file and file.filename:
                try:
                    filename = secure_filename(file.filename)
                    if filename and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                        # Generate unique filename
                        name, ext = os.path.splitext(filename)
                        timestamp = int(time.time())
                        new_filename = f"bulk_{timestamp}_{name}{ext}"
                        file_path = os.path.join(upload_dir, new_filename)
                        
                        file.save(file_path)
                        uploaded_files.append({
                            'original': filename,
                            'saved': new_filename,
                            'path': file_path
                        })
                except Exception as e:
                    print(f"Error processing file {file.filename}: {str(e)}")
        
        if uploaded_files:
            flash(f'{len(uploaded_files)} iconen succesvol geüpload voor bulk assignment', 'success')
        else:
            flash('Geen geldige bestanden gevonden voor upload', 'warning')
        
        return jsonify({
            'success': True,
            'uploaded_files': uploaded_files,
            'message': f'{len(uploaded_files)} files uploaded successfully'
        })
        
    except Exception as e:
        print(f"Error in bulk_upload_icons: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/ui-customization/remove-icon', methods=['POST'])
@login_required
@admin_required
def remove_icon():
    """Remove an uploaded icon"""
    try:
        data = request.get_json()
        controller_type = data.get('controller_type')
        state = data.get('state')  # 'online' or 'offline'
        page_name = data.get('page_name', 'dashboard')
        
        customization = UICustomization.query.filter_by(page_name=page_name).first()
        if customization:
            marker_config = customization.get_marker_config()
            
            if controller_type in marker_config and state in marker_config[controller_type]:
                # Get the filename to delete
                icon_filename = marker_config[controller_type][state].get('custom_icon')
                
                if icon_filename:
                    # Remove from filesystem
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    file_path = os.path.join(base_dir, 'static', 'uploads', icon_filename)
                    
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing file {file_path}: {str(e)}")
                    
                    # Remove from config
                    if 'custom_icon' in marker_config[controller_type][state]:
                        del marker_config[controller_type][state]['custom_icon']
                    
                    customization.set_marker_config(marker_config)
                    db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in remove_icon: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/remove-marker-icon', methods=['POST'])
@login_required
@admin_required
def remove_marker_icon():
    """Remove an uploaded icon from marker configuration"""
    try:
        data = request.get_json()
        page_name = data.get('page_name', 'dashboard')
        controller_type = data.get('controller_type')
        state = data.get('state')  # 'online' or 'offline'
        
        if not controller_type or not state:
            return jsonify({
                'success': False, 
                'error': 'Missing parameters'
            }), 400
            
        # Get customization record
        customization = UICustomization.query.filter_by(
            page_name=page_name
        ).first()
        if not customization:
            return jsonify({
                'success': False, 
                'error': 'No customization found'
            }), 404
            
        # Get marker config
        marker_config = customization.get_marker_config()
        
        # Remove the custom icon if exists
        if (controller_type in marker_config and
                state in marker_config[controller_type] and
                'custom_icon' in marker_config[controller_type][state]):
            
            old_icon = marker_config[controller_type][state]['custom_icon']
            
            # Delete the actual file
            base_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
            old_file_path = os.path.join(
                base_dir, 'static', 'uploads', old_icon
            )
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                
            # Remove from config
            del marker_config[controller_type][state]['custom_icon']
            
            # Save updated config
            customization.set_marker_config(marker_config)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Icon verwijderd voor {controller_type} {state}'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No icon found to remove'
            }), 404
            
    except Exception as e:
        print(f"Error removing marker icon: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/ui-customization/<page_name>', methods=['POST'])
@login_required
@admin_required
def save_ui_customization(page_name):
    # Initialize debug logging function
    def server_debug_log(message, data=None):
        try:
            debug_dir = '/home/lxcloud/debug'
            os.makedirs(debug_dir, exist_ok=True)
            log_filename = f"server_debug_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
            log_path = os.path.join(debug_dir, log_filename)
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_entry = f"[{timestamp}] {message}\n"
            if data:
                log_entry += f"Data: {data}\n"
            log_entry += f"User: {current_user.username}\n"
            log_entry += f"Page: {page_name}\n"
            log_entry += "-" * 80 + "\n"
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Debug logging error: {e}")
    
    # TEST: Just check if any files have actual content
    print("=== SIMPLE FILE CHECK ===")
    for key in request.files:
        file_obj = request.files[key]
        if file_obj and hasattr(file_obj, 'filename') and file_obj.filename:
            # Read file size without moving pointer
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            print(f"FOUND FILE: {key} = {file_obj.filename} ({file_size} bytes)")
            server_debug_log(f"FOUND VALID FILE: {key} = {file_obj.filename} ({file_size} bytes)")
        else:
            print(f"EMPTY/NO FILE: {key} (filename: {getattr(file_obj, 'filename', 'NO_ATTR') if file_obj else 'NO_OBJ'})")
            if file_obj:
                server_debug_log(f"EMPTY FILE OBJECT: {key} has filename='{file_obj.filename}' content_type='{file_obj.content_type}'")
    
    # Additional debug: Log all form data  
    server_debug_log("=== FORM DATA DEBUG ===")
    for key, value in request.form.items():
        if 'color' in key.lower() or 'height' in key.lower():
            server_debug_log(f"Form field: {key} = {value}")
    
    server_debug_log(f"=== UI CUSTOMIZATION SAVE START for {page_name} ===")
    server_debug_log(f"Request method: {request.method}")
    server_debug_log(f"Request files: {list(request.files.keys())}")
    server_debug_log(f"Request form keys: {list(request.form.keys())}")
    
    try:
        # Normaliseer login alias naar '__login__'
        if page_name == 'login':
            page_name = '__login__'

        # Validate page_name
        valid_pages = ['dashboard', '__login__', 'controllers', 'profile']
        if page_name not in valid_pages:
            flash(f'Invalid page name: {page_name}', 'error')
            return redirect(url_for('admin.ui_customization'))
        
        customization = UICustomization.query.filter_by(page_name=page_name).first()
        if not customization:
            customization = UICustomization(page_name=page_name)
            db.session.add(customization)
        
        customization.custom_css = request.form.get('custom_css', '')
        
        # Handle logo upload
        # compute base directory once to keep lines short
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if 'logo_file' in request.files:
            logo_file = request.files['logo_file']
            if logo_file and logo_file.filename:
                try:
                    # Ensure uploads directory exists (compute once)
                    upload_dir = os.path.join(base_dir, 'static', 'uploads')
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
                server_debug_log(f"Checking online icon file for {controller_type}")
                server_debug_log(f"File object exists: {online_icon_file is not None}")
                server_debug_log(f"Filename: {online_icon_file.filename if online_icon_file else 'None'}")
                
                if online_icon_file and online_icon_file.filename:
                    try:
                        # Ensure uploads directory exists
                        upload_dir = os.path.join(base_dir, 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        print(f"DEBUG: Upload directory created: {upload_dir}")

                        # Remove old icon if exists
                        if ('online' in marker_config[controller_type] and 
                            'custom_icon' in marker_config[controller_type]['online']):
                            old_icon = marker_config[controller_type]['online']['custom_icon']
                            old_file_path = os.path.join(upload_dir, old_icon)
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)
                                print(f"DEBUG: Removed old file: {old_file_path}")

                        # Secure the filename and save
                        filename = secure_filename(online_icon_file.filename)
                        print(f"DEBUG: Secured filename: {filename}")
                        if filename and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                            # Add controller type and timestamp to avoid conflicts
                            name, ext = os.path.splitext(filename)
                            timestamp = int(time.time())
                            icon_filename = f"marker_{controller_type}_online_{timestamp}{ext}"
                            file_path = os.path.join(upload_dir, icon_filename)
                            print(f"DEBUG: Saving to: {file_path}")

                            online_icon_file.save(file_path)
                            print(f"DEBUG: File saved successfully")
                            marker_config[controller_type]['online']['custom_icon'] = icon_filename
                            flash(f'Online icon uploaded/vervangen voor {controller_type}', 'success')
                        else:
                            flash(f'Ongeldig bestandstype voor {controller_type} online icon. Alleen PNG, JPG, SVG toegestaan.', 'error')
                    except Exception as e:
                        print(f"ERROR uploading online icon for {controller_type}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        flash(f'Fout bij uploaden online icon voor {controller_type}', 'error')
                
                # Handle icon uploads for offline state
                offline_icon_file = request.files.get(f'marker_{controller_type}_offline_icon_file')
                if offline_icon_file and offline_icon_file.filename:
                    try:
                        # Ensure uploads directory exists
                        upload_dir = os.path.join(base_dir, 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)

                        # Remove old icon if exists
                        if ('offline' in marker_config[controller_type] and 
                            'custom_icon' in marker_config[controller_type]['offline']):
                            old_icon = marker_config[controller_type]['offline']['custom_icon']
                            old_file_path = os.path.join(upload_dir, old_icon)
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)
                                print(f"DEBUG: Removed old offline file: {old_file_path}")

                        # Secure the filename and save
                        filename = secure_filename(offline_icon_file.filename)
                        if filename and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                            # Add controller type and timestamp to avoid conflicts
                            name, ext = os.path.splitext(filename)
                            timestamp = int(time.time())
                            icon_filename = f"marker_{controller_type}_offline_{timestamp}{ext}"
                            file_path = os.path.join(upload_dir, icon_filename)

                            offline_icon_file.save(file_path)
                            marker_config[controller_type]['offline']['custom_icon'] = icon_filename
                            flash(f'Offline icon uploaded/vervangen voor {controller_type}', 'success')
                        else:
                            flash(f'Ongeldig bestandstype voor {controller_type} offline icon. Alleen PNG, JPG, SVG toegestaan.', 'error')
                    except Exception as e:
                        error_msg = f"Error uploading offline icon for {controller_type}: {str(e)}"
                        print(error_msg)
                        import traceback
                        print("Full traceback:")
                        traceback.print_exc()
                        
                        # Log to debug file as well
                        server_debug_log(error_msg, str(e))
                        server_debug_log("Full exception traceback", traceback.format_exc())
                        
                        flash(f'Fout bij uploaden offline icon voor {controller_type}: {str(e)}', 'error')
                
                # Update marker configuration with form data
                marker_config[controller_type]['online']['color'] = request.form.get(f'marker_{controller_type}_online_color', '#28a745')
                marker_config[controller_type]['offline']['color'] = request.form.get(f'marker_{controller_type}_offline_color', '#dc3545')
                
                # Add icon size configuration
                icon_height = request.form.get(f'marker_{controller_type}_icon_height', '32')
                marker_config[controller_type]['icon_height'] = f'{icon_height}px'
            
            customization.set_marker_config(marker_config)
        except Exception as e:
            print(f"Error setting marker config: {str(e)}")
            flash(f'Fout bij opslaan marker configuratie: {str(e)}', 'error')

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

@admin_bp.route('/test-upload', methods=['GET', 'POST'])
@login_required
@admin_required
def test_upload():
    if request.method == 'POST':
        print("=== TEST UPLOAD START ===")
        print(f"Files received: {list(request.files.keys())}")
        
        for key, file_obj in request.files.items():
            print(f"Processing file key: {key}")
            print(f"File object: {file_obj}")
            if hasattr(file_obj, 'filename'):
                print(f"Filename: {file_obj.filename}")
                if file_obj.filename:
                    try:
                        content_length = len(file_obj.read())
                        file_obj.seek(0)
                        print(f"File size: {content_length} bytes")
                        
                        # Try to save the file
                        upload_dir = '/home/lxcloud/debug'
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        filename = f"test_{int(time.time())}_{file_obj.filename}"
                        file_path = os.path.join(upload_dir, filename)
                        
                        file_obj.save(file_path)
                        print(f"File saved successfully to: {file_path}")
                        flash(f'File {file_obj.filename} uploaded!', 'success')
                        
                    except Exception as e:
                        print(f"Error saving file: {str(e)}")
                        flash(f'Error uploading file: {str(e)}', 'error')
                else:
                    print(f"Empty filename for key: {key}")
            else:
                print(f"No filename attribute for key: {key}")
        
        print("=== TEST UPLOAD END ===")
        return redirect(url_for('admin.test_upload'))
    
    # GET request - show simple upload form
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Test Upload</title></head>
    <body>
        <h1>Test File Upload</h1>
        <form method="POST" enctype="multipart/form-data">
            <p><label>Test File: <input type="file" name="test_file" required></label></p>
            <p><input type="submit" value="Upload Test File"></p>
        </form>
        <p><a href="/admin">Back to Admin</a></p>
    </body>
    </html>
    '''

@admin_bp.route('/debug-log', methods=['POST'])
@login_required
@admin_required
def debug_log():
    """Debug logging endpoint to write client-side logs to file"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create debug directory if it doesn't exist
        debug_dir = '/home/lxcloud/debug'
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create log filename with date
        log_filename = f"ui_debug_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        log_path = os.path.join(debug_dir, log_filename)
        
        # Format log entry
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {data.get('message', 'No message')}\n"
        
        if data.get('data'):
            log_entry += f"Data: {data['data']}\n"
        
        log_entry += f"User: {current_user.username}\n"
        log_entry += f"Page: {data.get('page', 'unknown')}\n"
        log_entry += f"Action: {data.get('action', 'unknown')}\n"
        log_entry += "-" * 80 + "\n"
        
        # Write to file
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return jsonify({'success': True, 'log_file': log_path})
        
    except Exception as e:
        print(f"Error in debug_log endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        else:
            # Ensure all required fields exist, preserving custom_icon if present
            for state in ['online', 'offline']:
                if state not in marker_config[controller_type]:
                    marker_config[controller_type][state] = {}
                
                # Set defaults for missing fields, but preserve existing values
                config = marker_config[controller_type][state]
                if 'icon' not in config:
                    config['icon'] = default_icons[controller_type]
                if 'color' not in config:
                    config['color'] = '#28a745' if state == 'online' else '#dc3545'
                if 'size' not in config:
                    config['size'] = '30'
                # custom_icon is preserved if it exists
    
    return jsonify(marker_config)


@admin_bp.route('/upload-marker-icon', methods=['POST'])
@login_required
@admin_required
def upload_marker_icon():
    """Upload a marker icon via AJAX"""
    try:
        # Get form data
        file = request.files.get('file')
        controller_type = request.form.get('controller_type')
        state = request.form.get('state')
        page_name = request.form.get('page_name', 'dashboard')
        
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        if not controller_type or not state:
            return jsonify({'success': False, 'error': 'Missing controller_type or state'})
        
        # Validate file
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, SVG allowed'})
        
        if file.content_length and file.content_length > 2 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File too large. Maximum 2MB allowed'})
        
        # Get/create UI customization record
        customization = UICustomization.query.filter_by(page_name=page_name).first()
        if not customization:
            customization = UICustomization(page_name=page_name)
            db.session.add(customization)
        
        # Get current marker config
        marker_config = customization.get_marker_config()
        if controller_type not in marker_config:
            marker_config[controller_type] = {'online': {}, 'offline': {}}
        
        if state not in marker_config[controller_type]:
            marker_config[controller_type][state] = {}
        
        # Ensure uploads directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(base_dir, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Remove old icon if exists
        if 'custom_icon' in marker_config[controller_type][state]:
            old_icon = marker_config[controller_type][state]['custom_icon']
            old_file_path = os.path.join(upload_dir, old_icon)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Create new filename with timestamp
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = int(time.time())
        icon_filename = f"marker_{controller_type}_{state}_{timestamp}{ext}"
        file_path = os.path.join(upload_dir, icon_filename)
        
        # Save file
        file.save(file_path)
        
        # Update marker config
        marker_config[controller_type][state]['custom_icon'] = icon_filename
        customization.set_marker_config(marker_config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': icon_filename,
            'icon_url': f'/static/uploads/{icon_filename}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in upload_marker_icon: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/upload-login-logo', methods=['POST'])
@login_required
def upload_login_logo():
    """Handle AJAX login logo upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'svg'}
        if '.' in file.filename:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
        else:
            file_ext = ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': 'Invalid file type. Only PNG, JPG, and SVG allowed.'
            })
        
        # Create uploads directory structure (flat ui/ directory)
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        upload_dir = os.path.join(base_dir, 'static', 'uploads', 'ui')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"login_logo_{name}_{int(time.time())}{ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        # Update database
        customization = UICustomization.query.filter_by(page_name='__login__').first()
        if not customization:
            customization = UICustomization(page_name='__login__')
            db.session.add(customization)
        
        # Remove old logo file if exists
        current_config = customization.get_login_config() or {}
        # Ensure both keys exist in config
        if 'login_logo' not in current_config:
            current_config['login_logo'] = None
        if 'login_background' not in current_config:
            current_config['login_background'] = None

        old_logo = current_config.get('login_logo')
        if old_logo:
            old_path = os.path.join(upload_dir, old_logo)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Update config
        current_config['login_logo'] = filename
        customization.set_login_config(current_config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/ui/{filename}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in upload_login_logo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/upload-login-background', methods=['POST'])
@login_required
def upload_login_background():
    """Handle AJAX login background upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        if '.' in file.filename:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
        else:
            file_ext = ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': 'Invalid file type. Only PNG and JPG allowed.'
            })
        
        # Check file size (5MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({
                'success': False, 
                'error': 'File too large. Maximum size is 5MB.'
            })
        
        # Create uploads directory structure (flat ui/ directory)
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        upload_dir = os.path.join(base_dir, 'static', 'uploads', 'ui')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"login_bg_{name}_{int(time.time())}{ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        # Update database
        customization = UICustomization.query.filter_by(page_name='__login__').first()
        if not customization:
            customization = UICustomization(page_name='__login__')
            db.session.add(customization)
        
        # Remove old background file if exists
        current_config = customization.get_login_config() or {}
        # Ensure both keys exist in config
        if 'login_logo' not in current_config:
            current_config['login_logo'] = None
        if 'login_background' not in current_config:
            current_config['login_background'] = None

        old_bg = current_config.get('login_background')
        if old_bg:
            old_path = os.path.join(upload_dir, old_bg)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Update config
        current_config['login_background'] = filename
        customization.set_login_config(current_config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/ui/{filename}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in upload_login_background: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/remove-login-logo', methods=['POST'])
@login_required
def remove_login_logo():
    """Remove login logo"""
    try:
        customization = UICustomization.query.filter_by(page_name='__login__').first()
        if customization:
            login_config = customization.get_login_config() or {}
            if 'login_logo' not in login_config:
                login_config['login_logo'] = None
            if 'login_background' not in login_config:
                login_config['login_background'] = None
            old_logo = login_config.get('login_logo')

            if old_logo:
                # Remove file
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                file_path = os.path.join(
                    base_dir, 'static', 'uploads', 'ui', old_logo
                )
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Update config: keep key with null always
            login_config['login_logo'] = None
            customization.set_login_config(login_config)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/remove-login-background', methods=['POST'])
@login_required
def remove_login_background():
    """Remove login background"""
    try:
        customization = UICustomization.query.filter_by(page_name='__login__').first()
        if customization:
            login_config = customization.get_login_config() or {}
            if 'login_logo' not in login_config:
                login_config['login_logo'] = None
            if 'login_background' not in login_config:
                login_config['login_background'] = None
            old_bg = login_config.get('login_background')

            if old_bg:
                # Remove file
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                file_path = os.path.join(
                    base_dir, 'static', 'uploads', 'ui', old_bg
                )
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Update config: keep key with null always
            login_config['login_background'] = None
            customization.set_login_config(login_config)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})