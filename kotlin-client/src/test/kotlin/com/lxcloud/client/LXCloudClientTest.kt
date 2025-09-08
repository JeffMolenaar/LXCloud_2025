package com.lxcloud.client

import com.lxcloud.client.models.ControllerType
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Before
import org.junit.Test
import kotlin.test.assertTrue
import kotlin.test.assertFalse
import kotlin.test.assertEquals

class LXCloudClientTest {
    
    private lateinit var mockServer: MockWebServer
    private lateinit var client: LXCloudClient
    
    @Before
    fun setUp() {
        mockServer = MockWebServer()
        mockServer.start()
        val baseUrl = mockServer.url("/").toString().trimEnd('/')
        client = LXCloudClient(baseUrl, enableLogging = true)
    }
    
    @After
    fun tearDown() {
        client.close()
        mockServer.shutdown()
    }
    
    @Test
    fun `test connect method handles connection successfully`() = runBlocking {
        // Mock response for debug endpoint
        mockServer.enqueue(MockResponse()
            .setResponseCode(404)
            .setBody("""{"error": "Method not allowed. debug is a reserved endpoint."}"""))
        
        val result = client.connect()
        assertTrue(result.isSuccess)
        assertTrue(client.isConnected())
    }
    
    @Test
    fun `test register controller successfully`() = runBlocking {
        val mockResponse = """
            {
                "message": "Controller registered successfully",
                "controller": {
                    "id": 1,
                    "serial_number": "TEST123",
                    "controller_type": "speedradar",
                    "name": "Test Controller",
                    "is_online": true,
                    "latitude": 51.5,
                    "longitude": 4.8
                }
            }
        """.trimIndent()
        
        mockServer.enqueue(MockResponse()
            .setResponseCode(201)
            .setBody(mockResponse)
            .addHeader("Content-Type", "application/json"))
        
        val result = client.registerController(
            serialNumber = "TEST123",
            type = ControllerType.SPEED_RADAR,
            name = "Test Controller",
            latitude = 51.5,
            longitude = 4.8
        )
        
        assertTrue(result.isSuccess)
        val controller = result.getOrNull()!!
        assertEquals("TEST123", controller.serialNumber)
        assertEquals(ControllerType.SPEED_RADAR, controller.controllerType)
        assertEquals("Test Controller", controller.name)
        assertTrue(controller.isOnline)
    }
    
    @Test
    fun `test send data successfully`() = runBlocking {
        val mockResponse = """
            {
                "message": "Data updated successfully",
                "timestamp": "2024-01-01T12:00:00"
            }
        """.trimIndent()
        
        mockServer.enqueue(MockResponse()
            .setResponseCode(200)
            .setBody(mockResponse)
            .addHeader("Content-Type", "application/json"))
        
        val data: Map<String, Any?> = mapOf(
            "speed" to 45.5,
            "temperature" to 20.3,
            "humidity" to 65
        )
        
        val result = client.sendData("TEST123", data)
        
        if (result.isFailure) {
            println("Send data failed: ${result.exceptionOrNull()?.message}")
        }
        assertTrue(result.isSuccess)
        assertEquals("2024-01-01T12:00:00", result.getOrNull())
    }
    
    @Test
    fun `test mark controller online`() = runBlocking {
        val mockResponse = """
            {
                "message": "Status updated successfully",
                "status": "online"
            }
        """.trimIndent()
        
        mockServer.enqueue(MockResponse()
            .setResponseCode(200)
            .setBody(mockResponse)
            .addHeader("Content-Type", "application/json"))
        
        val result = client.markOnline("TEST123")
        
        assertTrue(result.isSuccess)
        assertEquals("online", result.getOrNull())
    }
    
    @Test
    fun `test get controller info`() = runBlocking {
        val mockResponse = """
            {
                "controller": {
                    "id": 1,
                    "serial_number": "TEST123",
                    "controller_type": "weatherstation",
                    "name": "Weather Station 1",
                    "is_online": false,
                    "latitude": 52.1,
                    "longitude": 5.2
                }
            }
        """.trimIndent()
        
        mockServer.enqueue(MockResponse()
            .setResponseCode(200)
            .setBody(mockResponse)
            .addHeader("Content-Type", "application/json"))
        
        val result = client.getController("TEST123")
        
        assertTrue(result.isSuccess)
        val controller = result.getOrNull()!!
        assertEquals("TEST123", controller.serialNumber)
        assertEquals(ControllerType.WEATHER_STATION, controller.controllerType)
        assertFalse(controller.isOnline)
    }
    
    @Test
    fun `test error handling for failed registration`() = runBlocking {
        val mockResponse = """
            {
                "error": "Invalid controller type"
            }
        """.trimIndent()
        
        mockServer.enqueue(MockResponse()
            .setResponseCode(400)
            .setBody(mockResponse)
            .addHeader("Content-Type", "application/json"))
        
        val result = client.registerController(
            serialNumber = "TEST123",
            type = ControllerType.SPEED_RADAR
        )
        
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()?.message?.contains("Invalid controller type") == true)
    }
    
    @Test
    fun `test disconnect cleans up resources`() {
        assertTrue(client.isConnected() || !client.isConnected()) // Initial state
        client.disconnect()
        assertFalse(client.isConnected())
    }
    
    @Test
    fun `test authentication requirement for admin operations`() = runBlocking {
        val result = client.listAllControllers()
        
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()?.message?.contains("Authentication required") == true)
    }
    
    @Test
    fun `test register and activate controller`() = runBlocking {
        // Mock registration response
        mockServer.enqueue(MockResponse()
            .setResponseCode(201)
            .setBody("""
                {
                    "message": "Controller registered successfully",
                    "controller": {
                        "id": 1,
                        "serial_number": "TEST123",
                        "controller_type": "speedradar",
                        "name": "Test Controller",
                        "is_online": true
                    }
                }
            """.trimIndent())
            .addHeader("Content-Type", "application/json"))
        
        // Mock status update response
        mockServer.enqueue(MockResponse()
            .setResponseCode(200)
            .setBody("""
                {
                    "message": "Status updated successfully",
                    "status": "online"
                }
            """.trimIndent())
            .addHeader("Content-Type", "application/json"))
        
        val result = client.registerAndActivateController(
            serialNumber = "TEST123",
            type = ControllerType.SPEED_RADAR,
            name = "Test Controller"
        )
        
        assertTrue(result.isSuccess)
        val controller = result.getOrNull()!!
        assertEquals("TEST123", controller.serialNumber)
        assertTrue(controller.isOnline)
    }
}