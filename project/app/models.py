from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

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
    controllers = db.relationship(
        "Controller", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Hash and store a plaintext password for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the provided plaintext password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def generate_2fa_secret(self):
        """Generate and store a new 2FA secret for the user.

        Returns the base32 secret string.
        """
        self.two_factor_secret = pyotp.random_base32()
        return self.two_factor_secret

    def get_2fa_uri(self):
        """Return an otpauth provisioning URI for use with authenticator apps.

        Returns None when no 2FA secret is set.
        """
        if self.two_factor_secret:
            return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
                name=self.email, issuer_name="LXCloud"
            )
        return None

    def verify_2fa_token(self, token):
        """Verify a 2FA token against the stored secret.

        Returns True if token is valid, False otherwise.
        """
        if self.two_factor_secret:
            totp = pyotp.TOTP(self.two_factor_secret)
            return totp.verify(token)
        return False


class Controller(db.Model):
    __tablename__ = "controllers"

    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    controller_type = db.Column(db.String(50), nullable=False)

    # Known controller types: speedradar, beaufortmeter, weatherstation, aicamera
    name = db.Column(db.String(120), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    timeout_seconds = db.Column(
        db.Integer, nullable=True
    )  # Per-controller timeout in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    data_points = db.relationship(
        "ControllerData", backref="controller", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Serialize controller to a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "controller_type": self.controller_type,
            "name": self.name or self.serial_number,
            "user_id": self.user_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_online": self.is_online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
        }

    def is_stale(self, default_timeout_seconds=300):
        """Check if controller should be considered offline based on last_seen time

        Uses the controller's individual timeout_seconds if set, otherwise uses default_timeout_seconds
        """
        if not self.last_seen:
            return True

        from datetime import datetime, timedelta

        # Use controller's individual timeout if set, otherwise use the provided default
        timeout_to_use = (
            self.timeout_seconds
            if self.timeout_seconds is not None
            else default_timeout_seconds
        )
        cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_to_use)
        return self.last_seen < cutoff_time

    def update_status(self):
        """Mark controller as online and set `last_seen` to current UTC time."""
        from datetime import datetime

        self.is_online = True
        self.last_seen = datetime.utcnow()


class ControllerData(db.Model):
    __tablename__ = "controller_data"

    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(
        db.Integer, db.ForeignKey("controllers.id"), nullable=False
    )
    data = db.Column(db.Text, nullable=False)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_data_dict(self):
        """Return the JSON-parsed payload stored in `data` or an empty dict.

        This method always returns a dictionary to simplify callers.
        """
        try:
            return json.loads(self.data)
        except Exception:
            return {}

    def set_data_dict(self, data_dict):
        """Serialize and store a dictionary in the `data` column."""
        self.data = json.dumps(data_dict)


class UICustomization(db.Model):
    __tablename__ = "ui_customization"

    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(100), nullable=False)  # dashboard, login, etc.
    custom_css = db.Column(db.Text, nullable=True)
    header_config = db.Column(db.Text, nullable=True)  # JSON
    footer_config = db.Column(db.Text, nullable=True)  # JSON
    marker_config = db.Column(db.Text, nullable=True)  # JSON for marker configurations
    map_config = db.Column(db.Text, nullable=True)
    # JSON for OpenStreetMap / map settings
    logo_filename = db.Column(
        db.String(255), nullable=True
    )  # Store uploaded logo filename
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_header_config(self):
        """Return header configuration as a dict, or an empty dict on error."""
        try:
            return json.loads(self.header_config) if self.header_config else {}
        except Exception:
            return {}

    def set_header_config(self, config_dict):
        """Serialize and store header configuration as JSON."""
        self.header_config = json.dumps(config_dict)

    def get_footer_config(self):
        """Return footer configuration as a dict, or an empty dict on error."""
        try:
            return json.loads(self.footer_config) if self.footer_config else {}
        except Exception:
            return {}

    def set_footer_config(self, config_dict):
        """Serialize and store footer configuration as JSON."""
        self.footer_config = json.dumps(config_dict)

    def get_marker_config(self):
        """Return marker configuration as a dict, or an empty dict on error."""
        try:
            return json.loads(self.marker_config) if self.marker_config else {}
        except Exception:
            return {}

    def set_marker_config(self, config_dict):
        """Serialize and store marker configuration as JSON."""
        self.marker_config = json.dumps(config_dict)

    def get_map_config(self):
        """Return map (OpenStreetMap) configuration as a dict, or an empty dict on error."""
        try:
            return json.loads(self.map_config) if self.map_config else {}
        except Exception:
            return {}

    def set_map_config(self, config_dict):
        """Serialize and store map configuration as JSON."""
        self.map_config = json.dumps(config_dict)

    def get_custom_css(self, page_name=None):
        """Return custom CSS for a specific page or default."""
        return self.custom_css if self.custom_css else ""

    def set_custom_css(self, css_content):
        """Store custom CSS content."""
        self.custom_css = css_content


class Addon(db.Model):
    __tablename__ = "addons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    controller_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    config = db.Column(db.Text, nullable=True)  # JSON configuration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_config(self):
        """Return addon config as a dict, or an empty dict on error."""
        try:
            return json.loads(self.config) if self.config else {}
        except Exception:
            return {}

    def set_config(self, config_dict):
        """Serialize and store addon configuration as JSON."""
        self.config = json.dumps(config_dict)
