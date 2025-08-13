import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
from app.models import db, Controller, ControllerData
from config.config import Config

class MQTTService:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.is_connected = False
        self.enabled = True
        self.retry_count = 0
        self.max_retries = 5
        self.retry_delay = 10
        self.connection_thread = None
        
    def init_app(self, app):
        self.app = app
        # Check if MQTT should be enabled
        self.enabled = getattr(Config, 'MQTT_ENABLED', True)
        if not self.enabled:
            print("MQTT service is disabled by configuration")
        
    def start(self):
        """Start the MQTT service in a separate thread"""
        if self.app and self.enabled:
            self.connection_thread = threading.Thread(target=self._run_mqtt_client)
            self.connection_thread.daemon = True
            self.connection_thread.start()
        elif not self.enabled:
            print("MQTT service is disabled - skipping connection")
            
    def stop(self):
        """Stop the MQTT service"""
        if self.client and self.is_connected:
            self.client.disconnect()
        self.enabled = False
    
    def get_status(self):
        """Get the current status of the MQTT service"""
        return {
            'enabled': self.enabled,
            'connected': self.is_connected,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
            
    def _run_mqtt_client(self):
        """Run the MQTT client with proper retry logic"""
        while self.enabled and self.retry_count < self.max_retries:
            try:
                with self.app.app_context():
                    self.client = mqtt.Client()
                    
                    # Set up callbacks
                    self.client.on_connect = self._on_connect
                    self.client.on_message = self._on_message
                    self.client.on_disconnect = self._on_disconnect
                    
                    # Set up authentication if configured
                    if Config.MQTT_USERNAME:
                        self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
                    
                    print(f"Attempting MQTT connection (attempt {self.retry_count + 1}/{self.max_retries})")
                    
                    # Connect to broker
                    self.client.connect(Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT, 60)
                    
                    # Reset retry count on successful connection attempt
                    self.retry_count = 0
                    
                    # Start the network loop
                    self.client.loop_forever()
                    
            except Exception as e:
                self.retry_count += 1
                print(f"MQTT connection error (attempt {self.retry_count}/{self.max_retries}): {e}")
                
                if self.retry_count >= self.max_retries:
                    print("Max MQTT retry attempts reached. MQTT service will be disabled.")
                    self.enabled = False
                    break
                
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONN_ACK response from the server"""
        if rc == 0:
            print("Connected to MQTT broker")
            self.is_connected = True
            
            # Subscribe to all controller topics
            topic = f"{Config.MQTT_TOPIC_PREFIX}/+/data"
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
            
            # Subscribe to controller status topics
            status_topic = f"{Config.MQTT_TOPIC_PREFIX}/+/status"
            client.subscribe(status_topic)
            print(f"Subscribed to topic: {status_topic}")
            
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")
            self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the server"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                prefix = topic_parts[0]
                serial_number = topic_parts[1].upper()
                message_type = topic_parts[2]
                
                if prefix == Config.MQTT_TOPIC_PREFIX:
                    if message_type == 'data':
                        self._handle_controller_data(serial_number, msg.payload.decode())
                    elif message_type == 'status':
                        self._handle_controller_status(serial_number, msg.payload.decode())
                        
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server"""
        print(f"Disconnected from MQTT broker, return code {rc}")
        self.is_connected = False
    
    def _handle_controller_data(self, serial_number, payload):
        """Handle incoming controller data"""
        try:
            data = json.loads(payload)
            
            # Extract controller information
            controller_type = data.get('type', 'unknown')
            controller_data = data.get('data', {})
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Find or create controller
            controller = Controller.query.filter_by(serial_number=serial_number).first()
            if not controller:
                controller = Controller(
                    serial_number=serial_number,
                    controller_type=controller_type,
                    name=serial_number
                )
                db.session.add(controller)
                print(f"New controller registered: {serial_number}")
            
            # Update controller info
            controller.controller_type = controller_type
            controller.update_status()
            
            # Update location if provided
            if latitude is not None and longitude is not None:
                controller.latitude = float(latitude)
                controller.longitude = float(longitude)
            
            # Store the data
            if controller_data:
                data_point = ControllerData(
                    controller_id=controller.id,
                    timestamp=datetime.utcnow()
                )
                data_point.set_data_dict(controller_data)
                db.session.add(data_point)
            
            db.session.commit()
            print(f"Data received from controller {serial_number}: {controller_data}")
            
        except json.JSONDecodeError:
            print(f"Invalid JSON from controller {serial_number}: {payload}")
        except Exception as e:
            print(f"Error handling controller data: {e}")
            db.session.rollback()
    
    def _handle_controller_status(self, serial_number, payload):
        """Handle controller status updates"""
        try:
            status_data = json.loads(payload)
            online = status_data.get('online', False)
            
            controller = Controller.query.filter_by(serial_number=serial_number).first()
            if controller:
                controller.is_online = online
                controller.last_seen = datetime.utcnow()
                db.session.commit()
                print(f"Controller {serial_number} status: {'online' if online else 'offline'}")
            
        except Exception as e:
            print(f"Error handling controller status: {e}")
            db.session.rollback()

# Global MQTT service instance
mqtt_service = MQTTService()