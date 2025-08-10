const mysql = require('mysql2/promise');
const logger = require('../config/logger');

async function setupDatabase() {
  try {
    console.log('[2025-08-10 12:14:36] Setting up database schema...');
    
    // Connect as root to create database and user
    let connection;
    
    // Try multiple root authentication methods
    const rootAuthMethods = [
      { user: 'root', password: '' }, // No password (common in Docker/dev)
      { user: 'root', password: 'root' }, // Common default
      { user: 'root', password: 'password' }, // Another common default
      { user: 'root', auth_plugin: 'mysql_native_password', password: '' } // MySQL 8.0+ native auth
    ];
    
    let connectionSuccess = false;
    
    for (const authMethod of rootAuthMethods) {
      try {
        console.log(`Attempting to connect as root with auth method: ${JSON.stringify({user: authMethod.user, hasPassword: !!authMethod.password, auth_plugin: authMethod.auth_plugin})}`);
        
        // Use only valid MySQL2 connection options
        const connectionConfig = {
          host: 'localhost',
          user: authMethod.user,
          password: authMethod.password
        };
        
        // Add auth_plugin if specified
        if (authMethod.auth_plugin) {
          connectionConfig.authPlugins = {
            mysql_native_password: () => authMethod.auth_plugin
          };
        }
        
        connection = await mysql.createConnection(connectionConfig);
        console.log('✅ Connected to MySQL as root');
        connectionSuccess = true;
        break;
      } catch (error) {
        console.log(`❌ Failed: ${error.message}`);
        continue;
      }
    }
    
    if (!connectionSuccess) {
      console.log('\n🔧 Manual Database Setup Required');
      console.log('==========================================');
      console.log('All automatic connection attempts failed. Common reasons:');
      console.log('1. MySQL root user requires a password');
      console.log('2. MySQL root user is configured for socket authentication only');
      console.log('3. MySQL service is not running');
      console.log('');
      console.log('Please run the following SQL commands as MySQL root user:');
      console.log('');
      console.log('# Connect to MySQL as root:');
      console.log('sudo mysql -u root');
      console.log('# OR if password required:');
      console.log('mysql -u root -p');
      console.log('');
      console.log('# Then execute these SQL commands:');
      console.log('CREATE DATABASE IF NOT EXISTS lxcloud;');
      console.log('CREATE USER IF NOT EXISTS \'lxcloud\'@\'localhost\' IDENTIFIED BY \'lxcloud\';');
      console.log('GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxcloud\'@\'localhost\';');
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
      await connection.execute('CREATE USER IF NOT EXISTS \'lxcloud\'@\'localhost\' IDENTIFIED BY \'lxcloud\'');
      console.log('✅ User "lxcloud" created or already exists');
      
      // Grant privileges
      await connection.execute('GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxcloud\'@\'localhost\'');
      console.log('✅ Privileges granted to lxcloud user');
      
      // Flush privileges
      await connection.execute('FLUSH PRIVILEGES');
      console.log('✅ Privileges flushed');
      
      await connection.end();
      console.log('\n🎉 Database setup completed successfully!');
      console.log('The application can now connect using:');
      console.log('  - Username: lxcloud');
      console.log('  - Password: lxcloud');
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