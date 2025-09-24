from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, User

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.email = request.form['email']
        current_user.address = request.form['address']
        
        # Change password if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Password updated successfully', 'success')
            else:
                flash('Current password is incorrect', 'error')
                return render_template('users/profile.html')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
    
    return render_template('users/profile.html')

@users_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form['password']
    
    if not current_user.check_password(password):
        flash('Password is incorrect', 'error')
        return redirect(url_for('users.profile'))
    
    # Unbind all controllers
    for controller in current_user.controllers:
        controller.user_id = None
    
    # Delete user
    db.session.delete(current_user)
    db.session.commit()
    
    flash('Your account has been deleted', 'info')
    return redirect(url_for('auth.login'))