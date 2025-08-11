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

def main():
    """Main function for development server"""
    # Initialize MQTT service
    init_mqtt()
    
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

if __name__ == '__main__':
    main()