from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    controllers = db.relationship('Controller', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_2fa_secret(self):
        self.two_factor_secret = pyotp.random_base32()
        return self.two_factor_secret
    
    def get_2fa_uri(self):
        if self.two_factor_secret:
            return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
                name=self.email,
                issuer_name="LXCloud"
            )
        return None
    
    def verify_2fa_token(self, token):
        if self.two_factor_secret:
            totp = pyotp.TOTP(self.two_factor_secret)
            return totp.verify(token)
        return False

class Controller(db.Model):
    __tablename__ = 'controllers'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    controller_type = db.Column(db.String(50), nullable=False)  # speedradar, beaufortmeter, weatherstation, aicamera
    name = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    data_points = db.relationship('ControllerData', backref='controller', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        from app.utils import utc_to_local
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'controller_type': self.controller_type,
            'name': self.name or self.serial_number,
            'user_id': self.user_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_seen_local': utc_to_local(self.last_seen).isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat()
        }

class ControllerData(db.Model):
    __tablename__ = 'controller_data'
    
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('controllers.id'), nullable=False)
    data = db.Column(db.Text, nullable=False)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_data_dict(self):
        try:
            return json.loads(self.data)
        except:
            return {}
    
    def set_data_dict(self, data_dict):
        self.data = json.dumps(data_dict)

class UICustomization(db.Model):
    __tablename__ = 'ui_customization'
    
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(100), nullable=False)  # dashboard, login, etc.
    custom_css = db.Column(db.Text, nullable=True)
    header_config = db.Column(db.Text, nullable=True)  # JSON
    footer_config = db.Column(db.Text, nullable=True)  # JSON
    logo_filename = db.Column(db.String(255), nullable=True)  # Store uploaded logo filename
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_header_config(self):
        try:
            return json.loads(self.header_config) if self.header_config else {}
        except:
            return {}
    
    def set_header_config(self, config_dict):
        self.header_config = json.dumps(config_dict)
    
    def get_footer_config(self):
        try:
            return json.loads(self.footer_config) if self.footer_config else {}
        except:
            return {}
    
    def set_footer_config(self, config_dict):
        self.footer_config = json.dumps(config_dict)

class Addon(db.Model):
    __tablename__ = 'addons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    controller_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    config = db.Column(db.Text, nullable=True)  # JSON configuration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_config(self):
        try:
            return json.loads(self.config) if self.config else {}
        except:
            return {}
    
    def set_config(self, config_dict):
        self.config = json.dumps(config_dict)