const mqtt = require('mqtt');
const logger = require('../config/logger');
const Controller = require('../models/Controller');

class MQTTService {
  constructor() {
    this.client = null;
    this.io = null;
    this.reconnectInterval = 5000;
  }

  initialize(socketIo) {
    this.io = socketIo;
    this.connect();
  }

  connect() {
    const brokerUrl = process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883';
    const options = {
      username: process.env.MQTT_USERNAME,
      password: process.env.MQTT_PASSWORD,
      reconnectPeriod: this.reconnectInterval,
      connectTimeout: 30000,
      clean: true
    };

    this.client = mqtt.connect(brokerUrl, options);

    this.client.on('connect', () => {
      logger.info('Connected to MQTT broker');
      this.subscribeToTopics();
    });

    this.client.on('error', (error) => {
      logger.error('MQTT connection error:', error);
    });

    this.client.on('offline', () => {
      logger.warn('MQTT client offline');
    });

    this.client.on('reconnect', () => {
      logger.info('Reconnecting to MQTT broker');
    });

    this.client.on('message', (topic, message) => {
      this.handleMessage(topic, message);
    });
  }

  subscribeToTopics() {
    const topicPrefix = process.env.MQTT_TOPIC_PREFIX || 'lxcloud';
    
    // Subscribe to controller data topics
    this.client.subscribe(`${topicPrefix}/controllers/+/data`, (err) => {
      if (err) {
        logger.error('Failed to subscribe to controller data topic:', err);
      } else {
        logger.info('Subscribed to controller data topics');
      }
    });

    // Subscribe to controller status topics
    this.client.subscribe(`${topicPrefix}/controllers/+/status`, (err) => {
      if (err) {
        logger.error('Failed to subscribe to controller status topic:', err);
      } else {
        logger.info('Subscribed to controller status topics');
      }
    });

    // Subscribe to controller registration topics
    this.client.subscribe(`${topicPrefix}/controllers/+/register`, (err) => {
      if (err) {
        logger.error('Failed to subscribe to controller registration topic:', err);
      } else {
        logger.info('Subscribed to controller registration topics');
      }
    });
  }

  async handleMessage(topic, message) {
    try {
      const topicParts = topic.split('/');
      const topicPrefix = process.env.MQTT_TOPIC_PREFIX || 'lxcloud';
      
      if (topicParts.length < 4 || topicParts[0] !== topicPrefix || topicParts[1] !== 'controllers') {
        return;
      }

      const serialNumber = topicParts[2];
      const messageType = topicParts[3];
      const payload = JSON.parse(message.toString());

      logger.info(`Received MQTT message: ${topic}`, { serialNumber, messageType, payload });

      switch (messageType) {
        case 'register':
          await this.handleControllerRegistration(serialNumber, payload);
          break;
        case 'data':
          await this.handleControllerData(serialNumber, payload);
          break;
        case 'status':
          await this.handleControllerStatus(serialNumber, payload);
          break;
        default:
          logger.warn(`Unknown message type: ${messageType}`);
      }

    } catch (error) {
      logger.error('Error handling MQTT message:', error);
    }
  }

  async handleControllerRegistration(serialNumber, payload) {
    try {
      const { type, latitude, longitude, name } = payload;
      
      if (!type || !['speedradar', 'beaufortmeter', 'weatherstation', 'aicamera'].includes(type)) {
        logger.error(`Invalid controller type: ${type}`);
        return;
      }

      let controller = await Controller.findBySerialNumber(serialNumber);
      
      if (!controller) {
        // Create new controller
        controller = await Controller.create({
          serialNumber,
          type,
          latitude: latitude || null,
          longitude: longitude || null
        });
        
        if (name) {
          await controller.update({ name, latitude, longitude, config: {} });
        }
        
        logger.info(`New controller registered: ${serialNumber} (${type})`);
      } else {
        // Update existing controller
        await controller.update({
          name: name || controller.name,
          latitude: latitude || controller.latitude,
          longitude: longitude || controller.longitude,
          config: controller.config
        });
        
        logger.info(`Controller updated: ${serialNumber}`);
      }

      // Update status to online
      await controller.updateStatus('online');

      // Emit real-time update
      this.emitControllerUpdate(controller);

    } catch (error) {
      logger.error('Error handling controller registration:', error);
    }
  }

  async handleControllerData(serialNumber, payload) {
    try {
      let controller = await Controller.findBySerialNumber(serialNumber);
      
      if (!controller) {
        logger.warn(`Data received for unknown controller: ${serialNumber}`);
        return;
      }

      // Add data to controller
      await controller.addData(payload.data, payload.timestamp);
      
      logger.debug(`Data added for controller: ${serialNumber}`);

      // Emit real-time data update
      this.emitControllerDataUpdate(controller, payload.data);

    } catch (error) {
      logger.error('Error handling controller data:', error);
    }
  }

  async handleControllerStatus(serialNumber, payload) {
    try {
      let controller = await Controller.findBySerialNumber(serialNumber);
      
      if (!controller) {
        logger.warn(`Status update for unknown controller: ${serialNumber}`);
        return;
      }

      const { status, timestamp } = payload;
      await controller.updateStatus(status, timestamp);
      
      logger.info(`Controller ${serialNumber} status updated to: ${status}`);

      // Emit real-time status update
      this.emitControllerUpdate(controller);

    } catch (error) {
      logger.error('Error handling controller status:', error);
    }
  }

  emitControllerUpdate(controller) {
    if (this.io) {
      // Emit to all connected clients
      this.io.emit('controller-updated', controller.toJSON());
      
      // Emit to specific user if controller is bound
      if (controller.userId) {
        this.io.to(`user-${controller.userId}`).emit('controller-updated', controller.toJSON());
      }
    }
  }

  emitControllerDataUpdate(controller, data) {
    if (this.io) {
      const updateData = {
        controllerId: controller.id,
        serialNumber: controller.serialNumber,
        data: data,
        timestamp: new Date()
      };
      
      // Emit to all connected clients
      this.io.emit('controller-data', updateData);
      
      // Emit to specific user if controller is bound
      if (controller.userId) {
        this.io.to(`user-${controller.userId}`).emit('controller-data', updateData);
      }
    }
  }

  publish(topic, message) {
    if (this.client && this.client.connected) {
      this.client.publish(topic, JSON.stringify(message), (err) => {
        if (err) {
          logger.error('Failed to publish MQTT message:', err);
        }
      });
    }
  }

  disconnect() {
    if (this.client) {
      this.client.end();
      logger.info('Disconnected from MQTT broker');
    }
  }
}

const mqttService = new MQTTService();
module.exports = mqttService;