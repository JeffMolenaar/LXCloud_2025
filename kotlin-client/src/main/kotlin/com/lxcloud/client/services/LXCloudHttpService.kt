package com.lxcloud.client.services

import com.lxcloud.client.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * HTTP service for communicating with LXCloud API
 */
class LXCloudHttpService(
    private val baseUrl: String,
    private val enableLogging: Boolean = false,
    private val connectTimeoutSeconds: Long = 30,
    private val readTimeoutSeconds: Long = 30
) {
    
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }
    
    private val client: OkHttpClient by lazy {
        val builder = OkHttpClient.Builder()
            .connectTimeout(connectTimeoutSeconds, TimeUnit.SECONDS)
            .readTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
            .writeTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
        
        if (enableLogging) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            builder.addInterceptor(loggingInterceptor)
        }
        
        builder.build()
    }
    
    private val mediaTypeJson = "application/json".toMediaType()
    
    /**
     * Register a new controller or update existing one
     */
    suspend fun registerController(request: ControllerRegistrationRequest): Result<Controller> {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = json.encodeToString(request).toRequestBody(mediaTypeJson)
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/register")
                    .post(requestBody)
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                    apiResponse.controller?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("No controller data in response"))
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Send sensor data from controller
     */
    suspend fun sendControllerData(serialNumber: String, data: Map<String, Any?>): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = json.encodeToString(data).toRequestBody(mediaTypeJson)
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/$serialNumber/data")
                    .post(requestBody)
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<String>>(responseBody)
                    Result.success(apiResponse.timestamp ?: "Data sent successfully")
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<String>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Update controller online/offline status
     */
    suspend fun updateControllerStatus(serialNumber: String, online: Boolean): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val request = StatusUpdateRequest(online)
                val requestBody = json.encodeToString(request).toRequestBody(mediaTypeJson)
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/$serialNumber/status")
                    .post(requestBody)
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<String>>(responseBody)
                    Result.success(apiResponse.status ?: "Status updated successfully")
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<String>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get controller information
     */
    suspend fun getController(serialNumber: String): Result<Controller> {
        return withContext(Dispatchers.IO) {
            try {
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/$serialNumber")
                    .get()
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                    apiResponse.controller?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("No controller data in response"))
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Modify controller configuration
     */
    suspend fun modifyController(serialNumber: String, updates: Map<String, Any?>): Result<Controller> {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = json.encodeToString(updates).toRequestBody(mediaTypeJson)
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/$serialNumber")
                    .put(requestBody)
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                    apiResponse.controller?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("No controller data in response"))
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * List all controllers (requires authentication)
     */
    suspend fun listControllers(authToken: String? = null): Result<List<Controller>> {
        return withContext(Dispatchers.IO) {
            try {
                val requestBuilder = Request.Builder()
                    .url("$baseUrl/api/controllers/list")
                    .get()
                
                // Add authentication header if provided
                authToken?.let {
                    requestBuilder.addHeader("Authorization", "Bearer $it")
                }
                
                val httpRequest = requestBuilder.build()
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val apiResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                    apiResponse.controllers?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("No controllers data in response"))
                } else {
                    val errorMessage = if (responseBody != null) {
                        try {
                            val errorResponse = json.decodeFromString<ApiResponse<Controller>>(responseBody)
                            errorResponse.error ?: "Unknown error"
                        } catch (e: Exception) {
                            responseBody
                        }
                    } else {
                        "HTTP ${response.code}: ${response.message}"
                    }
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get controller status information (requires authentication)
     */
    suspend fun getControllerStatus(authToken: String): Result<List<Controller>> {
        return withContext(Dispatchers.IO) {
            try {
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/controllers/status")
                    .addHeader("Authorization", "Bearer $authToken")
                    .get()
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val controllers = json.decodeFromString<List<Controller>>(responseBody)
                    Result.success(controllers)
                } else {
                    val errorMessage = responseBody ?: "HTTP ${response.code}: ${response.message}"
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get system statistics (requires authentication)
     */
    suspend fun getStatsOverview(authToken: String): Result<StatsOverview> {
        return withContext(Dispatchers.IO) {
            try {
                val httpRequest = Request.Builder()
                    .url("$baseUrl/api/stats/overview")
                    .addHeader("Authorization", "Bearer $authToken")
                    .get()
                    .build()
                
                val response = client.newCall(httpRequest).execute()
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    val stats = json.decodeFromString<StatsOverview>(responseBody)
                    Result.success(stats)
                } else {
                    val errorMessage = responseBody ?: "HTTP ${response.code}: ${response.message}"
                    Result.failure(Exception(errorMessage))
                }
            } catch (e: IOException) {
                Result.failure(e)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Close the HTTP client and cleanup resources
     */
    fun close() {
        client.dispatcher.executorService.shutdown()
        client.connectionPool.evictAll()
    }
}