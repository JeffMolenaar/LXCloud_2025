const mysql = require('mysql2/promise');
const logger = require('./logger');

class Database {
  constructor() {
    this.pool = null;
  }

  async initialize() {
    try {
      this.pool = mysql.createPool({
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        user: process.env.DB_USER || 'lxadmin',
        password: process.env.DB_PASSWORD || 'lxadmin',
        database: process.env.DB_NAME || 'lxcloud',
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
      });

      // Test connection
      const connection = await this.pool.getConnection();
      await connection.ping();
      connection.release();

      logger.info('Database pool created successfully');
      
      // Run database migrations
      await this.runMigrations();
      
    } catch (error) {
      logger.error('Database initialization failed:', error);
      throw error;
    }
  }

  async runMigrations() {
    try {
      const connection = await this.pool.getConnection();
      
      // Create users table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS users (
          id INT PRIMARY KEY AUTO_INCREMENT,
          email VARCHAR(255) UNIQUE NOT NULL,
          password VARCHAR(255) NOT NULL,
          name VARCHAR(255) NOT NULL,
          address TEXT,
          role ENUM('user', 'admin') DEFAULT 'user',
          two_fa_enabled BOOLEAN DEFAULT FALSE,
          two_fa_secret VARCHAR(255),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          last_login TIMESTAMP NULL,
          is_active BOOLEAN DEFAULT TRUE
        )
      `);

      // Create controllers table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS controllers (
          id INT PRIMARY KEY AUTO_INCREMENT,
          serial_number VARCHAR(255) UNIQUE NOT NULL,
          type ENUM('speedradar', 'beaufortmeter', 'weatherstation', 'aicamera') NOT NULL,
          name VARCHAR(255),
          user_id INT NULL,
          latitude DECIMAL(10, 8) NULL,
          longitude DECIMAL(11, 8) NULL,
          status ENUM('online', 'offline') DEFAULT 'offline',
          last_seen TIMESTAMP NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          config JSON,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
      `);

      // Create controller_data table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS controller_data (
          id INT PRIMARY KEY AUTO_INCREMENT,
          controller_id INT NOT NULL,
          data JSON NOT NULL,
          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (controller_id) REFERENCES controllers(id) ON DELETE CASCADE,
          INDEX idx_controller_timestamp (controller_id, timestamp),
          INDEX idx_timestamp (timestamp)
        )
      `);

      // Create sessions table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS sessions (
          session_id VARCHAR(128) PRIMARY KEY,
          expires INT NOT NULL,
          data MEDIUMTEXT
        )
      `);

      // Create ui_customizations table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS ui_customizations (
          id INT PRIMARY KEY AUTO_INCREMENT,
          page VARCHAR(255) NOT NULL,
          css_content TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY unique_page (page)
        )
      `);

      // Create addons table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS addons (
          id INT PRIMARY KEY AUTO_INCREMENT,
          name VARCHAR(255) NOT NULL,
          version VARCHAR(50) NOT NULL,
          description TEXT,
          config JSON,
          is_active BOOLEAN DEFAULT TRUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
      `);

      // Create dashboard_cards table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS dashboard_cards (
          id INT PRIMARY KEY AUTO_INCREMENT,
          user_id INT NOT NULL,
          card_type VARCHAR(100) NOT NULL,
          position_x INT DEFAULT 0,
          position_y INT DEFAULT 0,
          width INT DEFAULT 1,
          height INT DEFAULT 1,
          config JSON,
          is_visible BOOLEAN DEFAULT TRUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Create system_settings table
      await connection.execute(`
        CREATE TABLE IF NOT EXISTS system_settings (
          id INT PRIMARY KEY AUTO_INCREMENT,
          setting_key VARCHAR(255) UNIQUE NOT NULL,
          setting_value TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
      `);

      connection.release();
      logger.info('Database migrations completed successfully');
      
    } catch (error) {
      logger.error('Database migration failed:', error);
      throw error;
    }
  }

  async query(sql, params = []) {
    try {
      const [rows] = await this.pool.execute(sql, params);
      return rows;
    } catch (error) {
      logger.error('Database query error:', error);
      throw error;
    }
  }

  async transaction(callback) {
    const connection = await this.pool.getConnection();
    try {
      await connection.beginTransaction();
      const result = await callback(connection);
      await connection.commit();
      return result;
    } catch (error) {
      await connection.rollback();
      throw error;
    } finally {
      connection.release();
    }
  }

  async close() {
    if (this.pool) {
      await this.pool.end();
      logger.info('Database connection pool closed');
    }
  }
}

const database = new Database();
module.exports = database;