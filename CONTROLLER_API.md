# Controller API Documentation

This document describes the API endpoints that controller devices should use to communicate with the LXCloud system instead of MQTT.

## Base URL

All API endpoints are relative to: `http://your-lxcloud-server/api`

## Authentication

The controller API endpoints do not require authentication - they are designed for use by IoT devices.

## Endpoints

### 1. Register Controller

Register a new controller or update an existing one.

**Endpoint:** `POST /controllers/register`

**Request Body:**
```json
{
    "serial_number": "ABC123",
    "type": "speedradar",
    "name": "Highway Speed Monitor",
    "latitude": 52.3676,
    "longitude": 4.9041
}
```

**Fields:**
- `serial_number` (required): Unique identifier for the controller
- `type` (required): Controller type - one of: `speedradar`, `beaufortmeter`, `weatherstation`, `aicamera`
- `name` (optional): Human-readable name for the controller
- `latitude` (optional): GPS latitude coordinate
- `longitude` (optional): GPS longitude coordinate

**Response (201 Created):**
```json
{
    "message": "Controller registered successfully",
    "controller": {
        "id": 1,
        "serial_number": "ABC123",
        "controller_type": "speedradar",
        "name": "Highway Speed Monitor",
        "latitude": 52.3676,
        "longitude": 4.9041,
        "is_online": true,
        "last_seen": "2025-01-08T10:30:00",
        "created_at": "2025-01-08T10:30:00"
    }
}
```

### 2. Send Data

Send sensor data from the controller.

**Endpoint:** `POST /controllers/<serial_number>/data`

**Request Body:**
```json
{
    "temperature": 22.5,
    "humidity": 65.3,
    "speed": 45.2,
    "direction": "north",
    "latitude": 52.3676,
    "longitude": 4.9041
}
```

**Note:** The data fields depend on the controller type. Common fields:
- Speed Radar: `speed`, `direction`, `vehicle_count`
- Weather Station: `temperature`, `humidity`, `pressure`, `wind_speed`, `wind_direction`
- Beaufort Meter: `wind_speed`, `beaufort_scale`, `direction`
- AI Camera: `detections`, `objects_count`, `alert_level`

**Response (200 OK):**
```json
{
    "message": "Data updated successfully",
    "timestamp": "2025-01-08T10:30:00"
}
```

### 3. Update Status

Update the online/offline status of the controller.

**Endpoint:** `POST /controllers/<serial_number>/status`

**Request Body:**
```json
{
    "online": true
}
```

**Response (200 OK):**
```json
{
    "message": "Status updated successfully",
    "status": "online"
}
```

### 4. Modify Controller

Update controller configuration.

**Endpoint:** `PUT /controllers/<serial_number>`

**Request Body:**
```json
{
    "name": "Updated Controller Name",
    "type": "weatherstation",
    "latitude": 52.3700,
    "longitude": 4.9100
}
```

**Response (200 OK):**
```json
{
    "message": "Controller updated successfully",
    "controller": {
        "id": 1,
        "serial_number": "ABC123",
        "controller_type": "weatherstation",
        "name": "Updated Controller Name",
        "latitude": 52.3700,
        "longitude": 4.9100,
        "is_online": true,
        "last_seen": "2025-01-08T10:30:00",
        "created_at": "2025-01-08T10:30:00"
    }
}
```

### 5. Get Controller Info

Retrieve controller information.

**Endpoint:** `GET /controllers/<serial_number>`

**Response (200 OK):**
```json
{
    "controller": {
        "id": 1,
        "serial_number": "ABC123",
        "controller_type": "speedradar",
        "name": "Highway Speed Monitor",
        "latitude": 52.3676,
        "longitude": 4.9041,
        "is_online": true,
        "last_seen": "2025-01-08T10:30:00",
        "created_at": "2025-01-08T10:30:00"
    }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Controller not found
- `500 Internal Server Error` - Server error

Error responses include details:
```json
{
    "error": "Description of the error"
}
```

## Migration from MQTT

Controllers currently using MQTT should migrate to use these API endpoints:

### Before (MQTT):
- **Register:** Send initial data to `lxcloud/{serial_number}/data`
- **Send Data:** Publish to `lxcloud/{serial_number}/data`
- **Update Status:** Publish to `lxcloud/{serial_number}/status`

### After (API):
- **Register:** `POST /api/controllers/register`
- **Send Data:** `POST /api/controllers/{serial_number}/data`
- **Update Status:** `POST /api/controllers/{serial_number}/status`

## Example Usage

### Python Example

```python
import requests
import json

# Configuration
BASE_URL = 'http://your-lxcloud-server/api'
SERIAL_NUMBER = 'WEATHER001'

# Register controller
registration_data = {
    'serial_number': SERIAL_NUMBER,
    'type': 'weatherstation',
    'name': 'Roof Weather Station',
    'latitude': 52.3676,
    'longitude': 4.9041
}

response = requests.post(f'{BASE_URL}/controllers/register', 
                        json=registration_data)
print(f"Registration: {response.status_code} - {response.json()}")

# Send data periodically
sensor_data = {
    'temperature': 22.5,
    'humidity': 65.3,
    'pressure': 1013.25,
    'wind_speed': 5.2,
    'wind_direction': 'NW'
}

response = requests.post(f'{BASE_URL}/controllers/{SERIAL_NUMBER}/data',
                        json=sensor_data)
print(f"Data update: {response.status_code} - {response.json()}")
```

### Sending Location Updates

Controllers can update their location by including latitude/longitude in any data update:

```python
sensor_data = {
    'temperature': 22.5,
    'latitude': 52.3680,  # Updated location
    'longitude': 4.9045   # Updated location
}

requests.post(f'{BASE_URL}/controllers/{SERIAL_NUMBER}/data', json=sensor_data)
```

This will automatically update the controller's location in the system and the map will show the new position.