#!/usr/bin/env python3
"""
Test script for per-controller timeout functionality
"""
import sys
import os
import time
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config

def test_per_controller_timeout():
    """Test that controllers can have individual timeout settings"""
    app = create_app()
    
    with app.app_context():
        # Clean up any existing test controllers
        Controller.query.filter(Controller.serial_number.like('TEST_TIMEOUT_%')).delete()
        db.session.commit()
        
        # Create test controller with custom timeout (60 seconds)
        test_controller_custom = Controller(
            serial_number='TEST_TIMEOUT_CUSTOM',
            controller_type='speedradar',
            name='Test Custom Timeout Controller',
            is_online=True,
            timeout_seconds=60,  # Custom 60-second timeout
            last_seen=datetime.utcnow() - timedelta(seconds=90)  # 90 seconds ago (should be offline)
        )
        
        # Create test controller with default timeout
        test_controller_default = Controller(
            serial_number='TEST_TIMEOUT_DEFAULT',
            controller_type='speedradar',
            name='Test Default Timeout Controller',
            is_online=True,
            timeout_seconds=None,  # Use default timeout (300 seconds)
            last_seen=datetime.utcnow() - timedelta(seconds=90)  # 90 seconds ago (should still be online)
        )
        
        db.session.add(test_controller_custom)
        db.session.add(test_controller_default)
        db.session.commit()
        
        print(f"Created test controllers:")
        print(f"  Custom timeout (60s): {test_controller_custom.serial_number}")
        print(f"    Last seen: {test_controller_custom.last_seen}")
        print(f"    Is online: {test_controller_custom.is_online}")
        print(f"    Timeout: {test_controller_custom.timeout_seconds}s")
        print(f"    Should be stale: {test_controller_custom.is_stale(Config.CONTROLLER_OFFLINE_TIMEOUT)}")
        
        print(f"  Default timeout (300s): {test_controller_default.serial_number}")
        print(f"    Last seen: {test_controller_default.last_seen}")
        print(f"    Is online: {test_controller_default.is_online}")
        print(f"    Timeout: {test_controller_default.timeout_seconds}")
        print(f"    Should be stale: {test_controller_default.is_stale(Config.CONTROLLER_OFFLINE_TIMEOUT)}")
        
        # Initialize and force a status check
        controller_status_service.init_app(app)
        print("\nRunning status check...")
        controller_status_service.force_check()
        
        # Refresh from database by re-querying
        db.session.refresh(test_controller_custom)
        db.session.refresh(test_controller_default)
        
        print(f"\nAfter status check:")
        print(f"  Custom timeout controller is online: {test_controller_custom.is_online}")
        print(f"  Default timeout controller is online: {test_controller_default.is_online}")
        
        # Verify results
        assert not test_controller_custom.is_online, "Controller with custom 60s timeout should be offline after 90s"
        assert test_controller_default.is_online, "Controller with default 300s timeout should still be online after 90s"
        
        print("\n✅ Per-controller timeout functionality works correctly!")
        
        # Clean up
        Controller.query.filter(Controller.serial_number.like('TEST_TIMEOUT_%')).delete()
        db.session.commit()

def test_api_register_with_timeout():
    """Test registering a controller with custom timeout via API"""
    import json
    app = create_app()
    
    with app.test_client() as client:
        # Test data
        controller_data = {
            'serial_number': 'TEST_API_TIMEOUT_001',
            'type': 'speedradar',
            'name': 'Test API Timeout Controller',
            'latitude': 51.913071,
            'longitude': 5.713852,
            'timeout_seconds': 120
        }
        
        # Register controller
        response = client.post('/api/controllers/register', 
                             data=json.dumps(controller_data),
                             content_type='application/json')
        
        print(f"\nAPI Register Response Status: {response.status_code}")
        response_data = response.get_json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        assert 'controller' in response_data
        assert response_data['controller']['timeout_seconds'] == 120
        
        # Verify in database
        with app.app_context():
            controller = Controller.query.filter_by(serial_number='TEST_API_TIMEOUT_001').first()
            assert controller is not None
            assert controller.timeout_seconds == 120
            print(f"✅ Controller registered with timeout_seconds: {controller.timeout_seconds}")
            
            # Clean up
            db.session.delete(controller)
            db.session.commit()

def test_api_modify_timeout():
    """Test modifying controller timeout via API"""
    import json
    app = create_app()
    
    with app.app_context():
        # Create controller first
        controller = Controller(
            serial_number='TEST_API_MODIFY_001',
            controller_type='speedradar',
            name='Test API Modify Controller',
            timeout_seconds=300
        )
        controller.update_status()
        db.session.add(controller)
        db.session.commit()
        
        controller_id = controller.serial_number
    
    with app.test_client() as client:
        # Modify controller timeout
        modify_data = {
            'timeout_seconds': 180
        }
        
        response = client.put(f'/api/controllers/{controller_id}', 
                            data=json.dumps(modify_data),
                            content_type='application/json')
        
        print(f"\nAPI Modify Response Status: {response.status_code}")
        response_data = response.get_json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response_data['controller']['timeout_seconds'] == 180
        
        # Verify in database
        with app.app_context():
            controller = Controller.query.filter_by(serial_number='TEST_API_MODIFY_001').first()
            assert controller.timeout_seconds == 180
            print(f"✅ Controller timeout modified to: {controller.timeout_seconds}")
            
            # Clean up
            db.session.delete(controller)
            db.session.commit()

if __name__ == '__main__':
    print("Testing per-controller timeout functionality...")
    test_per_controller_timeout()
    test_api_register_with_timeout()
    test_api_modify_timeout()
    print("\n🎉 All per-controller timeout tests passed!")