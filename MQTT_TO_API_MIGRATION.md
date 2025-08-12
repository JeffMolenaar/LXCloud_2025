# MQTT to API Migration Guide

This guide helps you migrate existing controllers from MQTT communication to the new REST API endpoints.

## Quick Migration Summary

| MQTT Method | New API Method |
|-------------|----------------|
| Publish to `lxcloud/{serial}/data` | POST `/api/controllers/{serial}/data` |
| Publish to `lxcloud/{serial}/status` | POST `/api/controllers/{serial}/status` |
| Initial registration via data | POST `/api/controllers/register` |

## Migration Steps

### 1. Replace MQTT Client with HTTP Client

**Before (MQTT):**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set("username", "password")
client.connect("mqtt.lxcloud.local", 1883, 60)

# Send data
data = {"temperature": 22.5, "humidity": 65}
client.publish(f"lxcloud/{SERIAL}/data", json.dumps(data))
```

**After (API):**
```python
import requests

BASE_URL = "http://lxcloud.local/api"
SERIAL = "WEATHER001"

# Send data
data = {"temperature": 22.5, "humidity": 65}
response = requests.post(f"{BASE_URL}/controllers/{SERIAL}/data", json=data)
```

### 2. Add Initial Registration

**New requirement - register your controller first:**
```python
# Register controller (do this once at startup)
registration = {
    "serial_number": "WEATHER001",
    "type": "weatherstation", 
    "name": "Roof Weather Station",
    "latitude": 52.3676,
    "longitude": 4.9041
}

response = requests.post(f"{BASE_URL}/controllers/register", json=registration)
if response.status_code in [200, 201]:
    print("Controller registered successfully")
```

### 3. Update Data Sending

**Before:**
```python
# MQTT data message
payload = {
    "type": "weatherstation",
    "data": {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    },
    "latitude": current_lat,
    "longitude": current_lng
}
client.publish(f"lxcloud/{serial}/data", json.dumps(payload))
```

**After:**
```python
# API data update (simpler structure)
data = {
    "temperature": temperature,
    "humidity": humidity, 
    "pressure": pressure,
    "latitude": current_lat,  # Optional location update
    "longitude": current_lng
}
response = requests.post(f"{BASE_URL}/controllers/{serial}/data", json=data)
```

### 4. Update Status Reporting

**Before:**
```python
status = {"online": True}
client.publish(f"lxcloud/{serial}/status", json.dumps(status))
```

**After:**
```python
status = {"online": True}
response = requests.post(f"{BASE_URL}/controllers/{serial}/status", json=status)
```

## Complete Example Migration

### Before (MQTT-based controller):
```python
import paho.mqtt.client as mqtt
import json
import time

class WeatherController:
    def __init__(self, serial, mqtt_host):
        self.serial = serial
        self.client = mqtt.Client()
        self.client.connect(mqtt_host, 1883, 60)
        
    def send_data(self, temperature, humidity):
        payload = {
            "type": "weatherstation",
            "data": {
                "temperature": temperature,
                "humidity": humidity
            }
        }
        self.client.publish(f"lxcloud/{self.serial}/data", json.dumps(payload))
        
    def update_status(self, online):
        payload = {"online": online}
        self.client.publish(f"lxcloud/{self.serial}/status", json.dumps(payload))
```

### After (API-based controller):
```python
import requests
import json
import time

class WeatherController:
    def __init__(self, serial, api_base_url):
        self.serial = serial
        self.api_url = api_base_url
        self.register()
        
    def register(self):
        """Register controller with the system"""
        data = {
            "serial_number": self.serial,
            "type": "weatherstation",
            "name": f"Weather Station {self.serial}",
            "latitude": 52.3676,  # Your location
            "longitude": 4.9041
        }
        response = requests.post(f"{self.api_url}/controllers/register", json=data)
        if response.status_code not in [200, 201]:
            print(f"Registration failed: {response.text}")
            
    def send_data(self, temperature, humidity):
        data = {
            "temperature": temperature,
            "humidity": humidity
        }
        response = requests.post(f"{self.api_url}/controllers/{self.serial}/data", json=data)
        return response.status_code == 200
        
    def update_status(self, online):
        data = {"online": online}
        response = requests.post(f"{self.api_url}/controllers/{self.serial}/status", json=data)
        return response.status_code == 200
```

## Benefits of API Migration

1. **Simpler**: No MQTT broker dependency
2. **More reliable**: HTTP has better error handling
3. **Easier debugging**: Standard HTTP status codes
4. **Better authentication**: Can use standard HTTP auth methods
5. **Firewall friendly**: Uses standard HTTP ports
6. **Location updates**: Easier to update controller position

## Testing Your Migration

Use the provided test script to verify your controller works:

```bash
python test_controller_api.py
```

Or test individual endpoints:

```bash
# Test registration
curl -X POST http://your-server/api/controllers/register \
  -H "Content-Type: application/json" \
  -d '{"serial_number":"TEST001","type":"weatherstation","latitude":52.3676,"longitude":4.9041}'

# Test data update  
curl -X POST http://your-server/api/controllers/TEST001/data \
  -H "Content-Type: application/json" \
  -d '{"temperature":22.5,"humidity":65}'
```

## Backward Compatibility

The MQTT system will continue to work during migration, but it's recommended to switch to the API for better reliability and features like location updates.