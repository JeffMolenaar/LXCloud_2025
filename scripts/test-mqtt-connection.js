#!/usr/bin/env node

/**
 * LXCloud MQTT Connection Test Script
 * Tests MQTT broker connectivity using the same configuration as the application
 */

const mqtt = require('mqtt');
const fs = require('fs');
const path = require('path');
const net = require('net');

// Function to load environment variables from .env file
function loadEnvFile(envPath) {
  if (!fs.existsSync(envPath)) {
    throw new Error(`Environment file not found: ${envPath}`);
  }

  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = {};
  
  envContent.split('\n').forEach(line => {
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.startsWith('#')) {
      const [key, ...valueParts] = trimmedLine.split('=');
      if (key && valueParts.length > 0) {
        envVars[key.trim()] = valueParts.join('=').trim();
      }
    }
  });
  
  return envVars;
}

// Function to check if MQTT port is listening
function checkMQTTPort(host, port) {
  return new Promise((resolve, reject) => {
    const socket = new net.Socket();
    const timeout = 3000;
    
    socket.setTimeout(timeout);
    
    socket.on('connect', () => {
      socket.destroy();
      resolve(true);
    });
    
    socket.on('timeout', () => {
      socket.destroy();
      reject(new Error(`Port ${port} is not responding`));
    });
    
    socket.on('error', (error) => {
      socket.destroy();
      reject(new Error(`Cannot connect to ${host}:${port} - ${error.message}`));
    });
    
    socket.connect(port, host);
  });
}

// Function to test MQTT connectivity
function testMQTTConnection(brokerUrl, username, password, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const client = mqtt.connect(brokerUrl, {
      username: username,
      password: password,
      connectTimeout: timeout,
      clean: true
    });

    const timer = setTimeout(() => {
      client.end(true);
      reject(new Error(`Connection timeout after ${timeout}ms`));
    }, timeout);

    client.on('connect', () => {
      clearTimeout(timer);
      
      // Test publishing a message
      client.publish('test/connectivity', 'hello', (err) => {
        client.end();
        if (err) {
          reject(new Error(`Failed to publish test message: ${err.message}`));
        } else {
          resolve('MQTT connection successful');
        }
      });
    });

    client.on('error', (error) => {
      clearTimeout(timer);
      client.end(true);
      reject(new Error(`MQTT connection error: ${error.message}`));
    });

    client.on('offline', () => {
      clearTimeout(timer);
      client.end(true);
      reject(new Error('MQTT client went offline'));
    });
  });
}

async function main() {
  try {
    // Determine the application directory
    const appDir = process.env.INSTALL_DIR || '/opt/LXCloud_2025';
    const currentDir = process.cwd();
    
    // Try to find .env file in multiple locations
    let envPath;
    const possibleEnvPaths = [
      path.join(appDir, '.env'),
      path.join(currentDir, '.env'),
      path.join(__dirname, '..', '.env')
    ];
    
    for (const testPath of possibleEnvPaths) {
      if (fs.existsSync(testPath)) {
        envPath = testPath;
        break;
      }
    }
    
    if (!envPath) {
      throw new Error('No .env file found in expected locations: ' + possibleEnvPaths.join(', '));
    }

    // Load environment variables
    const envVars = loadEnvFile(envPath);
    
    // Get MQTT configuration
    const brokerUrl = envVars.MQTT_BROKER_URL || 'mqtt://localhost:1883';
    const username = envVars.MQTT_USERNAME || 'lxcloud_mqtt';
    const password = envVars.MQTT_PASSWORD;
    
    if (!password) {
      throw new Error('MQTT_PASSWORD not found in environment file');
    }

    // Parse broker URL to get host and port
    const url = new URL(brokerUrl);
    const host = url.hostname || 'localhost';
    const port = parseInt(url.port) || 1883;

    // First check if the MQTT port is reachable
    try {
      await checkMQTTPort(host, port);
    } catch (error) {
      throw new Error(`MQTT broker not reachable: ${error.message}`);
    }

    // Test MQTT connection
    const result = await testMQTTConnection(brokerUrl, username, password);
    console.log(result);
    process.exit(0);
    
  } catch (error) {
    if (require.main === module) {
      console.error(`MQTT connectivity test failed: ${error.message}`);
      process.exit(1);
    } else {
      throw error;
    }
  }
}

// Handle command line execution
if (require.main === module) {
  main();
}

module.exports = { testMQTTConnection, loadEnvFile };