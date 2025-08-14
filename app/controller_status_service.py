"""
Controller Status Service

This service runs in the background to automatically manage controller online/offline status
based on when they last reported to the cloud platform.
"""

import threading
import time
from app.models import db, Controller
from config.config import Config


class ControllerStatusService:
    def __init__(self, app=None):
        self.app = app
        self.enabled = True
        self.status_thread = None
        self.stop_event = threading.Event()
        
    def init_app(self, app):
        """Initialize the service with Flask app"""
        self.app = app
        
    def start(self):
        """Start the background status checking service"""
        if self.app and self.enabled:
            self.status_thread = threading.Thread(target=self._run_status_checker)
            self.status_thread.daemon = True
            self.status_thread.start()
            print(f"Controller status service started (check interval: {Config.CONTROLLER_STATUS_CHECK_INTERVAL}s, timeout: {Config.CONTROLLER_OFFLINE_TIMEOUT}s)")
        else:
            print("Controller status service is disabled")
            
    def stop(self):
        """Stop the background service"""
        self.enabled = False
        self.stop_event.set()
        if self.status_thread and self.status_thread.is_alive():
            self.status_thread.join(timeout=5)
            
    def get_status(self):
        """Get the current status of the service"""
        return {
            'enabled': self.enabled,
            'running': self.status_thread and self.status_thread.is_alive(),
            'check_interval': Config.CONTROLLER_STATUS_CHECK_INTERVAL,
            'offline_timeout': Config.CONTROLLER_OFFLINE_TIMEOUT
        }
        
    def _run_status_checker(self):
        """Main loop for checking controller status"""
        while self.enabled and not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    self._check_controller_status()
            except Exception as e:
                print(f"Error in controller status checker: {e}")
                
            # Wait for the configured interval or until stop event is set
            self.stop_event.wait(Config.CONTROLLER_STATUS_CHECK_INTERVAL)
    
    def _check_controller_status(self):
        """Check all controllers and update their online/offline status"""
        try:
            # Find controllers that should be marked offline
            # (currently online but are stale according to their individual or global timeout)
            online_controllers = Controller.query.filter(
                Controller.is_online == True
            ).all()
            
            # Filter for actually stale controllers and mark them offline
            controllers_updated = 0
            for controller in online_controllers:
                # Use the controller's individual timeout, or fall back to global default
                if controller.is_stale(Config.CONTROLLER_OFFLINE_TIMEOUT):
                    controller.is_online = False
                    controllers_updated += 1
                    timeout_used = controller.timeout_seconds if controller.timeout_seconds is not None else Config.CONTROLLER_OFFLINE_TIMEOUT
                    print(f"Controller {controller.serial_number} marked offline (last seen: {controller.last_seen}, timeout: {timeout_used}s)")
            
            if controllers_updated > 0:
                db.session.commit()
                print(f"Updated {controllers_updated} controller(s) to offline status")
                
        except Exception as e:
            print(f"Error checking controller status: {e}")
            db.session.rollback()
    
    def force_check(self):
        """Force an immediate status check (useful for testing)"""
        if self.app:
            with self.app.app_context():
                self._check_controller_status()


# Global controller status service instance
controller_status_service = ControllerStatusService()