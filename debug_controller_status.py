#!/usr/bin/env python3
"""
Debug script for controller status issues in production
This script helps diagnose why controllers might be stuck in "online" status
"""
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config

def analyze_controller_status():
    """Analyze current controller status and identify issues"""
    app = create_app()
    
    with app.app_context():
        print("=== Controller Status Analysis ===")
        print(f"Configuration:")
        print(f"  Global timeout: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds ({Config.CONTROLLER_OFFLINE_TIMEOUT/60:.1f} minutes)")
        print(f"  Check interval: {Config.CONTROLLER_STATUS_CHECK_INTERVAL} seconds")
        print()
        
        # Get all controllers
        controllers = Controller.query.all()
        
        if not controllers:
            print("No controllers found in the database.")
            return
        
        print(f"Found {len(controllers)} controller(s):")
        print()
        
        current_time = datetime.utcnow()
        issue_controllers = []
        
        for controller in controllers:
            timeout_to_use = controller.timeout_seconds if controller.timeout_seconds is not None else Config.CONTROLLER_OFFLINE_TIMEOUT
            
            # Calculate how long since last seen
            if controller.last_seen:
                time_since_last_seen = current_time - controller.last_seen
                time_since_seconds = int(time_since_last_seen.total_seconds())
                
                # Check if should be offline
                should_be_offline = time_since_seconds > timeout_to_use
                has_issue = controller.is_online and should_be_offline
                
                if has_issue:
                    issue_controllers.append(controller)
                
                status_indicator = "⚠️ " if has_issue else "✅" if controller.is_online else "❌"
                
                print(f"{status_indicator} {controller.serial_number} ({controller.controller_type})")
                print(f"    Name: {controller.name or 'N/A'}")
                print(f"    Status: {'ONLINE' if controller.is_online else 'OFFLINE'}")
                print(f"    Last seen: {controller.last_seen} ({time_since_seconds}s ago)")
                print(f"    Timeout: {timeout_to_use}s ({timeout_to_use/60:.1f}m)")
                print(f"    Should be offline: {'YES' if should_be_offline else 'NO'}")
                
                if has_issue:
                    print(f"    🐛 ISSUE: Controller shows ONLINE but hasn't been seen for {time_since_seconds}s (>{timeout_to_use}s)")
                
                print()
            else:
                print(f"❌ {controller.serial_number} ({controller.controller_type})")
                print(f"    Name: {controller.name or 'N/A'}")
                print(f"    Status: {'ONLINE' if controller.is_online else 'OFFLINE'}")
                print(f"    Last seen: NEVER")
                print(f"    Timeout: {timeout_to_use}s ({timeout_to_use/60:.1f}m)")
                print(f"    🐛 ISSUE: Controller has never reported but shows as {'ONLINE' if controller.is_online else 'OFFLINE'}")
                print()
                
                if controller.is_online:
                    issue_controllers.append(controller)
        
        print(f"=== Summary ===")
        print(f"Total controllers: {len(controllers)}")
        print(f"Controllers with status issues: {len(issue_controllers)}")
        
        if issue_controllers:
            print("\n⚠️ IDENTIFIED ISSUES:")
            for controller in issue_controllers:
                if controller.last_seen:
                    time_since_seconds = int((current_time - controller.last_seen).total_seconds())
                    timeout_to_use = controller.timeout_seconds if controller.timeout_seconds is not None else Config.CONTROLLER_OFFLINE_TIMEOUT
                    print(f"  - {controller.serial_number}: Online but not seen for {time_since_seconds}s (timeout: {timeout_to_use}s)")
                else:
                    print(f"  - {controller.serial_number}: Online but never seen")
        
        return len(issue_controllers)

def test_controller_status_service():
    """Test if the controller status service is working"""
    app = create_app()
    
    print("\n=== Controller Status Service Test ===")
    
    with app.app_context():
        # Initialize service
        controller_status_service.init_app(app)
        
        # Get service status
        status = controller_status_service.get_status()
        print(f"Service enabled: {status['enabled']}")
        print(f"Service running: {status['running']}")
        print(f"Check interval: {status['check_interval']}s")
        print(f"Offline timeout: {status['offline_timeout']}s")
        
        if not status['enabled']:
            print("⚠️ WARNING: Controller status service is DISABLED")
            return False
        
        if not status['running']:
            print("⚠️ WARNING: Controller status service is NOT RUNNING")
            print("This means controllers will not be automatically marked offline!")
            return False
        
        print("\n🔧 Testing service functionality...")
        
        # Count issues before
        issues_before = analyze_controller_status()
        
        if issues_before > 0:
            print(f"\n🔧 Running manual status check to fix {issues_before} issue(s)...")
            controller_status_service.force_check()
            
            print("\n🔧 Re-analyzing after manual check...")
            issues_after = analyze_controller_status()
            
            if issues_after == 0:
                print("✅ Manual status check FIXED all issues!")
                print("This means the service logic works, but may not be running automatically in production.")
                return True
            elif issues_after < issues_before:
                print(f"⚠️ Manual status check PARTIALLY fixed issues ({issues_before} -> {issues_after})")
                return False
            else:
                print(f"❌ Manual status check did NOT fix issues")
                return False
        else:
            print("✅ No status issues found - service appears to be working correctly")
            return True

def provide_production_fix_recommendations():
    """Provide recommendations for fixing the issue in production"""
    print("\n=== Production Fix Recommendations ===")
    
    print("If controllers are stuck in 'online' status in production, try these fixes:")
    print()
    
    print("1. 🔄 IMMEDIATE FIX - Restart the application:")
    print("   sudo systemctl restart lxcloud")
    print("   # or however your service is named")
    print()
    
    print("2. 🔍 CHECK if the status service is running:")
    print("   # Look for these log messages during startup:")
    print("   journalctl -u lxcloud -f | grep -i 'controller status'")
    print("   # Should see: 'Controller status service started'")
    print()
    
    print("3. 🐛 MANUAL STATUS CHECK (temporary fix):")
    print("   # Create a script to manually run status checks:")
    print("   cat > /tmp/fix_controller_status.py << 'EOF'")
    print("#!/usr/bin/env python3")
    print("import sys, os")
    print("sys.path.insert(0, '/opt/LXCloud')  # Adjust path as needed")
    print("from app import create_app")
    print("from app.controller_status_service import controller_status_service")
    print("app = create_app()")
    print("with app.app_context():")
    print("    controller_status_service.init_app(app)")
    print("    controller_status_service.force_check()")
    print("    print('Status check completed')")
    print("EOF")
    print("   python3 /tmp/fix_controller_status.py")
    print()
    
    print("4. 🔧 PERMANENT FIX - Add to cron for safety:")
    print("   # Add this line to crontab to run every 5 minutes:")
    print("   */5 * * * * cd /opt/LXCloud && python3 /tmp/fix_controller_status.py")
    print()
    
    print("5. 🔍 DEBUGGING - Check logs for errors:")
    print("   journalctl -u lxcloud | grep -i error")
    print("   journalctl -u lxcloud | grep -i 'controller status'")

def main():
    """Main function"""
    print("🔍 LXCloud Controller Status Diagnostic Tool")
    print("=" * 50)
    
    try:
        # Analyze current status
        issues_count = analyze_controller_status()
        
        # Test service functionality
        service_working = test_controller_status_service()
        
        # Provide recommendations
        if issues_count > 0 or not service_working:
            provide_production_fix_recommendations()
        
        print("\n=== Diagnostic Complete ===")
        if issues_count == 0 and service_working:
            print("✅ No issues detected - controller status system is working correctly")
        else:
            print(f"⚠️ Detected {issues_count} controller status issue(s)")
            if not service_working:
                print("⚠️ Controller status service is not working properly")
            print("See recommendations above for fixes.")
        
    except Exception as e:
        print(f"❌ Error during diagnostic: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()