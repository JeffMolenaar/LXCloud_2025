#!/usr/bin/env python3
"""
LXCloud - Cloud Dashboard Platform
Main application entry point
"""

import os
import sys
from flask import Flask

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.mqtt_service import mqtt_service
from app.controller_status_service import controller_status_service

# Create Flask application instance
app = create_app()

def init_mqtt():
    """Initialize MQTT service with error handling"""
    try:
        mqtt_service.init_app(app)
        mqtt_service.start()
        print("MQTT service initialization completed")
    except Exception as e:
        print(f"MQTT service initialization failed: {e}")
        print("Application will continue without MQTT functionality")

def init_controller_status_service():
    """Initialize controller status service with error handling"""
    try:
        controller_status_service.init_app(app)
        success = controller_status_service.start()
        if success:
            print("✅ Controller status service initialization completed")
        else:
            print("❌ Controller status service failed to start properly")
            print("⚠️ Controllers may not be automatically marked offline!")
            print("💡 Tip: Check the logs and restart the application if needed")
        return success
    except Exception as e:
        print(f"❌ Controller status service initialization failed: {e}")
        print("⚠️ Application will continue without automatic status management")
        print("🔧 This means controllers will not be automatically marked offline when they stop reporting")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function for development server"""
    # Initialize MQTT service
    init_mqtt()
    
    # Initialize controller status service
    init_controller_status_service()
    
    # Get configuration
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"Starting LXCloud on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

# For production WSGI servers (Gunicorn)
if __name__ != '__main__':
    # Initialize MQTT service for production
    init_mqtt()
    # Initialize controller status service for production
    init_controller_status_service()

if __name__ == '__main__':
    main()