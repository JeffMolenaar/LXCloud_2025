#!/usr/bin/env python3
"""
Manual controller status fix script
Use this to manually check and fix controller status when the background service isn't working
"""
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config

def manual_status_fix():
    """Manually run controller status check and fix stuck controllers"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Manual Controller Status Fix")
        print("=" * 40)
        
        # Check how many controllers are currently online
        online_count = Controller.query.filter(Controller.is_online == True).count()
        total_count = Controller.query.count()
        
        print(f"Controllers in database: {total_count}")
        print(f"Currently marked online: {online_count}")
        
        if online_count == 0:
            print("✅ No controllers are marked online - nothing to check")
            return
        
        print(f"\n🔍 Checking {online_count} online controller(s)...")
        
        # Initialize the service (but don't start the background thread)
        controller_status_service.init_app(app)
        
        # Force a status check
        controller_status_service.force_check()
        
        # Check results
        new_online_count = Controller.query.filter(Controller.is_online == True).count()
        fixed_count = online_count - new_online_count
        
        print(f"\n📊 Results:")
        print(f"Controllers now online: {new_online_count}")
        print(f"Controllers fixed (marked offline): {fixed_count}")
        
        if fixed_count > 0:
            print(f"✅ Successfully fixed {fixed_count} controller(s) that were stuck online")
        else:
            print("ℹ️ No controllers needed status fixes")
        
        # Show current status of all controllers
        print(f"\n📋 Current controller status:")
        controllers = Controller.query.all()
        if controllers:
            for controller in controllers:
                status = "🟢 ONLINE" if controller.is_online else "🔴 OFFLINE"
                timeout = controller.timeout_seconds if controller.timeout_seconds is not None else Config.CONTROLLER_OFFLINE_TIMEOUT
                
                if controller.last_seen:
                    time_since = (datetime.utcnow() - controller.last_seen).total_seconds()
                    print(f"  {status} {controller.serial_number} (last seen {int(time_since)}s ago, timeout: {timeout}s)")
                else:
                    print(f"  {status} {controller.serial_number} (never seen, timeout: {timeout}s)")
        else:
            print("  No controllers registered")

if __name__ == '__main__':
    try:
        manual_status_fix()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)