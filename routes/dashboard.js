const express = require('express');
const { requireAuth, requireTwoFA } = require('../middleware/auth');
const User = require('../models/User');
const Controller = require('../models/Controller');
const logger = require('../config/logger');

const router = express.Router();

// Apply authentication middleware to all dashboard routes
router.use(requireAuth);
router.use(requireTwoFA);

// Dashboard main page
router.get('/', async (req, res) => {
  try {
    const user = req.user;
    
    // Get user's controllers
    const controllers = await Controller.findByUser(user.id);
    
    // Get overall stats if admin
    let stats = null;
    if (user.role === 'admin') {
      stats = await Controller.getStats();
    }
    
    // Get dashboard cards
    const dashboardCards = await user.getDashboardCards();
    
    res.render('dashboard/index', {
      title: 'Dashboard - LXCloud',
      user: user.toJSON(),
      controllers: controllers.map(c => c.toJSON()),
      stats: stats,
      dashboardCards: dashboardCards,
      messages: {
        twofa: req.query.twofa === 'enabled' ? 'Two-factor authentication has been enabled successfully!' : null
      }
    });
    
  } catch (error) {
    logger.error('Dashboard error:', error);
    res.status(500).render('error', {
      title: 'Dashboard Error',
      message: 'Unable to load dashboard',
      error: { status: 500 }
    });
  }
});

// Map view
router.get('/map', async (req, res) => {
  try {
    const user = req.user;
    
    let controllers;
    if (user.role === 'admin') {
      // Admin can see all controllers
      controllers = await Controller.findAll();
    } else {
      // Regular users see only their controllers
      controllers = await Controller.findByUser(user.id);
    }
    
    // Filter controllers with location data
    const controllersWithLocation = controllers.filter(c => c.latitude && c.longitude);
    
    res.render('dashboard/map', {
      title: 'Controller Map - LXCloud',
      user: user.toJSON(),
      controllers: controllersWithLocation.map(c => c.toJSON())
    });
    
  } catch (error) {
    logger.error('Map view error:', error);
    res.status(500).render('error', {
      title: 'Map Error',
      message: 'Unable to load map view',
      error: { status: 500 }
    });
  }
});

// Controller details page
router.get('/controller/:id', async (req, res) => {
  try {
    const user = req.user;
    const controllerId = req.params.id;
    
    const controller = await Controller.findById(controllerId);
    if (!controller) {
      return res.status(404).render('error', {
        title: 'Controller Not Found',
        message: 'The requested controller does not exist.',
        error: { status: 404 }
      });
    }
    
    // Check permissions
    if (user.role !== 'admin' && controller.userId !== user.id) {
      return res.status(403).render('error', {
        title: 'Access Denied',
        message: 'You do not have permission to view this controller.',
        error: { status: 403 }
      });
    }
    
    // Get recent data
    const recentData = await controller.getData(100);
    const latestData = await controller.getLatestData();
    
    res.render('dashboard/controller-details', {
      title: `${controller.name || controller.serialNumber} - LXCloud`,
      user: user.toJSON(),
      controller: controller.toJSON(),
      recentData: recentData,
      latestData: latestData
    });
    
  } catch (error) {
    logger.error('Controller details error:', error);
    res.status(500).render('error', {
      title: 'Controller Error',
      message: 'Unable to load controller details',
      error: { status: 500 }
    });
  }
});

// Analytics page
router.get('/analytics', async (req, res) => {
  try {
    const user = req.user;
    
    let controllers;
    if (user.role === 'admin') {
      controllers = await Controller.findAll();
    } else {
      controllers = await Controller.findByUser(user.id);
    }
    
    res.render('dashboard/analytics', {
      title: 'Analytics - LXCloud',
      user: user.toJSON(),
      controllers: controllers.map(c => c.toJSON())
    });
    
  } catch (error) {
    logger.error('Analytics error:', error);
    res.status(500).render('error', {
      title: 'Analytics Error',
      message: 'Unable to load analytics',
      error: { status: 500 }
    });
  }
});

module.exports = router;