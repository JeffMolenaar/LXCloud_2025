const mysql = require('mysql2/promise');
const logger = require('../config/logger');

async function setupDatabase() {
  try {
    console.log('[2025-08-10 12:14:36] Setting up database schema...');
    
    // For localhost installations, try to setup database automatically
    let connection;
    let connectionSuccess = false;
    
    // Try connecting as root without password first (common for localhost MariaDB)
    try {
      console.log('Attempting to connect as root without password...');
      connection = await mysql.createConnection({
        host: 'localhost',
        user: 'root',
        password: ''
      });
      console.log('✅ Connected to MySQL as root');
      connectionSuccess = true;
    } catch (error) {
      console.log(`❌ Root connection failed: ${error.message}`);
      
      // Try using sudo mysql for localhost systems
      console.log('Attempting automated database setup via sudo mysql...');
      try {
        const { execSync } = require('child_process');
        
        // Execute SQL commands directly through sudo mysql
        const sqlCommands = `
          CREATE DATABASE IF NOT EXISTS lxcloud;
          CREATE USER IF NOT EXISTS 'lxcloud'@'localhost' IDENTIFIED BY 'lxcloud';
          GRANT ALL PRIVILEGES ON lxcloud.* TO 'lxcloud'@'localhost';
          FLUSH PRIVILEGES;
        `;
        
        execSync(`sudo mysql -e "${sqlCommands}"`, { stdio: 'inherit' });
        console.log('✅ Database setup completed via sudo mysql');
        
        // Test connection with new user
        const testConnection = await mysql.createConnection({
          host: 'localhost',
          user: 'lxcloud',
          password: 'lxcloud',
          database: 'lxcloud'
        });
        
        await testConnection.ping();
        await testConnection.end();
        console.log('✅ Database connection test successful');
        
        return true;
      } catch (sudoError) {
        console.log(`❌ Sudo mysql failed: ${sudoError.message}`);
      }
    }
    
    if (connectionSuccess && connection) {
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
    
    // Fallback: Provide manual instructions
    console.log('\n🔧 Manual Database Setup Required');
    console.log('==========================================');
    console.log('Automatic setup failed. Please run ONE of the following:');
    console.log('');
    console.log('Option 1 - Using sudo (recommended for localhost):');
    console.log('sudo mysql -e "CREATE DATABASE IF NOT EXISTS lxcloud; CREATE USER IF NOT EXISTS \'lxcloud\'@\'localhost\' IDENTIFIED BY \'lxcloud\'; GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxcloud\'@\'localhost\'; FLUSH PRIVILEGES;"');
    console.log('');
    console.log('Option 2 - Manual MySQL connection:');
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