const { testMQTTConnection, loadEnvFile } = require('../scripts/test-mqtt-connection');
const path = require('path');
const fs = require('fs');

describe('MQTT Connectivity', () => {
  let envVars;
  
  beforeAll(() => {
    // Load environment variables for testing
    const envPath = path.join(__dirname, '..', '.env');
    if (fs.existsSync(envPath)) {
      envVars = loadEnvFile(envPath);
    } else {
      // Use example environment for testing
      const exampleEnvPath = path.join(__dirname, '..', '.env.example');
      if (fs.existsSync(exampleEnvPath)) {
        envVars = loadEnvFile(exampleEnvPath);
      }
    }
  });

  describe('Environment Configuration', () => {
    test('should load environment variables correctly', () => {
      expect(envVars).toBeDefined();
      expect(envVars.MQTT_BROKER_URL).toBeDefined();
      expect(envVars.MQTT_USERNAME).toBeDefined();
      expect(envVars.MQTT_PASSWORD).toBeDefined();
    });

    test('should have valid MQTT configuration', () => {
      expect(envVars.MQTT_BROKER_URL).toMatch(/^mqtt:\/\//);
      expect(envVars.MQTT_USERNAME).toBe('lxcloud_mqtt');
      expect(envVars.MQTT_PASSWORD).toBeTruthy();
    });
  });

  describe('MQTT Test Script Functionality', () => {
    test('should handle missing environment file gracefully', () => {
      expect(() => {
        loadEnvFile('/nonexistent/path/.env');
      }).toThrow();
    });

    test('should reject connection to non-existent broker', async () => {
      const fakeBrokerUrl = 'mqtt://nonexistent.broker:1883';
      const username = 'test';
      const password = 'test';
      
      await expect(
        testMQTTConnection(fakeBrokerUrl, username, password, 1000)
      ).rejects.toThrow();
    }, 10000);

    test('should handle connection timeout properly', async () => {
      // Use a non-responsive IP address to test timeout
      const timeoutBrokerUrl = 'mqtt://192.0.2.1:1883'; // RFC 5737 test address
      const username = 'test';
      const password = 'test';
      
      const startTime = Date.now();
      await expect(
        testMQTTConnection(timeoutBrokerUrl, username, password, 1000)
      ).rejects.toThrow();
      const endTime = Date.now();
      
      // Should timeout around 1000ms, allow some tolerance
      expect(endTime - startTime).toBeGreaterThanOrEqual(900);
      expect(endTime - startTime).toBeLessThan(2000);
    }, 5000);
  });

  describe('Configuration Validation', () => {
    test('should validate MQTT broker URL format', () => {
      const validUrls = [
        'mqtt://localhost:1883',
        'mqtt://127.0.0.1:1883',
        'mqtt://example.com:1883',
        'mqtts://secure.example.com:8883'
      ];
      
      validUrls.forEach(url => {
        expect(() => new URL(url)).not.toThrow();
      });
    });

    test('should validate MQTT credentials format', () => {
      expect(envVars.MQTT_USERNAME).toMatch(/^[a-zA-Z0-9_]+$/);
      expect(envVars.MQTT_PASSWORD.length).toBeGreaterThan(0);
    });
  });
});