# Controller Online/Offline Status Management

This document describes the automatic controller status management system implemented in LXCloud.

## Overview

The system automatically manages controller online/offline status based on when controllers last reported to the cloud platform. This ensures that the dashboard accurately reflects the real-time status of all controllers without requiring manual intervention.

## How It Works

### Automatic Offline Detection
- Controllers are automatically marked **offline** when they haven't reported to the platform within the configured timeout period
- The background service checks all controllers periodically and updates their status
- Default timeout: **5 minutes** (300 seconds)
- Default check interval: **1 minute** (60 seconds)

### Automatic Online Detection
- Controllers are automatically marked **online** when they:
  - Register with the platform (`POST /api/controllers/register`)
  - Send data updates (`POST /api/controllers/{serial}/data`)
  - Send status updates (`POST /api/controllers/{serial}/status`)
  - Are modified via API (`PUT /api/controllers/{serial}`)

### Behavior
- If a controller posts data **within** the timeout window → stays **online**
- If a controller hasn't posted for **longer than** the timeout → marked **offline**
- When an offline controller posts again → immediately marked **online**

## Configuration

Add these settings to your `.env` file:

```bash
# How long (in seconds) before a controller is considered offline (default: 300 = 5 minutes)
CONTROLLER_OFFLINE_TIMEOUT=300

# How often (in seconds) to check for offline controllers (default: 60 = 1 minute)
CONTROLLER_STATUS_CHECK_INTERVAL=60
```

### Configuration Examples

**Conservative (10 minute timeout, check every 2 minutes):**
```bash
CONTROLLER_OFFLINE_TIMEOUT=600
CONTROLLER_STATUS_CHECK_INTERVAL=120
```

**Aggressive (2 minute timeout, check every 30 seconds):**
```bash
CONTROLLER_OFFLINE_TIMEOUT=120
CONTROLLER_STATUS_CHECK_INTERVAL=30
```

**Very responsive (30 second timeout, check every 10 seconds):**
```bash
CONTROLLER_OFFLINE_TIMEOUT=30
CONTROLLER_STATUS_CHECK_INTERVAL=10
```

## Monitoring

### System Status API
Administrators can monitor the background services via:
```
GET /api/system/status
```

Response includes:
- Controller status service status (enabled, running, intervals)
- MQTT service status
- System version

### Logs
The controller status service logs its activities:
```
Controller status service started (check interval: 60s, timeout: 300s)
Controller SENSOR001 marked offline (last seen: 2025-08-13 10:30:15)
Updated 3 controller(s) to offline status
```

## API Endpoints (Unchanged)

All existing API endpoints continue to work exactly as before:

- `POST /api/controllers/register` - Register new controllers
- `POST /api/controllers/{serial}/data` - Send sensor data
- `POST /api/controllers/{serial}/status` - Update controller status
- `PUT /api/controllers/{serial}` - Modify controller settings
- `GET /api/controllers/{serial}` - Get controller information

## Database Schema

No database migrations are required. The system uses existing fields:

- `Controller.is_online` (boolean) - Current online status
- `Controller.last_seen` (datetime) - Last time controller reported

## Testing

Run the included tests to verify functionality:

```bash
# Test the status timeout functionality
python archive/test-scripts-removed-20250924/test_controller_status.py

# Test API integration with status management
python archive/test-scripts-removed-20250924/test_integration_status.py

# Test existing API endpoints (should all still work)
python archive/test-scripts-removed-20250924/test_controller_api.py
```

## Performance Considerations

- The background service runs in a separate thread
- Database queries are efficient (indexed on `is_online` and `last_seen`)
- Configurable check interval allows tuning based on your needs
- Service gracefully handles database connection issues

## Troubleshooting

### Service Not Starting
Check logs for initialization messages:
```
Controller status service started (check interval: 60s, timeout: 300s)
```

### Controllers Not Going Offline
- Verify the timeout configuration
- Check if controllers are posting data more frequently than expected
- Monitor logs for status check messages

### High Database Load
- Increase `CONTROLLER_STATUS_CHECK_INTERVAL` to reduce frequency
- Ensure your database has indexes on `controllers.is_online` and `controllers.last_seen`

## Implementation Details

The system consists of:

1. **Configuration** (`config/config.py`) - Timeout settings
2. **Background Service** (`app/controller_status_service.py`) - Status checker
3. **Model Methods** (`app/models.py`) - Helper methods for status management
4. **API Integration** (`app/routes/api.py`) - Automatic online status setting
5. **Application Startup** (`run.py`) - Service initialization