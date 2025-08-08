const mysql = require('mysql2/promise');
const logger = require('./logger');

class Database {
  constructor() {
    this.pool = null;
    this.mockMode = false;
    this.mockUsers = null;
    this.mockControllers = null;
    this.mockData = null;
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
        queueLimit: 0,
        acquireTimeout: 10000,
        timeout: 10000
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
      
      // If we're in development mode and can't connect to MySQL, 
      // set up a mock database to allow the application to start
      if (process.env.NODE_ENV === 'development') {
        logger.warn('Falling back to mock database for development');
        this.setupMockDatabase();
        return;
      }
      
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

  setupMockDatabase() {
    // Create an in-memory mock database for development
    this.mockMode = true;
    this.mockUsers = new Map();
    this.mockControllers = new Map();
    this.mockData = new Map();
    
    // Create a default admin user for testing
    const bcrypt = require('bcryptjs');
    const adminHash = bcrypt.hashSync('admin123', 12);
    
    this.mockUsers.set(1, {
      id: 1,
      email: 'admin@lxcloud.local',
      password: adminHash,
      name: 'Administrator',
      address: null,
      role: 'admin',
      two_fa_enabled: false,
      two_fa_secret: null,
      created_at: new Date(),
      updated_at: new Date(),
      last_login: null,
      is_active: true
    });
    
    logger.info('Mock database initialized with default admin user (admin@lxcloud.local / admin123)');
  }

  async query(sql, params = []) {
    if (this.mockMode) {
      return this.mockQuery(sql, params);
    }
    
    try {
      const [rows] = await this.pool.execute(sql, params);
      return rows;
    } catch (error) {
      logger.error('Database query error:', error);
      throw error;
    }
  }

  mockQuery(sql, params = []) {
    // Basic mock implementation for common queries
    const lowerSql = sql.toLowerCase().trim();
    
    if (lowerSql.includes('select * from users where email = ?')) {
      const email = params[0];
      for (const user of this.mockUsers.values()) {
        if (user.email === email && user.is_active) {
          return [user];
        }
      }
      return [];
    }
    
    if (lowerSql.includes('select * from users where id = ?')) {
      const id = parseInt(params[0]);
      const user = this.mockUsers.get(id);
      return user && user.is_active ? [user] : [];
    }
    
    if (lowerSql.includes('select password from users where id = ?')) {
      const id = parseInt(params[0]);
      const user = this.mockUsers.get(id);
      return user ? [{ password: user.password }] : [];
    }
    
    if (lowerSql.includes('update users set last_login = now() where id = ?')) {
      const id = parseInt(params[0]);
      const user = this.mockUsers.get(id);
      if (user) {
        user.last_login = new Date();
        this.mockUsers.set(id, user);
      }
      return { affectedRows: user ? 1 : 0 };
    }
    
    if (lowerSql.includes('insert into users')) {
      // Simple mock insert for user creation
      const newId = Math.max(...this.mockUsers.keys(), 0) + 1;
      return { insertId: newId };
    }
    
    // Mock controller queries for dashboard
    if (lowerSql.includes('select * from controllers where user_id = ?')) {
      return []; // Return empty array for now
    }
    
    if (lowerSql.includes('select count(*) as count from controllers')) {
      return [{ count: 0 }]; // Mock controller counts
    }
    
    if (lowerSql.includes('select count(*) as count from controllers where status = \'online\'')) {
      return [{ count: 0 }];
    }
    
    if (lowerSql.includes('select count(*) as count from controllers where user_id is not null')) {
      return [{ count: 0 }];
    }
    
    if (lowerSql.includes('select * from dashboard_cards where user_id = ?')) {
      return []; // Return empty dashboard cards
    }
    
    // For other queries, return empty result
    logger.warn(`Mock query not implemented: ${sql}`);
    return [];
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
    if (this.mockMode) {
      logger.info('Mock database closed');
      return;
    }
    
    if (this.pool) {
      await this.pool.end();
      logger.info('Database connection pool closed');
    }
  }
}

const database = new Database();
module.exports = database;