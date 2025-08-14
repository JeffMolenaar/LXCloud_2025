# Per-Controller Timeout Configuration

This document describes the per-controller timeout feature that allows each controller to have its own custom timeout value for determining when it should be considered offline.

## Overview

By default, all controllers use a global timeout value (`CONTROLLER_OFFLINE_TIMEOUT`) of 300 seconds (5 minutes). With the per-controller timeout feature, individual controllers can override this global default with their own custom timeout values.

## How It Works

1. **When a controller posts data** → controller is marked online
2. **When a controller doesn't post data within its timeout period** → controller is marked offline
3. **The timeout period is settable per controller** via the `timeout_seconds` field

## API Usage

### Setting Timeout During Registration

When registering a controller, you can specify a custom timeout:

```bash
curl -X POST http://localhost/api/controllers/register \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "250100.1.0625",
    "type": "speedradar",
    "name": "My Speed Radar",
    "latitude": 51.913071,
    "longitude": 5.713852,
    "timeout_seconds": 120
  }'
```

### Modifying Timeout for Existing Controller

You can update the timeout for an existing controller:

```bash
curl -X PUT http://localhost/api/controllers/250100.1.0625 \
  -H "Content-Type: application/json" \
  -d '{
    "timeout_seconds": 180
  }'
```

### Removing Custom Timeout (Revert to Global Default)

Set `timeout_seconds` to `null` to use the global default:

```bash
curl -X PUT http://localhost/api/controllers/250100.1.0625 \
  -H "Content-Type: application/json" \
  -d '{
    "timeout_seconds": null
  }'
```

## Database Schema

The `controllers` table now includes a `timeout_seconds` field:

- **Type**: INTEGER
- **Nullable**: Yes (NULL means use global default)
- **Constraints**: Must be a positive integer when set

## Behavior

### Controller Status Service

The background controller status service checks each controller's individual timeout:

1. For controllers with `timeout_seconds` set: Uses that value
2. For controllers with `timeout_seconds` = NULL: Uses the global `CONTROLLER_OFFLINE_TIMEOUT`

### API Endpoints

All controller API endpoints that mark controllers as online will respect the per-controller timeout when determining if the controller should later be marked offline.

## Examples

### Scenario 1: Different Device Types, Different Timeouts

- **Speed Radars**: 300 seconds (global default)
- **Weather Stations**: 900 seconds (15 minutes) - due to less frequent data transmission
- **AI Cameras**: 60 seconds (1 minute) - for critical real-time monitoring

### Scenario 2: Network Environment Considerations

- **Controllers on reliable networks**: 120 seconds
- **Controllers on cellular/unreliable networks**: 600 seconds (10 minutes)

## Migration

Existing controllers without a `timeout_seconds` value will continue to use the global timeout (`CONTROLLER_OFFLINE_TIMEOUT`). No migration or configuration changes are required for existing deployments.

## Configuration

The global timeout is still controlled by the environment variable:

```bash
CONTROLLER_OFFLINE_TIMEOUT=300  # Default 5 minutes
```

This serves as the fallback for controllers that don't have a custom timeout configured.