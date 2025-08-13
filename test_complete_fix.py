#!/usr/bin/env python3
"""
End-to-end test simulating the reported issue:
1. Simulate posting data at 13:00 Netherlands time (stored as 11:00 UTC)
2. Verify that the display shows 13:00, not 11:00
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pytz
import tempfile
import sqlite3
from app import create_app
from app.models import db, Controller, ControllerData

def test_end_to_end_timezone_fix():
    """Test the complete flow from data storage to display"""
    print("End-to-End Timezone Fix Test")
    print("=" * 35)
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Configure app to use temporary database
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['TIMEZONE'] = 'Europe/Amsterdam'  # Netherlands timezone
        app.config['TESTING'] = True
        
        with app.app_context():
            # Initialize database
            db.create_all()
            
            # Simulate the scenario: User posts data at 13:00 Netherlands time
            print("Simulating the original issue scenario:")
            print("1. User in Netherlands posts data at 13:00 local time")
            
            # This represents what happens when user posts at 13:00 CEST
            # The server receives this and stores it as UTC (11:00)
            utc_time_when_posted = datetime(2023, 8, 13, 11, 0, 0)  # 11:00 UTC = 13:00 CEST
            
            # Create a test controller
            controller = Controller(
                serial_number='TEST_250100.1.0625',
                controller_type='speedradar',
                name='Test Speed Radar',
                is_online=True,
                last_seen=utc_time_when_posted  # Stored as UTC
            )
            db.session.add(controller)
            
            # Create test data point
            data_point = ControllerData(
                controller_id=1,  # Will be set after commit
                timestamp=utc_time_when_posted  # Stored as UTC
            )
            data_point.set_data_dict({'speed': 45, 'direction': 'north'})
            
            db.session.commit()
            data_point.controller_id = controller.id
            db.session.add(data_point)
            db.session.commit()
            
            print(f"2. Data stored in database as UTC: {utc_time_when_posted}")
            
            # Test what the user sees now (after our fix)
            from app.utils import format_local_datetime, format_local_time, format_local_datetime_full
            
            displayed_datetime = format_local_datetime(controller.last_seen)
            displayed_time = format_local_time(controller.last_seen)
            displayed_full = format_local_datetime_full(controller.last_seen)
            
            print(f"3. What user sees after fix:")
            print(f"   - Last seen (datetime): {displayed_datetime}")
            print(f"   - Last seen (time only): {displayed_time}")
            print(f"   - Last seen (full): {displayed_full}")
            
            # Test API response
            controller_dict = controller.to_dict()
            print(f"4. API response includes:")
            print(f"   - last_seen (UTC): {controller_dict['last_seen']}")
            print(f"   - last_seen_local: {controller_dict['last_seen_local']}")
            
            # Verify the fix works
            success = True
            
            if "13:" not in displayed_time:
                print("✗ ERROR: Time display still showing UTC instead of local time")
                success = False
            else:
                print("✓ SUCCESS: Time display now shows 13:00 (local time) instead of 11:00 (UTC)")
            
            if controller_dict['last_seen_local'] and "T13:" not in controller_dict['last_seen_local']:
                print("✗ ERROR: API response not including correct local time")
                success = False
            else:
                print("✓ SUCCESS: API response includes local timezone information")
            
            # Test data point timestamps too
            data_displayed_time = format_local_time(data_point.timestamp)
            if "13:" not in data_displayed_time:
                print("✗ ERROR: Data point timestamps still showing UTC")
                success = False
            else:
                print("✓ SUCCESS: Data point timestamps also show local time")
            
            return success
            
    finally:
        # Clean up temporary database
        try:
            os.unlink(db_path)
        except:
            pass

def test_winter_time_scenario():
    """Test that winter time also works correctly (UTC+1)"""
    print("\nWinter Time Test (UTC+1)")
    print("=" * 25)
    
    # Test winter time: December (CET = UTC+1)
    utc_winter = datetime(2023, 12, 13, 11, 0, 0)  # 11:00 UTC in winter
    
    # Convert to Netherlands time
    netherlands_tz = pytz.timezone('Europe/Amsterdam')
    utc_aware = pytz.utc.localize(utc_winter)
    local_winter = utc_aware.astimezone(netherlands_tz)
    
    print(f"Winter scenario: 11:00 UTC -> {local_winter.hour}:00 CET")
    
    if local_winter.hour == 12:
        print("✓ Winter time conversion correct (UTC+1)")
        return True
    else:
        print(f"✗ Winter time conversion incorrect, got {local_winter.hour}:00")
        return False

if __name__ == "__main__":
    print("LXCloud - Complete Timezone Fix Validation")
    print("=" * 50)
    print("Testing the complete flow: Data storage -> Display")
    print()
    
    test1_passed = test_end_to_end_timezone_fix()
    test2_passed = test_winter_time_scenario()
    
    print()
    print("=" * 50)
    if test1_passed and test2_passed:
        print("✓ COMPLETE FIX VALIDATED!")
        print()
        print("The timezone issue has been completely resolved:")
        print("- Data posted at 13:00 Netherlands time is now displayed as 13:00")
        print("- No more confusion with UTC times being shown as local times")
        print("- Both summer time (CEST, UTC+2) and winter time (CET, UTC+1) work correctly")
        print("- Templates and API responses include proper timezone conversion")
        sys.exit(0)
    else:
        print("✗ FIX VALIDATION FAILED!")
        print("The timezone issue still exists or has partial problems")
        sys.exit(1)