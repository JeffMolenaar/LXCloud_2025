#!/usr/bin/env node

// Simple test script to verify database connection with lxcloud user
const database = require('../config/database');

console.log('Testing database connection with lxcloud user...');
console.log('Database configuration:');
console.log(`  Host: ${process.env.DB_HOST || 'localhost'}`);
console.log(`  Port: ${process.env.DB_PORT || 3306}`);
console.log(`  User: ${process.env.DB_USER || 'lxcloud'}`);
console.log(`  Database: ${process.env.DB_NAME || 'lxcloud'}`);
console.log('');

async function testConnection() {
  try {
    await database.initialize();
    console.log('✅ Database connection successful!');
    console.log('✅ Database tables created/verified successfully!');
    
    // Test a simple query
    const result = await database.query('SELECT 1 as test');
    console.log('✅ Database query test successful:', result);
    
    await database.close();
    console.log('✅ Database connection closed properly');
    
    process.exit(0);
  } catch (error) {
    console.error('❌ Database connection failed:', error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('');
      console.log('The database server is not running or not accessible.');
      console.log('Please ensure MySQL/MariaDB is installed and running.');
    } else if (error.code === 'ER_ACCESS_DENIED_ERROR' || error.errno === 1698) {
      console.log('');
      console.log('Access denied - please run the database setup script:');
      console.log('npm run setup-db');
      console.log('Or manually create database with:');
      console.log('sudo mysql -e "CREATE DATABASE IF NOT EXISTS lxcloud; CREATE USER IF NOT EXISTS \'lxcloud\'@\'localhost\' IDENTIFIED BY \'lxcloud\'; GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxcloud\'@\'localhost\'; FLUSH PRIVILEGES;"');
    } else if (error.code === 'ER_BAD_DB_ERROR') {
      console.log('');
      console.log('Database "lxcloud" does not exist - please run the database setup script:');
      console.log('npm run setup-db');
    }
    
    process.exit(1);
  }
}

testConnection();