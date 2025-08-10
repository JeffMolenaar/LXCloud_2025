/**
 * Centralized configuration management
 */
require('dotenv').config();

class Config {
  constructor() {
    this.env = process.env.NODE_ENV || 'development';
    this.isDevelopment = this.env === 'development';
    this.isProduction = this.env === 'production';
    this.isTest = this.env === 'test';
  }

  // Server configuration
  get server() {
    return {
      port: parseInt(process.env.PORT) || 3000,
      host: process.env.HOST || '0.0.0.0',
      trustProxy: process.env.TRUST_PROXY === 'true'
    };
  }

  // Database configuration
  get database() {
    return {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT) || 3306,
      user: process.env.DB_USER || 'lxcloud',
      password: process.env.DB_PASSWORD || 'lxcloud',
      name: process.env.DB_NAME || 'lxcloud',
      connectionLimit: parseInt(process.env.DB_CONNECTION_LIMIT) || 10,
      charset: process.env.DB_CHARSET || 'utf8mb4'
    };
  }

  // Authentication configuration
  get auth() {
    return {
      jwtSecret: process.env.JWT_SECRET || 'your-jwt-secret',
      jwtExpiresIn: process.env.JWT_EXPIRES_IN || '15m',
      jwtRefreshSecret: process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET || 'your-refresh-secret',
      jwtRefreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
      sessionSecret: process.env.SESSION_SECRET || 'your-session-secret',
      bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS) || 12,
      maxLoginAttempts: parseInt(process.env.MAX_LOGIN_ATTEMPTS) || 5,
      lockTimeMinutes: parseInt(process.env.LOCK_TIME_MINUTES) || 15,
      sessionMaxAge: parseInt(process.env.SESSION_MAX_AGE) || 24 * 60 * 60 * 1000, // 24 hours
      rememberMeMaxAge: parseInt(process.env.REMEMBER_ME_MAX_AGE) || 30 * 24 * 60 * 60 * 1000 // 30 days
    };
  }

  // MQTT configuration
  get mqtt() {
    return {
      brokerUrl: process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883',
      username: process.env.MQTT_USERNAME || 'lxcloud_mqtt',
      password: process.env.MQTT_PASSWORD || '',
      clientId: process.env.MQTT_CLIENT_ID || 'lxcloud_server',
      keepalive: parseInt(process.env.MQTT_KEEPALIVE) || 60,
      reconnectPeriod: parseInt(process.env.MQTT_RECONNECT_PERIOD) || 5000
    };
  }

  // Security configuration
  get security() {
    return {
      enableCors: process.env.ENABLE_CORS !== 'false',
      allowedOrigins: this.parseStringArray(process.env.ALLOWED_ORIGINS) || [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://192.168.2.171:3000'
      ],
      rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
      rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX) || 100,
      loginRateLimitWindowMs: parseInt(process.env.LOGIN_RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
      loginRateLimitMax: parseInt(process.env.LOGIN_RATE_LIMIT_MAX) || 5,
      forceHttps: process.env.FORCE_HTTPS === 'true',
      forceHttp: process.env.FORCE_HTTP === 'true',
      enableHsts: process.env.ENABLE_HSTS === 'true'
    };
  }

  // Logging configuration
  get logging() {
    return {
      level: process.env.LOG_LEVEL || (this.isDevelopment ? 'debug' : 'info'),
      file: process.env.LOG_FILE || 'logs/lxcloud.log',
      maxSize: process.env.LOG_MAX_SIZE || '10m',
      maxFiles: parseInt(process.env.LOG_MAX_FILES) || 5,
      enableConsole: process.env.LOG_CONSOLE !== 'false',
      enableFile: process.env.LOG_FILE_ENABLED === 'true'
    };
  }

  // Application features
  get features() {
    return {
      enableRegistration: process.env.ENABLE_REGISTRATION !== 'false',
      enableTwoFA: process.env.ENABLE_2FA !== 'false',
      enableMQTT: process.env.ENABLE_MQTT !== 'false',
      enableWebSockets: process.env.ENABLE_WEBSOCKETS !== 'false',
      enableEmailVerification: process.env.ENABLE_EMAIL_VERIFICATION === 'true',
      enablePasswordReset: process.env.ENABLE_PASSWORD_RESET === 'true'
    };
  }

  // Email configuration (for future password reset feature)
  get email() {
    return {
      host: process.env.EMAIL_HOST || '',
      port: parseInt(process.env.EMAIL_PORT) || 587,
      secure: process.env.EMAIL_SECURE === 'true',
      user: process.env.EMAIL_USER || '',
      password: process.env.EMAIL_PASSWORD || '',
      from: process.env.EMAIL_FROM || 'noreply@lxcloud.local'
    };
  }

  // Application info
  get app() {
    return {
      name: 'LXCloud',
      version: process.env.npm_package_version || '1.0.0',
      description: 'IoT Controller Management Platform'
    };
  }

  // Utility methods
  parseStringArray(str) {
    if (!str) return null;
    return str.split(',').map(s => s.trim()).filter(s => s.length > 0);
  }

  get(key) {
    const keys = key.split('.');
    let value = this;
    
    for (const k of keys) {
      value = value[k];
      if (value === undefined) return undefined;
    }
    
    return value;
  }

  // Validate required configuration
  validate() {
    const errors = [];

    if (this.isProduction) {
      if (!process.env.JWT_SECRET || process.env.JWT_SECRET === 'your-jwt-secret') {
        errors.push('JWT_SECRET must be set in production');
      }
      
      if (!process.env.SESSION_SECRET || process.env.SESSION_SECRET === 'your-session-secret') {
        errors.push('SESSION_SECRET must be set in production');
      }
      
      if (this.auth.bcryptRounds < 12) {
        errors.push('BCRYPT_ROUNDS should be at least 12 in production');
      }
    }

    if (errors.length > 0) {
      throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
    }

    return true;
  }

  // Get environment-specific defaults
  getDefaults() {
    const defaults = {
      development: {
        LOG_LEVEL: 'debug',
        LOG_CONSOLE: 'true',
        ENABLE_2FA: 'true',
        BCRYPT_ROUNDS: '10' // Faster for development
      },
      production: {
        LOG_LEVEL: 'info',
        LOG_CONSOLE: 'false',
        LOG_FILE_ENABLED: 'true',
        ENABLE_HSTS: 'true',
        BCRYPT_ROUNDS: '12'
      },
      test: {
        LOG_LEVEL: 'error',
        LOG_CONSOLE: 'false',
        BCRYPT_ROUNDS: '4' // Faster for tests
      }
    };

    return defaults[this.env] || {};
  }

  // Apply environment defaults if not set
  applyDefaults() {
    const defaults = this.getDefaults();
    
    for (const [key, value] of Object.entries(defaults)) {
      if (!process.env[key]) {
        process.env[key] = value;
      }
    }
  }
}

// Create and export singleton instance
const config = new Config();

// Apply environment defaults
config.applyDefaults();

// Validate configuration in production
if (config.isProduction) {
  config.validate();
}

module.exports = config;