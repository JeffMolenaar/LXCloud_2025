const express = require('express');
const { requireAuth, requireTwoFA, requireAdmin } = require('../middleware/auth');
const database = require('../config/database');
const mqttService = require('../controllers/mqttController');
const logger = require('../config/logger');

const router = express.Router();

// Apply authentication and admin middleware
router.use(requireAuth);
router.use(requireTwoFA);  
router.use(requireAdmin);

// Admin dashboard - use integrated version
router.get('/', async (req, res) => {
  try {
    // Get comprehensive system stats
    const stats = await getSystemStats();
    
    res.render('admin/index-integrated', {
      title: 'Super Admin Panel - LXCloud Integrated',
      user: req.user,
      stats: stats
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
    const users = await database.query('SELECT * FROM users ORDER BY created_at DESC');
    
    res.render('admin/users-integrated', {
      title: 'User Management - LXCloud',
      user: req.user,
      users: users
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

// Controller management
router.get('/controllers', async (req, res) => {
  try {
    const controllers = await database.query('SELECT * FROM controllers ORDER BY created_at DESC');
    
    res.render('admin/controllers-integrated', {
      title: 'Controller Management - LXCloud',
      user: req.user,
      controllers: controllers
    });
    
  } catch (error) {
    logger.error('Admin controllers error:', error);
    res.status(500).render('error', {
      title: 'Controller Management Error',
      message: 'Unable to load controller management', 
      error: { status: 500 }
    });
  }
});

// UI Customization
router.get('/ui-customization', async (req, res) => {
  try {
    const customizations = await database.query('SELECT * FROM ui_customizations ORDER BY page ASC');
    
    res.render('admin/ui-customization-integrated', {
      title: 'UI Customization - LXCloud',
      user: req.user,
      customizations: customizations
    });
    
  } catch (error) {
    logger.error('UI customization error:', error);
    res.render('admin/ui-customization-integrated', {
      title: 'UI Customization - LXCloud',
      user: req.user,
      customizations: []
    });
  }
});

// System Settings
router.get('/settings', async (req, res) => {
  try {
    const settings = await database.query('SELECT * FROM system_settings ORDER BY setting_key ASC');
    
    res.render('admin/settings-integrated', {
      title: 'System Settings - LXCloud',
      user: req.user,
      settings: settings,
      env: {
        DB_HOST: process.env.DB_HOST,
        DB_NAME: process.env.DB_NAME,
        MQTT_BROKER_URL: process.env.MQTT_BROKER_URL,
        MQTT_TOPIC_PREFIX: process.env.MQTT_TOPIC_PREFIX,
        NODE_ENV: process.env.NODE_ENV
      }
    });
    
  } catch (error) {
    logger.error('System settings error:', error);
    res.render('admin/settings-integrated', {
      title: 'System Settings - LXCloud',
      user: req.user,
      settings: [],
      env: {}
    });
  }
});

// API Routes for AJAX calls
router.post('/api/test-database', async (req, res) => {
  try {
    await database.query('SELECT 1');
    res.json({ success: true, message: 'Database connection successful' });
  } catch (error) {
    logger.error('Database test failed:', error);
    res.json({ success: false, error: error.message });
  }
});

router.post('/api/test-mqtt', async (req, res) => {
  try {
    if (mqttService.client && mqttService.client.connected) {
      // Publish test message
      mqttService.publish('lxcloud/admin/test', {
        message: 'Admin test message',
        timestamp: new Date().toISOString(),
        source: 'admin-panel'
      });
      res.json({ success: true, message: 'MQTT test message published' });
    } else {
      res.json({ success: false, error: 'MQTT client not connected' });
    }
  } catch (error) {
    logger.error('MQTT test failed:', error);
    res.json({ success: false, error: error.message });
  }
});

router.get('/api/stats', async (req, res) => {
  try {
    const stats = await getSystemStats();
    res.json(stats);
  } catch (error) {
    logger.error('Stats API error:', error);
    res.json({ total: 0, online: 0, bound: 0, totalUsers: 0 });
  }
});

// User management API
router.post('/api/users', async (req, res) => {
  try {
    const { email, password, name, role } = req.body;
    const bcrypt = require('bcryptjs');
    const hashedPassword = await bcrypt.hash(password, 12);
    
    const result = await database.query(
      'INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)',
      [email, hashedPassword, name, role || 'user']
    );
    
    logger.info(`Admin ${req.user.email} created user: ${email}`);
    res.json({ success: true, id: result.insertId });
  } catch (error) {
    logger.error('Create user error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

router.put('/api/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { name, email, role, is_active } = req.body;
    
    await database.query(
      'UPDATE users SET name = ?, email = ?, role = ?, is_active = ? WHERE id = ?',
      [name, email, role, is_active, id]
    );
    
    logger.info(`Admin ${req.user.email} updated user ID: ${id}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('Update user error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

router.delete('/api/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Don't allow deletion of the current admin user
    if (parseInt(id) === req.user.id) {
      return res.status(400).json({ success: false, error: 'Cannot delete your own account' });
    }
    
    await database.query('DELETE FROM users WHERE id = ?', [id]);
    
    logger.info(`Admin ${req.user.email} deleted user ID: ${id}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('Delete user error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

// UI Customization API
router.post('/api/ui-customization', async (req, res) => {
  try {
    const { page, css_content } = req.body;
    
    await database.query(
      'INSERT INTO ui_customizations (page, css_content) VALUES (?, ?) ON DUPLICATE KEY UPDATE css_content = VALUES(css_content)',
      [page, css_content]
    );
    
    logger.info(`Admin ${req.user.email} updated UI customization for page: ${page}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('UI customization error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

// System Settings API
router.post('/api/system-settings', async (req, res) => {
  try {
    const { setting_key, setting_value } = req.body;
    
    await database.query(
      'INSERT INTO system_settings (setting_key, setting_value) VALUES (?, ?) ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)',
      [setting_key, setting_value]
    );
    
    logger.info(`Admin ${req.user.email} updated system setting: ${setting_key}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('System settings error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

// Controller management API
router.post('/api/controllers/:id/bind', async (req, res) => {
  try {
    const { id } = req.params;
    const { user_id } = req.body;
    
    await database.query(
      'UPDATE controllers SET user_id = ? WHERE id = ?',
      [user_id, id]
    );
    
    logger.info(`Admin ${req.user.email} bound controller ${id} to user ${user_id}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('Bind controller error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

router.delete('/api/controllers/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    await database.query('DELETE FROM controllers WHERE id = ?', [id]);
    
    logger.info(`Admin ${req.user.email} deleted controller ID: ${id}`);
    res.json({ success: true });
  } catch (error) {
    logger.error('Delete controller error:', error);
    res.status(400).json({ success: false, error: error.message });
  }
});

// Helper function to get comprehensive system stats
async function getSystemStats() {
  try {
    const [totalUsers] = await database.query('SELECT COUNT(*) as count FROM users');
    const [totalControllers] = await database.query('SELECT COUNT(*) as count FROM controllers');
    const [onlineControllers] = await database.query('SELECT COUNT(*) as count FROM controllers WHERE status = ?', ['online']);
    const [boundControllers] = await database.query('SELECT COUNT(*) as count FROM controllers WHERE user_id IS NOT NULL');
    
    return {
      totalUsers: totalUsers.count || 0,
      total: totalControllers.count || 0,
      online: onlineControllers.count || 0,
      bound: boundControllers.count || 0
    };
  } catch (error) {
    logger.error('Error getting system stats:', error);
    return {
      totalUsers: 0,
      total: 0,
      online: 0,
      bound: 0
    };
  }
}

module.exports = router;