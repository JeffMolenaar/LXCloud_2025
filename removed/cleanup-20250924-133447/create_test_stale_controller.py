#!/usr/bin/env python3
"""
Create a test controller that appears to be stuck online (for testing)
"""
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller

def create_stale_controller():
    """Create a test controller that should appear offline but is marked online"""
    app = create_app()
    
    with app.app_context():
        # Clean up any existing test controller
        existing = Controller.query.filter_by(serial_number='TEST_STALE_001').first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # Create a controller that was last seen 1 day ago but is marked online
        stale_controller = Controller(
            serial_number='TEST_STALE_001',
            controller_type='speedradar',
            name='Test Stale Controller',
            is_online=True,  # This is the problem - it should be offline
            last_seen=datetime.utcnow() - timedelta(days=1),  # 1 day ago
            timeout_seconds=300  # 5 minute timeout
        )
        
        db.session.add(stale_controller)
        db.session.commit()
        
        print(f"✅ Created test stale controller:")
        print(f"   Serial: {stale_controller.serial_number}")
        print(f"   Status: {'ONLINE' if stale_controller.is_online else 'OFFLINE'}")
        print(f"   Last seen: {stale_controller.last_seen}")
        print(f"   Hours since last seen: {(datetime.utcnow() - stale_controller.last_seen).total_seconds() / 3600:.1f}")
        print(f"   Timeout: {stale_controller.timeout_seconds}s")
        print(f"\n🐛 This controller should appear OFFLINE but shows as ONLINE")
        print(f"💡 Use 'python fix_controller_status.py' to fix it")

if __name__ == '__main__':
    create_stale_controller()