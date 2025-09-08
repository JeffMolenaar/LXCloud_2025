# Quick Setup Guide

## Build the Client

```bash
cd kotlin-client
./gradlew build
```

## Run the Demo

To test the client with your LXCloud server:

1. Make sure your LXCloud server is running:
   ```bash
   cd ../
   python run.py
   ```

2. In another terminal, you can test the client:
   ```bash
   cd kotlin-client
   # The demo tries to connect to http://localhost:5000
   # Edit examples/src/main/kotlin/SimpleDemo.kt to change the server URL
   ```

## Integration in Your Project

### Add to your build.gradle.kts:

```kotlin
dependencies {
    implementation(files("path/to/kotlin-client/build/libs/kotlin-client-1.0.0.jar"))
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
```

### Basic Usage:

```kotlin
import com.lxcloud.client.LXCloudClient
import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    val client = LXCloudClient.create("http://your-lxcloud-server:5000")
    
    client.connect()
    
    // Register a controller
    val result = client.registerController(
        serialNumber = "YOUR_CONTROLLER_ID",
        type = ControllerType.SPEED_RADAR,
        name = "My Speed Radar"
    )
    
    // Send data
    client.sendData("YOUR_CONTROLLER_ID", mapOf(
        "speed" to 65.5,
        "timestamp" to System.currentTimeMillis()
    ))
    
    client.disconnect()
}
```

## Features

- ✅ Easy connection management
- ✅ Controller registration and configuration  
- ✅ Real-time data transmission
- ✅ Status management
- ✅ Admin operations (with authentication)
- ✅ Type-safe API
- ✅ Error handling
- ✅ Coroutine support