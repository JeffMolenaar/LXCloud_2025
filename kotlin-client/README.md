# LXCloud Kotlin Client

A Kotlin client library for easy connecting and disconnecting to the LXCloud server API. This library provides a simple interface to interact with the LXCloud system, allowing you to register controllers, send data, manage controller status, and perform administrative operations.

## Features

- ✅ Easy connection management
- ✅ Controller registration and management
- ✅ Real-time data transmission
- ✅ Status management (online/offline)
- ✅ Authentication support for admin operations
- ✅ Comprehensive error handling
- ✅ Coroutine-based async operations
- ✅ Type-safe API with Kotlin serialization
- ✅ Configurable timeouts and logging

## Installation

Add the following dependencies to your `build.gradle.kts`:

```kotlin
dependencies {
    implementation("com.lxcloud:kotlin-client:1.0.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
```

## Quick Start

### Basic Usage

```kotlin
import com.lxcloud.client.LXCloudClient
import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    // Create client instance
    val client = LXCloudClient.create("http://your-lxcloud-server.com")
    
    try {
        // Test connection
        val connected = client.connect()
        if (connected.isSuccess) {
            println("Connected to LXCloud server!")
            
            // Register a new controller
            val controller = client.registerController(
                serialNumber = "SR001",
                type = ControllerType.SPEED_RADAR,
                name = "Highway Speed Monitor",
                latitude = 52.3676,
                longitude = 4.9041
            )
            
            if (controller.isSuccess) {
                println("Controller registered: ${controller.getOrNull()}")
                
                // Send some sensor data
                val data = mapOf(
                    "speed" to 65.5,
                    "vehicle_count" to 127,
                    "timestamp" to System.currentTimeMillis()
                )
                
                val result = client.sendData("SR001", data)
                if (result.isSuccess) {
                    println("Data sent successfully: ${result.getOrNull()}")
                }
            }
        }
    } finally {
        client.disconnect()
    }
}
```

### Advanced Usage with Authentication

```kotlin
import com.lxcloud.client.LXCloudClient
import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    // Create authenticated client for admin operations
    val client = LXCloudClient.createAuthenticated(
        baseUrl = "http://your-lxcloud-server.com",
        authToken = "your-auth-token",
        enableLogging = true
    )
    
    try {
        // List all controllers (admin operation)
        val controllers = client.listAllControllers()
        if (controllers.isSuccess) {
            controllers.getOrNull()?.forEach { controller ->
                println("Controller: ${controller.name} (${controller.serialNumber}) - Online: ${controller.isOnline}")
            }
        }
        
        // Get system statistics
        val stats = client.getSystemStats()
        if (stats.isSuccess) {
            val overview = stats.getOrNull()!!
            println("Total Controllers: ${overview.totalControllers}")
            println("Online Controllers: ${overview.onlineControllers}")
            println("Offline Controllers: ${overview.offlineControllers}")
        }
        
        // Get only speed radar controllers
        val speedRadars = client.getControllersByType(ControllerType.SPEED_RADAR)
        if (speedRadars.isSuccess) {
            println("Found ${speedRadars.getOrNull()?.size} speed radars")
        }
        
    } finally {
        client.disconnect()
    }
}
```

## API Reference

### Connection Management

```kotlin
// Create client
val client = LXCloudClient.create("http://server.com")

// Test connection
val connected: Result<Boolean> = client.connect()

// Check connection status
val isConnected: Boolean = client.isConnected()

// Disconnect and cleanup
client.disconnect()
```

### Controller Operations

#### Register Controller

```kotlin
val result = client.registerController(
    serialNumber = "ABC123",
    type = ControllerType.WEATHER_STATION,
    name = "Weather Station 1",
    latitude = 52.3676,
    longitude = 4.9041,
    timeoutSeconds = 300
)
```

#### Send Data

```kotlin
val data = mapOf(
    "temperature" to 23.5,
    "humidity" to 65,
    "pressure" to 1013.25
)
val result = client.sendData("ABC123", data)
```

#### Send Data with Location

```kotlin
val data = mapOf("speed" to 45.5)
val result = client.sendDataWithLocation(
    serialNumber = "ABC123",
    data = data,
    latitude = 52.3676,
    longitude = 4.9041
)
```

#### Status Management

```kotlin
// Mark online
val onlineResult = client.markOnline("ABC123")

// Mark offline
val offlineResult = client.markOffline("ABC123")

// Check if online
val isOnline = client.isControllerOnline("ABC123")
```

#### Controller Information

```kotlin
// Get controller details
val controller = client.getController("ABC123")

// Update controller name
val updated = client.updateControllerName("ABC123", "New Name")

// Update location
val updated = client.updateControllerLocation("ABC123", 52.0, 4.0)

// Update type
val updated = client.updateControllerType("ABC123", ControllerType.AI_CAMERA)
```

### Admin Operations (Require Authentication)

```kotlin
// Set authentication token
client.setAuthToken("your-token")

// List all controllers
val controllers = client.listAllControllers()

// Get controller status
val status = client.getControllerStatus()

// Get system statistics
val stats = client.getSystemStats()

// Get controllers by type
val weatherStations = client.getControllersByType(ControllerType.WEATHER_STATION)

// Get only online controllers
val onlineControllers = client.getOnlineControllers()
```

### Convenience Methods

```kotlin
// Register and immediately activate
val controller = client.registerAndActivateController(
    serialNumber = "ABC123",
    type = ControllerType.SPEED_RADAR,
    name = "Highway Monitor"
)

// Send multiple data points
val dataPoints = listOf(
    mapOf("reading1" to 10.5),
    mapOf("reading2" to 11.0),
    mapOf("reading3" to 10.8)
)
val results = client.sendDataBatch("ABC123", dataPoints)
```

## Controller Types

The library supports the following controller types:

- `ControllerType.SPEED_RADAR` - Speed radar controllers
- `ControllerType.BEAUFORT_METER` - Beaufort wind meter controllers  
- `ControllerType.WEATHER_STATION` - Weather station controllers
- `ControllerType.AI_CAMERA` - AI camera controllers

## Error Handling

All methods return `Result<T>` objects that wrap successful results or exceptions:

```kotlin
val result = client.registerController(...)

if (result.isSuccess) {
    val controller = result.getOrNull()
    println("Success: $controller")
} else {
    val error = result.exceptionOrNull()
    println("Error: ${error?.message}")
}

// Or use map/fold for functional style
result
    .map { controller -> println("Registered: ${controller.name}") }
    .fold(
        onSuccess = { println("Operation successful") },
        onFailure = { error -> println("Operation failed: ${error.message}") }
    )
```

## Configuration

### Client Configuration

```kotlin
val client = LXCloudClient(
    baseUrl = "http://your-server.com",
    enableLogging = true,           // Enable HTTP logging
    connectTimeoutSeconds = 30,     // Connection timeout
    readTimeoutSeconds = 60         // Read timeout
)
```

### Auto-Closeable Support

The client implements `AutoCloseable` for automatic resource management:

```kotlin
LXCloudClient.create("http://server.com").use { client ->
    // Use client here
    client.connect()
    // Client automatically closed when leaving this block
}
```

## Thread Safety

The client is thread-safe and all operations are coroutine-based. You can safely use the same client instance from multiple coroutines.

## Examples

### IoT Device Example

```kotlin
class SpeedRadarDevice(private val serialNumber: String) {
    private val client = LXCloudClient.create("http://lxcloud-server.com")
    
    suspend fun initialize() {
        client.connect()
        client.registerController(
            serialNumber = serialNumber,
            type = ControllerType.SPEED_RADAR,
            name = "Highway Speed Radar $serialNumber"
        )
        client.markOnline(serialNumber)
    }
    
    suspend fun sendSpeedReading(speed: Double, vehicleCount: Int) {
        val data = mapOf(
            "speed" to speed,
            "vehicle_count" to vehicleCount,
            "timestamp" to System.currentTimeMillis()
        )
        client.sendData(serialNumber, data)
    }
    
    suspend fun shutdown() {
        client.markOffline(serialNumber)
        client.disconnect()
    }
}
```

### Dashboard Application Example

```kotlin
class ControllerDashboard(authToken: String) {
    private val client = LXCloudClient.createAuthenticated(
        baseUrl = "http://lxcloud-server.com",
        authToken = authToken
    )
    
    suspend fun getDashboardData(): DashboardData {
        val stats = client.getSystemStats().getOrThrow()
        val controllers = client.listAllControllers().getOrThrow()
        val onlineControllers = controllers.filter { it.isOnline }
        
        return DashboardData(
            totalControllers = stats.totalControllers,
            onlineControllers = stats.onlineControllers,
            controllers = controllers,
            onlineControllersList = onlineControllers
        )
    }
}

data class DashboardData(
    val totalControllers: Int,
    val onlineControllers: Int,
    val controllers: List<Controller>,
    val onlineControllersList: List<Controller>
)
```

## Testing

Run the tests using:

```bash
./gradlew test
```

The library includes comprehensive unit tests with mocked HTTP responses to ensure reliability.