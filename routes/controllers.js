const express = require('express');
const { requireAuth, requireTwoFA } = require('../middleware/auth');
const Controller = require('../models/Controller');
const { body, validationResult } = require('express-validator');
const logger = require('../config/logger');

const router = express.Router();

// Apply authentication middleware
router.use(requireAuth);
router.use(requireTwoFA);

// Controller list page
router.get('/', async (req, res) => {
  try {
    const user = req.user;
    
    let controllers;
    if (user.role === 'admin') {
      controllers = await Controller.findAll();
    } else {
      controllers = await Controller.findByUser(user.id);
    }
    
    res.render('controllers/index', {
      title: 'Controllers - LXCloud',
      user: user.toJSON(),
      controllers: controllers.map(c => c.toJSON())
    });
    
  } catch (error) {
    logger.error('Controllers list error:', error);
    res.status(500).render('error', {
      title: 'Controllers Error',
      message: 'Unable to load controllers',
      error: { status: 500 }
    });
  }
});

// Bind controller page
router.get('/bind', async (req, res) => {
  try {
    // Get available controllers that have reported but are not bound
    const availableControllers = await Controller.findUnbound();
    
    res.render('controllers/bind', {
      title: 'Bind Controller - LXCloud',
      user: req.user.toJSON(),
      availableControllers: availableControllers.map(c => c.toJSON())
    });
    
  } catch (error) {
    logger.error('Bind controller page error:', error);
    res.status(500).render('error', {
      title: 'Bind Controller Error',
      message: 'Unable to load bind controller page',
      error: { status: 500 }
    });
  }
});

// Bind controller action
router.post('/bind',
  [body('serialNumber').notEmpty().withMessage('Serial number is required')],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        const availableControllers = await Controller.findUnbound();
        return res.render('controllers/bind', {
          title: 'Bind Controller - LXCloud',
          user: req.user.toJSON(),
          availableControllers: availableControllers.map(c => c.toJSON()),
          error: errors.array()[0].msg
        });
      }

      const { serialNumber } = req.body;
      const controller = await Controller.findBySerialNumber(serialNumber);
      
      if (!controller) {
        const availableControllers = await Controller.findUnbound();
        return res.render('controllers/bind', {
          title: 'Bind Controller - LXCloud',
          user: req.user.toJSON(),
          availableControllers: availableControllers.map(c => c.toJSON()),
          error: 'Controller with this serial number has not been seen by the system'
        });
      }
      
      if (controller.userId) {
        const availableControllers = await Controller.findUnbound();
        return res.render('controllers/bind', {
          title: 'Bind Controller - LXCloud',
          user: req.user.toJSON(),
          availableControllers: availableControllers.map(c => c.toJSON()),
          error: 'Controller is already bound to another user'
        });
      }
      
      await controller.bindToUser(req.user.id);
      
      logger.info(`Controller ${serialNumber} bound to user ${req.user.email}`);
      res.redirect('/controllers?success=bound');
      
    } catch (error) {
      logger.error('Bind controller error:', error);
      const availableControllers = await Controller.findUnbound();
      res.render('controllers/bind', {
        title: 'Bind Controller - LXCloud',
        user: req.user.toJSON(),
        availableControllers: availableControllers.map(c => c.toJSON()),
        error: 'An error occurred while binding the controller'
      });
    }
  }
);

// Controller edit page
router.get('/:id/edit', async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).render('error', {
        title: 'Controller Not Found',
        message: 'The requested controller does not exist.',
        error: { status: 404 }
      });
    }
    
    // Check permissions
    if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
      return res.status(403).render('error', {
        title: 'Access Denied',
        message: 'You do not have permission to edit this controller.',
        error: { status: 403 }
      });
    }
    
    res.render('controllers/edit', {
      title: `Edit ${controller.name || controller.serialNumber} - LXCloud`,
      user: req.user.toJSON(),
      controller: controller.toJSON()
    });
    
  } catch (error) {
    logger.error('Controller edit page error:', error);
    res.status(500).render('error', {
      title: 'Controller Error',
      message: 'Unable to load controller edit page',
      error: { status: 500 }
    });
  }
});

// Update controller
router.post('/:id/edit',
  [
    body('name').optional().isLength({ min: 1, max: 255 }),
    body('latitude').optional().isFloat({ min: -90, max: 90 }),
    body('longitude').optional().isFloat({ min: -180, max: 180 })
  ],
  async (req, res) => {
    try {
      const controller = await Controller.findById(req.params.id);
      
      if (!controller) {
        return res.status(404).render('error', {
          title: 'Controller Not Found',
          message: 'The requested controller does not exist.',
          error: { status: 404 }
        });
      }
      
      // Check permissions
      if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
        return res.status(403).render('error', {
          title: 'Access Denied',
          message: 'You do not have permission to edit this controller.',
          error: { status: 403 }
        });
      }
      
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('controllers/edit', {
          title: `Edit ${controller.name || controller.serialNumber} - LXCloud`,
          user: req.user.toJSON(),
          controller: controller.toJSON(),
          error: errors.array()[0].msg
        });
      }
      
      const { name, latitude, longitude } = req.body;
      await controller.update({
        name: name || null,
        latitude: latitude ? parseFloat(latitude) : null,
        longitude: longitude ? parseFloat(longitude) : null,
        config: controller.config
      });
      
      logger.info(`Controller ${controller.serialNumber} updated by ${req.user.email}`);
      res.redirect('/controllers?success=updated');
      
    } catch (error) {
      logger.error('Controller update error:', error);
      res.render('controllers/edit', {
        title: `Edit Controller - LXCloud`,
        user: req.user.toJSON(),
        controller: req.body,
        error: 'An error occurred while updating the controller'
      });
    }
  }
);

// Unbind controller
router.post('/:id/unbind', async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    // Check permissions
    if (req.user.role !== 'admin' && controller.userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    await controller.unbind();
    
    logger.info(`Controller ${controller.serialNumber} unbound by ${req.user.email}`);
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Controller unbind error:', error);
    res.status(500).json({ error: 'Failed to unbind controller' });
  }
});

module.exports = router;