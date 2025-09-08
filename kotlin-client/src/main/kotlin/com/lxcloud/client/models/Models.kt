package com.lxcloud.client.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Represents a controller device in the LXCloud system
 */
@Serializable
data class Controller(
    val id: Int? = null,
    @SerialName("serial_number")
    val serialNumber: String,
    @SerialName("controller_type")
    val controllerType: ControllerType,
    val name: String? = null,
    @SerialName("user_id")
    val userId: Int? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @SerialName("is_online")
    val isOnline: Boolean = false,
    @SerialName("last_seen")
    val lastSeen: String? = null,
    @SerialName("timeout_seconds")
    val timeoutSeconds: Int? = null,
    @SerialName("created_at")
    val createdAt: String? = null
)

/**
 * Supported controller types
 */
@Serializable
enum class ControllerType {
    @SerialName("speedradar")
    SPEED_RADAR,
    
    @SerialName("beaufortmeter")
    BEAUFORT_METER,
    
    @SerialName("weatherstation")
    WEATHER_STATION,
    
    @SerialName("aicamera")
    AI_CAMERA
}

/**
 * Request model for controller registration
 */
@Serializable
data class ControllerRegistrationRequest(
    @SerialName("serial_number")
    val serialNumber: String,
    val type: ControllerType,
    val name: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @SerialName("timeout_seconds")
    val timeoutSeconds: Int? = null
)

/**
 * Controller data point for sensor readings
 */
@Serializable
data class ControllerData(
    val timestamp: String? = null,
    val data: Map<String, kotlinx.serialization.json.JsonElement>
)

/**
 * Request for updating controller status
 */
@Serializable
data class StatusUpdateRequest(
    val online: Boolean = true
)

/**
 * Response wrapper for API responses
 */
@Serializable
data class ApiResponse<T>(
    val message: String? = null,
    val error: String? = null,
    val controller: T? = null,
    val controllers: List<T>? = null,
    val total: Int? = null,
    val timestamp: String? = null,
    val status: String? = null
)

/**
 * Controller statistics overview
 */
@Serializable
data class StatsOverview(
    @SerialName("total_controllers")
    val totalControllers: Int,
    @SerialName("online_controllers")
    val onlineControllers: Int,
    @SerialName("offline_controllers")
    val offlineControllers: Int,
    @SerialName("total_users")
    val totalUsers: Int? = null,
    @SerialName("unbound_controllers")
    val unboundControllers: Int? = null
)

/**
 * System status information
 */
@Serializable
data class SystemStatus(
    @SerialName("mqtt_service")
    val mqttService: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    @SerialName("controller_status_service")
    val controllerStatusService: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val version: String? = null
)