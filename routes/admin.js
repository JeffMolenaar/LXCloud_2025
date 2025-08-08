const express = require('express');
const { requireAuth, requireTwoFA, requireAdmin } = require('../middleware/auth');
const User = require('../models/User');
const Controller = require('../models/Controller');
const logger = require('../config/logger');

const router = express.Router();

// Apply authentication and admin middleware
router.use(requireAuth);
router.use(requireTwoFA);
router.use(requireAdmin);

// Admin dashboard
router.get('/', async (req, res) => {
  try {
    const stats = await Controller.getStats();
    const totalUsers = await User.findAll();
    
    res.render('admin/index', {
      title: 'Admin Panel - LXCloud',
      user: req.user.toJSON(),
      stats: {
        ...stats,
        totalUsers: totalUsers.length
      }
    });
    
  } catch (error) {
    logger.error('Admin dashboard error:', error);
    res.status(500).render('error', {
      title: 'Admin Error',
      message: 'Unable to load admin dashboard',
      error: { status: 500 }
    });
  }
});

// User management
router.get('/users', async (req, res) => {
  try {
    const users = await User.findAll();
    
    res.render('admin/users', {
      title: 'User Management - LXCloud',
      user: req.user.toJSON(),
      users: users.map(u => u.toJSON())
    });
    
  } catch (error) {
    logger.error('Admin users error:', error);
    res.status(500).render('error', {
      title: 'User Management Error',
      message: 'Unable to load user management',
      error: { status: 500 }
    });
  }
});

// System controllers
router.get('/controllers', async (req, res) => {
  try {
    const controllers = await Controller.findAll();
    
    res.render('admin/controllers', {
      title: 'System Controllers - LXCloud',
      user: req.user.toJSON(),
      controllers: controllers.map(c => c.toJSON())
    });
    
  } catch (error) {
    logger.error('Admin controllers error:', error);
    res.status(500).render('error', {
      title: 'System Controllers Error',
      message: 'Unable to load system controllers',
      error: { status: 500 }
    });
  }
});

// UI Customization
router.get('/ui-customization', (req, res) => {
  res.render('admin/ui-customization', {
    title: 'UI Customization - LXCloud',
    user: req.user.toJSON()
  });
});

// Addon Management
router.get('/addons', (req, res) => {
  res.render('admin/addons', {
    title: 'Addon Management - LXCloud',
    user: req.user.toJSON()
  });
});

// System Settings
router.get('/settings', (req, res) => {
  res.render('admin/settings', {
    title: 'System Settings - LXCloud',
    user: req.user.toJSON()
  });
});

// Force unbind controller
router.post('/controllers/:id/unbind', async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    await controller.unbind();
    
    logger.info(`Controller ${controller.serialNumber} force unbound by admin ${req.user.email}`);
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Admin controller unbind error:', error);
    res.status(500).json({ error: 'Failed to unbind controller' });
  }
});

// Delete controller
router.delete('/controllers/:id', async (req, res) => {
  try {
    const controller = await Controller.findById(req.params.id);
    
    if (!controller) {
      return res.status(404).json({ error: 'Controller not found' });
    }
    
    await controller.delete();
    
    logger.info(`Controller ${controller.serialNumber} deleted by admin ${req.user.email}`);
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Admin controller delete error:', error);
    res.status(500).json({ error: 'Failed to delete controller' });
  }
});

// Disable user 2FA
router.post('/users/:id/disable-2fa', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    await user.disableTwoFA();
    
    logger.info(`2FA disabled for user ${user.email} by admin ${req.user.email}`);
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Admin 2FA disable error:', error);
    res.status(500).json({ error: 'Failed to disable 2FA' });
  }
});

// Reset user password
router.post('/users/:id/reset-password', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    const tempPassword = Math.random().toString(36).slice(-8);
    await user.updatePassword(tempPassword);
    
    logger.info(`Password reset for user ${user.email} by admin ${req.user.email}`);
    res.json({ 
      success: true, 
      tempPassword: tempPassword 
    });
    
  } catch (error) {
    logger.error('Admin password reset error:', error);
    res.status(500).json({ error: 'Failed to reset password' });
  }
});

// Delete user
router.delete('/users/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    if (user.id === req.user.id) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }
    
    await user.deactivate();
    
    logger.info(`User ${user.email} deleted by admin ${req.user.email}`);
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Admin user delete error:', error);
    res.status(500).json({ error: 'Failed to delete user' });
  }
});

module.exports = router;