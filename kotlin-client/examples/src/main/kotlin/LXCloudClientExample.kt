package examples

import com.lxcloud.client.LXCloudClient
import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.*
import kotlinx.coroutines.delay

/**
 * Complete example demonstrating all features of the LXCloud Kotlin client
 */
class LXCloudClientExample {
    
    suspend fun runCompleteExample() {
        println("🚀 Starting LXCloud Client Example")
        
        // Create client
        val client = LXCloudClient.create(
            baseUrl = "http://localhost:5000",  // Adjust to your server
            enableLogging = true
        )
        
        try {
            // 1. Test connection
            println("\n📡 Testing connection...")
            val connectionResult = client.connect()
            if (connectionResult.isSuccess) {
                println("✅ Connected to LXCloud server!")
            } else {
                println("❌ Failed to connect: ${connectionResult.exceptionOrNull()?.message}")
                return
            }
            
            // 2. Register controllers
            println("\n📝 Registering controllers...")
            
            val speedRadar = client.registerController(
                serialNumber = "SR001",
                type = ControllerType.SPEED_RADAR,
                name = "Highway Speed Monitor",
                latitude = 52.3676,
                longitude = 4.9041,
                timeoutSeconds = 300
            )
            
            val weatherStation = client.registerController(
                serialNumber = "WS001", 
                type = ControllerType.WEATHER_STATION,
                name = "Central Weather Station",
                latitude = 52.3700,
                longitude = 4.9000
            )
            
            if (speedRadar.isSuccess && weatherStation.isSuccess) {
                println("✅ Controllers registered successfully!")
                println("   Speed Radar: ${speedRadar.getOrNull()?.name}")
                println("   Weather Station: ${weatherStation.getOrNull()?.name}")
            }
            
            // 3. Send data from controllers
            println("\n📊 Sending sensor data...")
            
            // Speed radar data
            val speedData = mapOf(
                "current_speed" to 65.5,
                "average_speed" to 58.2,
                "vehicle_count" to 127,
                "max_speed" to 95.0,
                "timestamp" to System.currentTimeMillis()
            )
            
            val speedResult = client.sendData("SR001", speedData)
            if (speedResult.isSuccess) {
                println("✅ Speed radar data sent: ${speedResult.getOrNull()}")
            }
            
            // Weather station data
            val weatherData = mapOf(
                "temperature" to 23.5,
                "humidity" to 65,
                "pressure" to 1013.25,
                "wind_speed" to 12.5,
                "wind_direction" to 245,
                "rainfall" to 0.0,
                "timestamp" to System.currentTimeMillis()
            )
            
            val weatherResult = client.sendData("WS001", weatherData)
            if (weatherResult.isSuccess) {
                println("✅ Weather station data sent: ${weatherResult.getOrNull()}")
            }
            
            // 4. Status management
            println("\n🔄 Managing controller status...")
            
            // Mark controllers as online
            client.markOnline("SR001")
            client.markOnline("WS001")
            println("✅ Controllers marked as online")
            
            // Check status
            val sr001Online = client.isControllerOnline("SR001")
            val ws001Online = client.isControllerOnline("WS001")
            
            if (sr001Online.isSuccess && ws001Online.isSuccess) {
                println("📊 Status check:")
                println("   SR001 online: ${sr001Online.getOrNull()}")
                println("   WS001 online: ${ws001Online.getOrNull()}")
            }
            
            // 5. Update controller information
            println("\n✏️ Updating controller information...")
            
            val nameUpdate = client.updateControllerName("SR001", "Highway Speed Monitor - Updated")
            if (nameUpdate.isSuccess) {
                println("✅ Controller name updated")
            }
            
            val locationUpdate = client.updateControllerLocation("WS001", 52.3750, 4.9050)
            if (locationUpdate.isSuccess) {
                println("✅ Controller location updated")
            }
            
            // 6. Retrieve controller information
            println("\n📖 Retrieving controller information...")
            
            val sr001Info = client.getController("SR001")
            val ws001Info = client.getController("WS001")
            
            if (sr001Info.isSuccess && ws001Info.isSuccess) {
                println("📄 Controller information:")
                println("   ${sr001Info.getOrNull()}")
                println("   ${ws001Info.getOrNull()}")
            }
            
            // 7. Demonstrate batch operations
            println("\n📦 Sending batch data...")
            
            val batchData = listOf(
                mapOf("reading" to 10.5, "sequence" to 1),
                mapOf("reading" to 11.0, "sequence" to 2),
                mapOf("reading" to 10.8, "sequence" to 3)
            )
            
            val batchResult = client.sendDataBatch("SR001", batchData)
            if (batchResult.isSuccess) {
                println("✅ Batch data sent: ${batchResult.getOrNull()?.size} items")
            }
            
            // 8. Simulate continuous monitoring
            println("\n🔄 Simulating continuous monitoring (5 readings)...")
            
            repeat(5) { i ->
                val simulatedData = mapOf(
                    "reading_id" to i + 1,
                    "value" to (20.0 + (Math.random() * 10)), // Random value 20-30
                    "timestamp" to System.currentTimeMillis()
                )
                
                client.sendData("WS001", simulatedData)
                println("📡 Sent reading ${i + 1}: ${simulatedData["value"]}")
                delay(1000) // Wait 1 second between readings
            }
            
            println("\n✅ Continuous monitoring simulation complete")
            
            // 9. Demonstrate admin operations (if authentication is available)
            println("\n🔐 Admin operations (authentication required)...")
            
            // Note: These will fail without proper authentication
            val allControllers = client.listAllControllers()
            if (allControllers.isFailure) {
                println("ℹ️ Admin operations require authentication token")
                println("   Error: ${allControllers.exceptionOrNull()?.message}")
            } else {
                println("✅ Retrieved all controllers: ${allControllers.getOrNull()?.size}")
            }
            
            // 10. Cleanup
            println("\n🧹 Cleaning up...")
            client.markOffline("SR001")
            client.markOffline("WS001")
            println("✅ Controllers marked as offline")
            
        } catch (e: Exception) {
            println("❌ Error during example execution: ${e.message}")
            e.printStackTrace()
        } finally {
            client.disconnect()
            println("🔌 Disconnected from server")
        }
        
        println("\n🎉 Example completed successfully!")
    }
}

/**
 * Simulated IoT device that sends periodic data
 */
class SimulatedSpeedRadar(
    private val serialNumber: String,
    private val client: LXCloudClient
) {
    private var isRunning = false
    private var monitoringJob: Job? = null
    
    suspend fun start() {
        if (isRunning) return
        
        println("🚗 Starting Speed Radar $serialNumber")
        
        // Register the device
        val registration = client.registerAndActivateController(
            serialNumber = serialNumber,
            type = ControllerType.SPEED_RADAR,
            name = "Simulated Speed Radar $serialNumber",
            latitude = 52.3676 + (Math.random() * 0.01), // Slight random variation
            longitude = 4.9041 + (Math.random() * 0.01)
        )
        
        if (registration.isFailure) {
            println("❌ Failed to register speed radar: ${registration.exceptionOrNull()?.message}")
            return
        }
        
        isRunning = true
        
        // Start continuous monitoring
        monitoringJob = CoroutineScope(Dispatchers.Default).launch {
            while (isRunning) {
                try {
                    val speed = 30 + (Math.random() * 70) // Random speed 30-100 km/h
                    val vehicleCount = (Math.random() * 50).toInt() // Random count 0-50
                    
                    val data = mapOf(
                        "current_speed" to speed,
                        "vehicle_count" to vehicleCount,
                        "timestamp" to System.currentTimeMillis(),
                        "device_id" to serialNumber
                    )
                    
                    val result = client.sendData(serialNumber, data)
                    if (result.isSuccess) {
                        println("📊 $serialNumber: Speed=${String.format("%.1f", speed)} km/h, Vehicles=$vehicleCount")
                    } else {
                        println("❌ $serialNumber: Failed to send data - ${result.exceptionOrNull()?.message}")
                    }
                    
                    delay(5000) // Send data every 5 seconds
                } catch (e: Exception) {
                    println("❌ $serialNumber: Error in monitoring loop - ${e.message}")
                    break
                }
            }
        }
    }
    
    suspend fun stop() {
        if (!isRunning) return
        
        println("🛑 Stopping Speed Radar $serialNumber")
        isRunning = false
        monitoringJob?.cancel()
        client.markOffline(serialNumber)
    }
}

/**
 * Main function to run examples
 */
suspend fun main() {
    println("🌟 LXCloud Kotlin Client Examples")
    println("==================================\n")
    
    // Run complete example
    val example = LXCloudClientExample()
    example.runCompleteExample()
    
    println("\n" + "=".repeat(50))
    println("🤖 Running simulated IoT devices example...")
    
    // Create client for simulation
    val client = LXCloudClient.create("http://localhost:5000", enableLogging = false)
    
    try {
        val connectionResult = client.connect()
        if (connectionResult.isSuccess) {
            println("✅ Connected for simulation")
            
            // Create multiple simulated devices
            val devices = listOf(
                SimulatedSpeedRadar("SIM_SR001", client),
                SimulatedSpeedRadar("SIM_SR002", client),
                SimulatedSpeedRadar("SIM_SR003", client)
            )
            
            // Start all devices
            devices.forEach { it.start() }
            
            // Let them run for 30 seconds
            println("⏱️ Running simulation for 30 seconds...")
            delay(30000)
            
            // Stop all devices
            devices.forEach { it.stop() }
            
            println("✅ Simulation completed")
        } else {
            println("❌ Failed to connect for simulation")
        }
    } finally {
        client.disconnect()
    }
    
    println("\n🎯 All examples completed!")
}