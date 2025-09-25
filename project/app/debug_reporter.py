"""
LXCloud Debug Reporter
Automatically captures and reports errors for remote debugging
"""
import os
import json
import traceback
import hashlib
import re
import logging
from datetime import datetime
from typing import Dict, Any
from flask import request


class DebugReporter:
    """Automated error capture and sanitization for remote debugging"""

    def __init__(self, app=None):
        self.app = app
        # Change to home directory instead of /tmp
        self.debug_queue_dir = "/home/lxcloud/debug_queue"
        self.logger = logging.getLogger('lxcloud.debug_reporter')

        # Ensure debug queue directory exists
        if not os.path.exists(self.debug_queue_dir):
            try:
                os.makedirs(self.debug_queue_dir, mode=0o755)
                msg = f"Created debug queue: {self.debug_queue_dir}"
                self.logger.info(msg)
            except OSError as e:
                self.logger.error(f"Failed to create debug queue: {e}")

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

        # Register error handlers
        @app.errorhandler(500)
        def handle_500(error):
            self.capture_500_error(error)
            return self.app.handle_http_exception(error)

        @app.errorhandler(Exception)
        def handle_exception(error):
            self.capture_exception(error)
            raise error

    def _sanitize_data(self, data: str) -> str:
        """Remove sensitive information from data"""
        if not data:
            return ""

        # Remove passwords, tokens, emails, IPs
        patterns = [
            (r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
             'password: [REDACTED]'),
            (r'secret["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
             'secret: [REDACTED]'),
            (r'token["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
             'token: [REDACTED]'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
             '[EMAIL]'),
            (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),
            (r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',
             'SECRET_KEY=[REDACTED]'),
        ]

        sanitized = data
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized,
                               flags=re.IGNORECASE)

        return sanitized

    def _hash_identifier(self, value: str) -> str:
        """Create hash of sensitive identifier for tracking"""
        if not value:
            return "none"
        return hashlib.md5(value.encode()).hexdigest()[:8]

    def _create_debug_report(self, error_type: str,
                             error_info: Dict[str, Any]) -> str:
        """Create sanitized debug report and save to queue"""
        timestamp = datetime.now().isoformat()

        # Get user agent hash for tracking
        user_agent = request.headers.get('User-Agent', '') if request else ''
        user_agent_hash = self._hash_identifier(user_agent)

        report = {
            'timestamp': timestamp,
            'error_type': error_type,
            'user_agent_hash': user_agent_hash,
            'stack_trace': self._sanitize_data(
                error_info.get('stack_trace', '')),
            'error_message': self._sanitize_data(
                error_info.get('error_message', '')),
            'request_info': error_info.get('request_info', {}),
            'system_info': self._get_system_info(),
        }

        # Create filename with timestamp and error type
        safe_timestamp = timestamp.replace(':', '-')
        filename = f"{safe_timestamp}_{error_type}_{user_agent_hash}.json"
        filepath = os.path.join(self.debug_queue_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Debug report saved: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save debug report: {e}")
            return ""

    def _get_request_info(self) -> Dict[str, Any]:
        """Get sanitized request information"""
        if not request:
            return {}

        try:
            return {
                'method': request.method,
                'path': request.path,
                'url': self._sanitize_data(request.url),
                'remote_addr': '[IP_REDACTED]',
                'user_agent_hash': self._hash_identifier(
                    request.headers.get('User-Agent', '')),
                'referrer': self._sanitize_data(
                    request.headers.get('Referer', '')),
                'form_keys': (list(request.form.keys())
                              if hasattr(request, 'form') else []),
                'args_keys': list(request.args.keys()),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get request info: {e}")
            return {'error': 'failed_to_capture'}

    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information"""
        return {
            'python_version': f"{os.sys.version_info.major}."
                              f"{os.sys.version_info.minor}",
            'platform': os.name,
        }

    def capture_500_error(self, error):
        """Capture 500 Internal Server Error"""
        try:
            error_info = {
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'request_info': self._get_request_info(),
            }
            filename = self._create_debug_report('500_error', error_info)
            if filename:
                self.logger.info(f"500 error captured: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to capture 500 error: {e}")

    def capture_exception(self, error):
        """Capture general exceptions"""
        try:
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'request_info': self._get_request_info(),
            }
            filename = self._create_debug_report('exception', error_info)
            if filename:
                self.logger.info(f"Exception captured: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to capture exception: {e}")

    def capture_template_error(self, template_name: str, error: str):
        """Capture template rendering errors"""
        try:
            error_info = {
                'template_name': template_name,
                'error_message': error,
                'request_info': self._get_request_info(),
            }
            filename = self._create_debug_report('template_error', error_info)
            if filename:
                self.logger.info(f"Template error captured: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to capture template error: {e}")


# Global instance
debug_reporter = DebugReporter()