#!/usr/bin/env python3
"""
LXCloud MQTT Controller Simulator
Simulates controller data for testing purposes
"""

import json
import time
import random
import paho.mqtt.client as mqtt
from datetime import datetime
import argparse
import threading

class ControllerSimulator:
    def __init__(self, broker_host='localhost', broker_port=1883, topic_prefix='lxcloud'):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.client = mqtt.Client()
        self.running = False
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            print(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")
    
    def simulate_speedradar(self, serial_number, location=None):
        """Simulate speed radar controller"""
        while self.running:
            data = {
                'type': 'speedradar',
                'data': {
                    'speed_kmh': round(random.uniform(20, 120), 1),
                    'vehicle_count': random.randint(0, 5),
                    'average_speed': round(random.uniform(40, 80), 1),
                    'violations': random.randint(0, 2)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if location:
                data['latitude'] = location[0]
                data['longitude'] = location[1]
            
            topic = f"{self.topic_prefix}/{serial_number}/data"
            self.client.publish(topic, json.dumps(data))
            print(f"[{serial_number}] Published speed radar data")
            
            # Send status
            status_topic = f"{self.topic_prefix}/{serial_number}/status"
            status_data = {'online': True, 'timestamp': datetime.now().isoformat()}
            self.client.publish(status_topic, json.dumps(status_data))
            
            time.sleep(random.uniform(10, 30))  # Random interval
    
    def simulate_weatherstation(self, serial_number, location=None):
        """Simulate weather station controller"""
        while self.running:
            data = {
                'type': 'weatherstation',
                'data': {
                    'temperature_c': round(random.uniform(-10, 35), 1),
                    'humidity_percent': round(random.uniform(30, 90), 1),
                    'pressure_hpa': round(random.uniform(980, 1030), 1),
                    'wind_speed_kmh': round(random.uniform(0, 50), 1),
                    'wind_direction': random.randint(0, 359),
                    'rainfall_mm': round(random.uniform(0, 10), 2) if random.random() < 0.3 else 0
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if location:
                data['latitude'] = location[0]
                data['longitude'] = location[1]
            
            topic = f"{self.topic_prefix}/{serial_number}/data"
            self.client.publish(topic, json.dumps(data))
            print(f"[{serial_number}] Published weather station data")
            
            # Send status
            status_topic = f"{self.topic_prefix}/{serial_number}/status"
            status_data = {'online': True, 'timestamp': datetime.now().isoformat()}
            self.client.publish(status_topic, json.dumps(status_data))
            
            time.sleep(random.uniform(30, 60))  # Random interval
    
    def simulate_beaufortmeter(self, serial_number, location=None):
        """Simulate Beaufort meter controller"""
        while self.running:
            wind_speed = random.uniform(0, 40)
            beaufort_scale = min(12, int(wind_speed / 3.3))  # Approximate Beaufort scale
            
            data = {
                'type': 'beaufortmeter',
                'data': {
                    'wind_speed_kmh': round(wind_speed, 1),
                    'beaufort_scale': beaufort_scale,
                    'wind_direction': random.randint(0, 359),
                    'gust_speed_kmh': round(wind_speed * random.uniform(1.2, 1.8), 1),
                    'air_density': round(random.uniform(1.15, 1.35), 3)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if location:
                data['latitude'] = location[0]
                data['longitude'] = location[1]
            
            topic = f"{self.topic_prefix}/{serial_number}/data"
            self.client.publish(topic, json.dumps(data))
            print(f"[{serial_number}] Published Beaufort meter data")
            
            # Send status
            status_topic = f"{self.topic_prefix}/{serial_number}/status"
            status_data = {'online': True, 'timestamp': datetime.now().isoformat()}
            self.client.publish(status_topic, json.dumps(status_data))
            
            time.sleep(random.uniform(15, 45))  # Random interval
    
    def simulate_aicamera(self, serial_number, location=None):
        """Simulate AI camera controller"""
        while self.running:
            data = {
                'type': 'aicamera',
                'data': {
                    'people_count': random.randint(0, 20),
                    'vehicle_count': random.randint(0, 10),
                    'motion_detected': random.choice([True, False]),
                    'light_level': random.randint(0, 100),
                    'recording': random.choice([True, False]),
                    'storage_used_percent': round(random.uniform(20, 85), 1),
                    'alerts': random.randint(0, 3)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if location:
                data['latitude'] = location[0]
                data['longitude'] = location[1]
            
            topic = f"{self.topic_prefix}/{serial_number}/data"
            self.client.publish(topic, json.dumps(data))
            print(f"[{serial_number}] Published AI camera data")
            
            # Send status
            status_topic = f"{self.topic_prefix}/{serial_number}/status"
            status_data = {'online': True, 'timestamp': datetime.now().isoformat()}
            self.client.publish(status_topic, json.dumps(status_data))
            
            time.sleep(random.uniform(20, 60))  # Random interval

def main():
    parser = argparse.ArgumentParser(description='LXCloud Controller Simulator')
    parser.add_argument('--broker', default='localhost', help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic-prefix', default='lxcloud', help='MQTT topic prefix')
    
    args = parser.parse_args()
    
    simulator = ControllerSimulator(args.broker, args.port, args.topic_prefix)
    
    if not simulator.connect():
        return
    
    simulator.running = True
    
    # Start simulating different controller types
    controllers = [
        ('SR001', 'speedradar', (52.3676, 4.9041)),      # Amsterdam
        ('WS001', 'weatherstation', (52.3702, 4.8952)),  # Amsterdam Central
        ('BF001', 'beaufortmeter', (52.3738, 4.8910)),   # Amsterdam North
        ('AI001', 'aicamera', (52.3667, 4.8945)),        # Dam Square
        ('SR002', 'speedradar', (52.3667, 4.9036)),      # Vondelpark
    ]
    
    threads = []
    
    try:
        for serial, controller_type, location in controllers:
            if controller_type == 'speedradar':
                thread = threading.Thread(target=simulator.simulate_speedradar, 
                                        args=(serial, location))
            elif controller_type == 'weatherstation':
                thread = threading.Thread(target=simulator.simulate_weatherstation, 
                                        args=(serial, location))
            elif controller_type == 'beaufortmeter':
                thread = threading.Thread(target=simulator.simulate_beaufortmeter, 
                                        args=(serial, location))
            elif controller_type == 'aicamera':
                thread = threading.Thread(target=simulator.simulate_aicamera, 
                                        args=(serial, location))
            
            thread.daemon = True
            thread.start()
            threads.append(thread)
            print(f"Started simulator for {controller_type} {serial}")
        
        print(f"\nSimulating {len(controllers)} controllers...")
        print("Press Ctrl+C to stop")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping simulators...")
        simulator.disconnect()

if __name__ == '__main__':
    main()