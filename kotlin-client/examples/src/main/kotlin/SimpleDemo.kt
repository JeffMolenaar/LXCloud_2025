package examples

import com.lxcloud.client.LXCloudClient
import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.runBlocking

/**
 * Simple demo showing basic usage of the LXCloud Kotlin client
 */
fun main() = runBlocking {
    println("🚀 LXCloud Kotlin Client Demo")
    println("=============================")
    
    // Create client (adjust URL to your LXCloud server)
    val client = LXCloudClient.create(
        baseUrl = "http://localhost:5000",
        enableLogging = true
    )
    
    try {
        // 1. Connect to server
        println("\n📡 Connecting to LXCloud server...")
        val connected = client.connect()
        
        if (connected.isSuccess) {
            println("✅ Connected successfully!")
        } else {
            println("❌ Connection failed: ${connected.exceptionOrNull()?.message}")
            println("💡 Make sure your LXCloud server is running on http://localhost:5000")
            return@runBlocking
        }
        
        // 2. Register a speed radar controller
        println("\n📝 Registering speed radar controller...")
        val controller = client.registerController(
            serialNumber = "DEMO_SR001",
            type = ControllerType.SPEED_RADAR,
            name = "Demo Speed Radar",
            latitude = 52.3676,
            longitude = 4.9041,
            timeoutSeconds = 300
        )
        
        if (controller.isSuccess) {
            println("✅ Controller registered: ${controller.getOrNull()?.name}")
            println("   Serial: ${controller.getOrNull()?.serialNumber}")
            println("   Type: ${controller.getOrNull()?.controllerType}")
            println("   Online: ${controller.getOrNull()?.isOnline}")
        } else {
            println("❌ Registration failed: ${controller.exceptionOrNull()?.message}")
        }
        
        // 3. Send some sensor data
        println("\n📊 Sending sensor data...")
        val sensorData = mapOf(
            "current_speed" to 67.5,
            "vehicle_count" to 15,
            "average_speed" to 58.3,
            "max_speed" to 89.2,
            "measurement_time" to System.currentTimeMillis()
        )
        
        val dataResult = client.sendData("DEMO_SR001", sensorData)
        if (dataResult.isSuccess) {
            println("✅ Data sent successfully!")
            println("   Timestamp: ${dataResult.getOrNull()}")
        } else {
            println("❌ Data send failed: ${dataResult.exceptionOrNull()?.message}")
        }
        
        // 4. Update controller status
        println("\n🔄 Managing controller status...")
        val onlineResult = client.markOnline("DEMO_SR001")
        if (onlineResult.isSuccess) {
            println("✅ Controller marked as online")
        }
        
        // 5. Get controller information
        println("\n📖 Retrieving controller info...")
        val info = client.getController("DEMO_SR001")
        if (info.isSuccess) {
            val ctrl = info.getOrNull()!!
            println("📄 Controller Details:")
            println("   Name: ${ctrl.name}")
            println("   Serial: ${ctrl.serialNumber}")
            println("   Type: ${ctrl.controllerType}")
            println("   Online: ${ctrl.isOnline}")
            println("   Location: ${ctrl.latitude}, ${ctrl.longitude}")
            println("   Last Seen: ${ctrl.lastSeen}")
        }
        
        // 6. Update controller location
        println("\n✏️ Updating controller location...")
        val locationUpdate = client.updateControllerLocation(
            "DEMO_SR001", 
            52.3700, // Slightly different coordinates
            4.9100
        )
        
        if (locationUpdate.isSuccess) {
            println("✅ Location updated successfully!")
        }
        
        // 7. Send multiple data points
        println("\n📦 Sending batch data...")
        val batchData = listOf(
            mapOf("reading" to 1, "speed" to 45.2),
            mapOf("reading" to 2, "speed" to 52.8),
            mapOf("reading" to 3, "speed" to 38.5)
        )
        
        val batchResult = client.sendDataBatch("DEMO_SR001", batchData)
        if (batchResult.isSuccess) {
            println("✅ Batch data sent: ${batchResult.getOrNull()?.size} readings")
        }
        
        // 8. Check if controller is online
        println("\n🔍 Checking controller status...")
        val isOnline = client.isControllerOnline("DEMO_SR001")
        if (isOnline.isSuccess) {
            println("📊 Controller DEMO_SR001 is ${if (isOnline.getOrNull() == true) "ONLINE" else "OFFLINE"}")
        }
        
        // 9. Demonstrate admin operations (will fail without auth)
        println("\n🔐 Testing admin operations...")
        val allControllers = client.listAllControllers()
        if (allControllers.isFailure) {
            println("ℹ️ Admin operations require authentication")
            println("   To use admin features, call: client.setAuthToken(\"your-token\")")
        } else {
            println("✅ Found ${allControllers.getOrNull()?.size} controllers")
        }
        
        println("\n🎉 Demo completed successfully!")
        println("\nℹ️ To use the client in your own application:")
        println("1. Add the kotlin-client dependency to your project")
        println("2. Create client: val client = LXCloudClient.create(\"http://your-server\")")
        println("3. Connect: client.connect()")
        println("4. Use the various methods to interact with your controllers")
        println("5. Don't forget to disconnect: client.disconnect()")
        
    } catch (e: Exception) {
        println("❌ Error during demo: ${e.message}")
        e.printStackTrace()
    } finally {
        // 10. Cleanup
        println("\n🧹 Disconnecting...")
        client.markOffline("DEMO_SR001")
        client.disconnect()
        println("✅ Disconnected from server")
    }
}