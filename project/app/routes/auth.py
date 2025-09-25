from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import pyotp
import qrcode
import io
import base64

from app.models import db, User
from app.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        two_factor_token = request.form.get('two_factor_token', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.two_factor_enabled:
                if not two_factor_token:
                    # First step - password correct, need 2FA
                    session['2fa_user_id'] = user.id
                    return render_template('auth/login.html', needs_2fa=True)
                else:
                    # Second step - verify 2FA
                    if user.verify_2fa_token(two_factor_token):
                        user.last_login = datetime.utcnow()
                        db.session.commit()
                        login_user(user)
                        session.pop('2fa_user_id', None)
                        return redirect(url_for('dashboard.index'))
                    else:
                        flash('Invalid 2FA token', 'error')
            else:
                # No 2FA required
                user.last_login = datetime.utcnow()
                db.session.commit()
                login_user(user)
                return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user (force non-admin regardless of form input)
        full_name = f"{form.first_name.data} {form.last_name.data}"
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=full_name,
            address='',
            is_admin=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/setup-2fa')
@login_required
def setup_2fa():
    if current_user.two_factor_enabled:
        flash('2FA is already enabled', 'info')
        return redirect(url_for('users.profile'))
    
    # Generate secret
    secret = current_user.generate_2fa_secret()
    db.session.commit()
    
    # Generate QR code
    qr_uri = current_user.get_2fa_uri()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_code_data = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('auth/setup_2fa.html', 
                         qr_code=qr_code_data, 
                         secret=secret)

@auth_bp.route('/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    token = request.form['token']
    
    if current_user.verify_2fa_token(token):
        current_user.two_factor_enabled = True
        db.session.commit()
        flash('2FA has been enabled successfully!', 'success')
    else:
        flash('Invalid token. Please try again.', 'error')
    
    return redirect(url_for('users.profile'))

@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.session.commit()
    flash('2FA has been disabled', 'info')
    return redirect(url_for('users.profile'))