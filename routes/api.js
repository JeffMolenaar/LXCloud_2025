const express = require('express');
const { authenticateToken, requireAuth } = require('../middleware/auth');
const Controller = require('../models/Controller');
const User = require('../models/User');
const logger = require('../config/logger');

const router = express.Router();

// Get recent activity
router.get('/recent-activity', requireAuth, async (req, res) => {
  try {
    const user = req.user;
    const limit = parseInt(req.query.limit) || 10;
    
    // This is a simplified version - you'd typically have an activity log table
    const activities = [
      {
        type: 'controller_connected',
        title: 'Controller Connected',
        description: 'Weather Station #001 came online',
        timestamp: new Date()
      },
      {
        type: 'data_received',
        title: 'New Data Received',
        description: 'Speed Radar #003 sent new measurements',
        timestamp: new Date(Date.now() - 5 * 60 * 1000)
      }
    ];
    
    res.json({ activities });
    
  } catch (error) {
    logger.error('Recent activity API error:', error);
    res.status(500).json({ error: 'Failed to load recent activity' });
  }
});

// Get controller data
router.get('/controllers/:id/data', authenticateToken, async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    // Check permissions
    if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    const limit = parseInt(req.query.limit) || 100;
    const offset = parseInt(req.query.offset) || 0;
    const startDate = req.query.startDate ? new Date(req.query.startDate) : null;
    const endDate = req.query.endDate ? new Date(req.query.endDate) : null;
    
    const data = await controller.getData(limit, offset, startDate, endDate);
    
    res.json({
      data: data,
      controller: controller.toJSON()
    });
    
  } catch (error) {
    logger.error('Controller data API error:', error);
    res.status(500).json({ error: 'Failed to load controller data' });
  }
});

// Get controller status
router.get('/controllers/:id/status', authenticateToken, async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    // Check permissions
    if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    res.json({
      id: controller.id,
      serialNumber: controller.serialNumber,
      status: controller.status,
      isOnline: controller.isOnline(),
      lastSeen: controller.lastSeen
    });
    
  } catch (error) {
    logger.error('Controller status API error:', error);
    res.status(500).json({ error: 'Failed to get controller status' });
  }
});

// Get all controllers for map
router.get('/controllers/map', requireAuth, async (req, res) => {
  try {
    const user = req.user;
    
    let controllers;
    if (user.role === 'admin') {
      controllers = await Controller.findAll();
    } else {
      controllers = await Controller.findByUser(user.id);
    }
    
    // Filter controllers with location data
    const controllersWithLocation = controllers
      .filter(c => c.latitude && c.longitude)
      .map(c => ({
        id: c.id,
        serialNumber: c.serialNumber,
        name: c.name,
        type: c.type,
        latitude: c.latitude,
        longitude: c.longitude,
        status: c.status,
        isOnline: c.isOnline(),
        lastSeen: c.lastSeen
      }));
    
    res.json({ controllers: controllersWithLocation });
    
  } catch (error) {
    logger.error('Controllers map API error:', error);
    res.status(500).json({ error: 'Failed to load controller map data' });
  }
});

// Get dashboard stats
router.get('/stats', requireAuth, async (req, res) => {
  try {
    const user = req.user;
    
    let stats;
    if (user.role === 'admin') {
      stats = await Controller.getStats();
      const users = await User.findAll();
      stats.totalUsers = users.length;
    } else {
      const userControllers = await Controller.findByUser(user.id);
      stats = {
        total: userControllers.length,
        online: userControllers.filter(c => c.isOnline()).length,
        offline: userControllers.filter(c => !c.isOnline()).length,
        bound: userControllers.length,
        unbound: 0
      };
    }
    
    res.json({ stats });
    
  } catch (error) {
    logger.error('Stats API error:', error);
    res.status(500).json({ error: 'Failed to load stats' });
  }
});

// Update controller location
router.put('/controllers/:id/location', authenticateToken, async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    // Check permissions
    if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    const { latitude, longitude } = req.body;
    
    if (!latitude || !longitude) {
      return res.status(400).json({ error: 'Latitude and longitude are required' });
    }
    
    await controller.update({
      name: controller.name,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      config: controller.config
    });
    
    res.json({
      success: true,
      controller: controller.toJSON()
    });
    
  } catch (error) {
    logger.error('Controller location update API error:', error);
    res.status(500).json({ error: 'Failed to update controller location' });
  }
});

// Get system health
router.get('/health', (req, res) => {
  const database = require('../config/database');
  const container = require('../config/container');
  
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    mockMode: database.mockMode,
    version: process.env.npm_package_version || '1.0.0',
    uptime: process.uptime(),
    services: {
      database: database.mockMode ? 'mock' : 'connected',
      session: 'available',
      auth: 'available'
    }
  });
});

module.exports = router;