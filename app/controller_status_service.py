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
        if not self.app:
            print("ERROR: Controller status service cannot start - Flask app not initialized")
            return False
            
        if not self.enabled:
            print("Controller status service is disabled")
            return False
            
        try:
            # Check if thread is already running
            if self.status_thread and self.status_thread.is_alive():
                print("Controller status service is already running")
                return True
                
            self.stop_event.clear()
            self.status_thread = threading.Thread(target=self._run_status_checker, name="ControllerStatusService")
            self.status_thread.daemon = True
            self.status_thread.start()
            
            # Wait a bit to ensure thread started successfully
            import time
            time.sleep(0.1)
            
            if self.status_thread.is_alive():
                print(f"✅ Controller status service started successfully (check interval: {Config.CONTROLLER_STATUS_CHECK_INTERVAL}s, timeout: {Config.CONTROLLER_OFFLINE_TIMEOUT}s)")
                return True
            else:
                print("❌ ERROR: Controller status service thread failed to start")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Failed to start controller status service: {e}")
            import traceback
            traceback.print_exc()
            return False
            
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
        print("Controller status service background thread started")
        
        while self.enabled and not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    self._check_controller_status()
            except Exception as e:
                print(f"❌ Error in controller status checker: {e}")
                import traceback
                traceback.print_exc()
                
            # Wait for the configured interval or until stop event is set
            if not self.stop_event.wait(Config.CONTROLLER_STATUS_CHECK_INTERVAL):
                # Timeout occurred (normal case)
                pass
            else:
                # Stop event was set
                break
                
        print("Controller status service background thread stopped")
    
    def _check_controller_status(self):
        """Check all controllers and update their online/offline status"""
        try:
            # Find controllers that should be marked offline
            # (currently online but are stale according to their individual or global timeout)
            online_controllers = Controller.query.filter(
                Controller.is_online == True
            ).all()
            
            if not online_controllers:
                # No online controllers to check
                return
            
            # Filter for actually stale controllers and mark them offline
            controllers_updated = 0
            from datetime import datetime
            current_time = datetime.utcnow()
            
            for controller in online_controllers:
                # Use the controller's individual timeout, or fall back to global default
                if controller.is_stale(Config.CONTROLLER_OFFLINE_TIMEOUT):
                    controller.is_online = False
                    controllers_updated += 1
                    timeout_used = controller.timeout_seconds if controller.timeout_seconds is not None else Config.CONTROLLER_OFFLINE_TIMEOUT
                    
                    if controller.last_seen:
                        time_since = (current_time - controller.last_seen).total_seconds()
                        print(f"🔄 Controller {controller.serial_number} marked offline (last seen: {controller.last_seen}, {int(time_since)}s ago, timeout: {timeout_used}s)")
                    else:
                        print(f"🔄 Controller {controller.serial_number} marked offline (never seen, timeout: {timeout_used}s)")
            
            if controllers_updated > 0:
                db.session.commit()
                print(f"✅ Updated {controllers_updated} controller(s) to offline status")
            else:
                # Occasionally log that service is running (every 10 checks = ~10 minutes by default)
                if not hasattr(self, '_check_counter'):
                    self._check_counter = 0
                self._check_counter += 1
                if self._check_counter % 10 == 0:
                    print(f"🔄 Controller status service running - checked {len(online_controllers)} online controller(s), no changes needed")
                
        except Exception as e:
            print(f"❌ Error checking controller status: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass
    
    def force_check(self):
        """Force an immediate status check (useful for testing)"""
        if self.app:
            with self.app.app_context():
                self._check_controller_status()


# Global controller status service instance
controller_status_service = ControllerStatusService()