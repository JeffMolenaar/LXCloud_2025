const database = require('../config/database');

describe('Database Configuration', () => {
  
  afterEach(() => {
    if (database && database.pool) {
      database.close();
    }
  });

  test('should not include deprecated MySQL2 options', async () => {
    // Mock the mysql.createPool to capture the config
    const mysql = require('mysql2/promise');
    const originalCreatePool = mysql.createPool;
    let capturedConfig;
    
    mysql.createPool = (config) => {
      capturedConfig = config;
      // Return a mock pool that throws on connection attempts
      return {
        getConnection: () => Promise.reject(new Error('ECONNREFUSED')),
        end: () => Promise.resolve()
      };
    };

    try {
      await database.initialize();
    } catch (error) {
      // Expected to fail due to no MySQL server
    }

    // Restore original function
    mysql.createPool = originalCreatePool;

    // Check that deprecated options are not present
    expect(capturedConfig).toBeDefined();
    expect(capturedConfig.acquireTimeout).toBeUndefined();
    expect(capturedConfig.timeout).toBeUndefined(); 
    expect(capturedConfig.reconnect).toBeUndefined();
  });

  test('should use only valid MySQL2 configuration options', async () => {
    const mysql = require('mysql2/promise');
    const originalCreatePool = mysql.createPool;
    let capturedConfig;
    
    mysql.createPool = (config) => {
      capturedConfig = config;
      // Return a mock pool that throws on connection attempts
      return {
        getConnection: () => Promise.reject(new Error('ECONNREFUSED')),
        end: () => Promise.resolve()
      };
    };

    try {
      await database.initialize();
    } catch (error) {
      // Expected to fail due to no MySQL server
    }

    // Restore original function
    mysql.createPool = originalCreatePool;

    // Check that only valid options are present
    const validOptions = [
      'host', 'port', 'user', 'password', 'database', 'charset',
      'waitForConnections', 'connectionLimit', 'queueLimit', 'idleTimeout'
    ];
    
    Object.keys(capturedConfig).forEach(option => {
      expect(validOptions).toContain(option);
    });
  });

  test('should fall back to mock mode in development when database connection fails', async () => {
    const originalNodeEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    // Reset database state
    database.mockMode = false;
    database.pool = null;

    await database.initialize();

    expect(database.mockMode).toBe(true);
    expect(database.mockUsers).toBeDefined();
    expect(database.mockControllers).toBeDefined();

    // Restore original NODE_ENV
    process.env.NODE_ENV = originalNodeEnv;
  });
});