package com.lxcloud.client

import com.lxcloud.client.models.*
import com.lxcloud.client.services.LXCloudHttpService
import kotlinx.coroutines.*

/**
 * Main client class for easy connecting and disconnecting to the LXCloud server API.
 * This class provides high-level methods to interact with the LXCloud system.
 */
class LXCloudClient(
    baseUrl: String,
    enableLogging: Boolean = false,
    connectTimeoutSeconds: Long = 30,
    readTimeoutSeconds: Long = 30
) : AutoCloseable {
    
    private val httpService = LXCloudHttpService(
        baseUrl = baseUrl.trimEnd('/'),
        enableLogging = enableLogging,
        connectTimeoutSeconds = connectTimeoutSeconds,
        readTimeoutSeconds = readTimeoutSeconds
    )
    
    private var authToken: String? = null
    private var isConnected = false
    
    /**
     * Test connection to the server
     */
    suspend fun connect(): Result<Boolean> {
        return try {
            // Test connection by calling the debug endpoint
            val result = httpService.getController("debug")
            isConnected = result.isSuccess || result.exceptionOrNull()?.message?.contains("debug") == true
            Result.success(isConnected)
        } catch (e: Exception) {
            isConnected = false
            Result.failure(e)
        }
    }
    
    /**
     * Disconnect from the server and cleanup resources
     */
    fun disconnect() {
        isConnected = false
        authToken = null
        httpService.close()
    }
    
    /**
     * Set authentication token for admin operations
     */
    fun setAuthToken(token: String) {
        this.authToken = token
    }
    
    /**
     * Check if client is connected
     */
    fun isConnected(): Boolean = isConnected
    
    // ============ Controller Operations ============
    
    /**
     * Register a new controller or update existing one
     */
    suspend fun registerController(
        serialNumber: String,
        type: ControllerType,
        name: String? = null,
        latitude: Double? = null,
        longitude: Double? = null,
        timeoutSeconds: Int? = null
    ): Result<Controller> {
        val request = ControllerRegistrationRequest(
            serialNumber = serialNumber,
            type = type,
            name = name,
            latitude = latitude,
            longitude = longitude,
            timeoutSeconds = timeoutSeconds
        )
        return httpService.registerController(request)
    }
    
    /**
     * Send sensor data from a controller
     */
    suspend fun sendData(serialNumber: String, data: Map<String, Any?>): Result<String> {
        return httpService.sendControllerData(serialNumber, data)
    }
    
    /**
     * Send sensor data with additional location information
     */
    suspend fun sendDataWithLocation(
        serialNumber: String,
        data: Map<String, Any?>,
        latitude: Double? = null,
        longitude: Double? = null
    ): Result<String> {
        val fullData = buildMap<String, Any?> {
            putAll(data)
            latitude?.let { put("latitude", it) }
            longitude?.let { put("longitude", it) }
        }
        return httpService.sendControllerData(serialNumber, fullData)
    }
    
    /**
     * Mark controller as online
     */
    suspend fun markOnline(serialNumber: String): Result<String> {
        return httpService.updateControllerStatus(serialNumber, true)
    }
    
    /**
     * Mark controller as offline
     */
    suspend fun markOffline(serialNumber: String): Result<String> {
        return httpService.updateControllerStatus(serialNumber, false)
    }
    
    /**
     * Get controller information
     */
    suspend fun getController(serialNumber: String): Result<Controller> {
        return httpService.getController(serialNumber)
    }
    
    /**
     * Modify controller configuration
     */
    suspend fun updateControllerName(serialNumber: String, name: String): Result<Controller> {
        return httpService.modifyController(serialNumber, mapOf("name" to name))
    }
    
    /**
     * Update controller location
     */
    suspend fun updateControllerLocation(
        serialNumber: String,
        latitude: Double,
        longitude: Double
    ): Result<Controller> {
        return httpService.modifyController(
            serialNumber,
            mapOf("latitude" to latitude, "longitude" to longitude)
        )
    }
    
    /**
     * Update controller type
     */
    suspend fun updateControllerType(
        serialNumber: String,
        type: ControllerType
    ): Result<Controller> {
        return httpService.modifyController(serialNumber, mapOf("type" to type.name.lowercase()))
    }
    
    /**
     * Update controller timeout
     */
    suspend fun updateControllerTimeout(
        serialNumber: String,
        timeoutSeconds: Int?
    ): Result<Controller> {
        return httpService.modifyController(
            serialNumber,
            mapOf("timeout_seconds" to timeoutSeconds)
        )
    }
    
    // ============ Admin Operations (require authentication) ============
    
    /**
     * List all controllers (requires authentication)
     */
    suspend fun listAllControllers(): Result<List<Controller>> {
        val token = authToken ?: return Result.failure(Exception("Authentication required"))
        return httpService.listControllers(token)
    }
    
    /**
     * Get controller status information (requires authentication)
     */
    suspend fun getControllerStatus(): Result<List<Controller>> {
        val token = authToken ?: return Result.failure(Exception("Authentication required"))
        return httpService.getControllerStatus(token)
    }
    
    /**
     * Get system statistics (requires authentication)
     */
    suspend fun getSystemStats(): Result<StatsOverview> {
        val token = authToken ?: return Result.failure(Exception("Authentication required"))
        return httpService.getStatsOverview(token)
    }
    
    // ============ Convenience Methods ============
    
    /**
     * Register and immediately mark a controller as online
     */
    suspend fun registerAndActivateController(
        serialNumber: String,
        type: ControllerType,
        name: String? = null,
        latitude: Double? = null,
        longitude: Double? = null,
        timeoutSeconds: Int? = null
    ): Result<Controller> {
        val registrationResult = registerController(
            serialNumber, type, name, latitude, longitude, timeoutSeconds
        )
        
        if (registrationResult.isSuccess) {
            // Mark as online after successful registration
            markOnline(serialNumber)
        }
        
        return registrationResult
    }
    
    /**
     * Send multiple data points in sequence
     */
    suspend fun sendDataBatch(
        serialNumber: String,
        dataPoints: List<Map<String, Any?>>
    ): Result<List<String>> {
        val results = mutableListOf<String>()
        
        for (data in dataPoints) {
            val result = sendData(serialNumber, data)
            if (result.isSuccess) {
                results.add(result.getOrNull() ?: "Success")
            } else {
                return Result.failure(result.exceptionOrNull() ?: Exception("Batch send failed"))
            }
        }
        
        return Result.success(results)
    }
    
    /**
     * Check if a controller exists and is online
     */
    suspend fun isControllerOnline(serialNumber: String): Result<Boolean> {
        return getController(serialNumber).map { controller ->
            controller.isOnline
        }
    }
    
    /**
     * Get all controllers of a specific type (requires authentication)
     */
    suspend fun getControllersByType(type: ControllerType): Result<List<Controller>> {
        return listAllControllers().map { controllers ->
            controllers.filter { it.controllerType == type }
        }
    }
    
    /**
     * Get all online controllers (requires authentication)
     */
    suspend fun getOnlineControllers(): Result<List<Controller>> {
        return listAllControllers().map { controllers ->
            controllers.filter { it.isOnline }
        }
    }
    
    /**
     * AutoCloseable implementation
     */
    override fun close() {
        disconnect()
    }
    
    companion object {
        /**
         * Create a new LXCloudClient with default settings
         */
        fun create(baseUrl: String, enableLogging: Boolean = false): LXCloudClient {
            return LXCloudClient(baseUrl, enableLogging)
        }
        
        /**
         * Create a new LXCloudClient with authentication
         */
        fun createAuthenticated(
            baseUrl: String,
            authToken: String,
            enableLogging: Boolean = false
        ): LXCloudClient {
            return LXCloudClient(baseUrl, enableLogging).apply {
                setAuthToken(authToken)
            }
        }
    }
}