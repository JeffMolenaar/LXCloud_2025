const mysql = require('mysql2/promise');
const logger = require('../config/logger');

async function setupDatabase() {
  try {
    console.log('Setting up database and lxadmin user...');
    
    // Connect as root to create database and user
    let connection;
    
    try {
      // Try to connect as root without password (common in dev environments)
      connection = await mysql.createConnection({
        host: 'localhost',
        user: 'root',
        password: ''
      });
      console.log('Connected to MySQL as root');
    } catch (error) {
      console.log('Failed to connect as root without password, trying with password prompt...');
      
      // If no password worked, prompt for manual setup
      console.log('\n🔧 Manual Database Setup Required');
      console.log('==========================================');
      console.log('Please run the following SQL commands as MySQL root user:');
      console.log('');
      console.log('mysql -u root -p');
      console.log('');
      console.log('Then execute:');
      console.log('CREATE DATABASE IF NOT EXISTS lxcloud;');
      console.log('CREATE USER IF NOT EXISTS \'lxadmin\'@\'localhost\' IDENTIFIED BY \'lxadmin\';');
      console.log('GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxadmin\'@\'localhost\';');
      console.log('FLUSH PRIVILEGES;');
      console.log('EXIT;');
      console.log('');
      console.log('After running these commands, the LXCloud application should be able to connect.');
      console.log('==========================================\n');
      
      return false;
    }
    
    if (connection) {
      // Create database
      await connection.execute('CREATE DATABASE IF NOT EXISTS lxcloud');
      console.log('✅ Database "lxcloud" created or already exists');
      
      // Create user
      await connection.execute('CREATE USER IF NOT EXISTS \'lxadmin\'@\'localhost\' IDENTIFIED BY \'lxadmin\'');
      console.log('✅ User "lxadmin" created or already exists');
      
      // Grant privileges
      await connection.execute('GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxadmin\'@\'localhost\'');
      console.log('✅ Privileges granted to lxadmin user');
      
      // Flush privileges
      await connection.execute('FLUSH PRIVILEGES');
      console.log('✅ Privileges flushed');
      
      await connection.end();
      console.log('\n🎉 Database setup completed successfully!');
      console.log('The application can now connect using:');
      console.log('  - Username: lxadmin');
      console.log('  - Password: lxadmin');
      console.log('  - Database: lxcloud\n');
      return true;
    }
    
  } catch (error) {
    console.error('❌ Database setup failed:', error.message);
    return false;
  }
}

// Run setup if called directly
if (require.main === module) {
  setupDatabase().then((success) => {
    if (success) {
      console.log('Database setup completed successfully');
      process.exit(0);
    } else {
      console.log('Database setup failed - please set up manually using the instructions above');
      process.exit(1);
    }
  });
}

module.exports = setupDatabase;