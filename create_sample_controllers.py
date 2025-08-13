#!/usr/bin/env python3
"""
Script to create sample controllers for testing
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller, ControllerData, User
import json

def create_sample_controllers():
    """Create sample controllers for testing"""
    app = create_app()
    
    with app.app_context():
        # Sample controller data
        controllers_data = [
            {
                'serial_number': 'LX2025-001-SPEED',
                'controller_type': 'speedradar',
                'name': 'Highway Speed Monitor',
                'latitude': 52.3676,
                'longitude': 4.9041,
                'is_online': True
            },
            {
                'serial_number': 'LX2025-002-WIND',
                'controller_type': 'beaufortmeter',
                'name': 'Harbor Wind Sensor',
                'latitude': 52.3783,
                'longitude': 4.8967,
                'is_online': True
            },
            {
                'serial_number': 'LX2025-003-WEATHER',
                'controller_type': 'weatherstation',
                'name': 'Central Weather Station',
                'latitude': 52.3702,
                'longitude': 4.8952,
                'is_online': False
            },
            {
                'serial_number': 'LX2025-004-CAM',
                'controller_type': 'aicamera',
                'name': 'Traffic Camera AI',
                'latitude': 52.3625,
                'longitude': 4.8968,
                'is_online': True
            },
            {
                'serial_number': 'LX2025-005-UNBOUND',
                'controller_type': 'speedradar',
                'name': None,
                'latitude': None,
                'longitude': None,
                'is_online': False
            },
            {
                'serial_number': 'LX2025-006-TEMP',
                'controller_type': 'weatherstation',
                'name': 'Temperature Monitor',
                'latitude': 52.3600,
                'longitude': 4.9100,
                'is_online': True
            }
        ]
        
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Admin user not found!")
            return
        
        # Create controllers
        created_controllers = []
        for i, controller_data in enumerate(controllers_data):
            # Check if controller already exists
            existing = Controller.query.filter_by(serial_number=controller_data['serial_number']).first()
            if existing:
                print(f"Controller {controller_data['serial_number']} already exists")
                continue
            
            controller = Controller(
                serial_number=controller_data['serial_number'],
                controller_type=controller_data['controller_type'],
                name=controller_data['name'],
                latitude=controller_data['latitude'],
                longitude=controller_data['longitude'],
                is_online=controller_data['is_online'],
                last_seen=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)) if controller_data['is_online'] else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            # Bind some controllers to admin, leave some unbound
            if i not in [4]:  # Leave LX2025-005-UNBOUND unbound
                controller.user_id = admin_user.id
            
            db.session.add(controller)
            created_controllers.append(controller)
        
        # Commit controllers first
        db.session.commit()
        
        # Create sample data for online controllers
        for controller in created_controllers:
            if controller.is_online:
                create_sample_data(controller)
        
        db.session.commit()
        print(f"Created {len(created_controllers)} controllers with sample data")

def create_sample_data(controller):
    """Create sample sensor data for a controller"""
    
    # Generate data for the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    # Generate data points every 15 minutes
    current_time = start_time
    while current_time <= end_time:
        
        # Generate appropriate data based on controller type
        if controller.controller_type == 'speedradar':
            data = {
                'speed_kmh': random.randint(20, 120),
                'vehicle_count': random.randint(0, 50),
                'average_speed': random.randint(40, 80)
            }
        elif controller.controller_type == 'beaufortmeter':
            data = {
                'wind_speed_ms': round(random.uniform(0, 25), 2),
                'wind_direction': random.randint(0, 360),
                'beaufort_scale': random.randint(0, 12)
            }
        elif controller.controller_type == 'weatherstation':
            data = {
                'temperature_c': round(random.uniform(-10, 35), 1),
                'humidity_percent': random.randint(30, 90),
                'pressure_hpa': random.randint(980, 1030),
                'rainfall_mm': round(random.uniform(0, 5), 1)
            }
        elif controller.controller_type == 'aicamera':
            data = {
                'object_count': random.randint(0, 20),
                'vehicles_detected': random.randint(0, 15),
                'people_detected': random.randint(0, 8),
                'confidence_avg': round(random.uniform(0.7, 0.95), 2)
            }
        else:
            data = {
                'sensor_value': random.randint(0, 100),
                'status': 'active'
            }
        
        # Create data point
        data_point = ControllerData(
            controller_id=controller.id,
            data=json.dumps(data),
            timestamp=current_time
        )
        
        db.session.add(data_point)
        current_time += timedelta(minutes=15)

if __name__ == '__main__':
    create_sample_controllers()