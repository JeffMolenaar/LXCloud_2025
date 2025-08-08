const express = require('express');
const { requireAuth, requireTwoFA, passwordLimiter } = require('../middleware/auth');
const { body, validationResult } = require('express-validator');
const logger = require('../config/logger');

const router = express.Router();

// Apply authentication middleware
router.use(requireAuth);
router.use(requireTwoFA);

// User profile page
router.get('/profile', (req, res) => {
  res.render('users/profile', {
    title: 'Profile Settings - LXCloud',
    user: req.user.toJSON(),
    messages: {
      success: req.query.success === 'updated' ? 'Profile updated successfully!' : null
    }
  });
});

// Update profile
router.post('/profile',
  [
    body('name').isLength({ min: 2, max: 255 }).withMessage('Name must be between 2-255 characters'),
    body('email').isEmail().normalizeEmail().withMessage('Valid email required'),
    body('address').optional().isLength({ max: 500 }).withMessage('Address too long')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('users/profile', {
          title: 'Profile Settings - LXCloud',
          user: req.user.toJSON(),
          error: errors.array()[0].msg
        });
      }

      const { name, email, address } = req.body;
      
      await req.user.update({
        name,
        email,
        address: address || null
      });
      
      // Update session data
      req.session.user = req.user.toJSON();
      
      logger.info(`User profile updated: ${req.user.email}`);
      res.redirect('/users/profile?success=updated');
      
    } catch (error) {
      logger.error('Profile update error:', error);
      res.render('users/profile', {
        title: 'Profile Settings - LXCloud',
        user: req.user.toJSON(),
        error: 'An error occurred while updating your profile'
      });
    }
  }
);

// Security settings page
router.get('/security', (req, res) => {
  res.render('users/security', {
    title: 'Security Settings - LXCloud',
    user: req.user.toJSON(),
    messages: {
      success: req.query.success === 'password' ? 'Password changed successfully!' : 
               req.query.success === '2fa-enabled' ? 'Two-factor authentication enabled!' :
               req.query.success === '2fa-disabled' ? 'Two-factor authentication disabled!' : null
    }
  });
});

// Change password
router.post('/security/password',
  passwordLimiter,
  [
    body('currentPassword').notEmpty().withMessage('Current password is required'),
    body('newPassword').isLength({ min: 8 }).withMessage('New password must be at least 8 characters'),
    body('confirmPassword').custom((value, { req }) => {
      if (value !== req.body.newPassword) {
        throw new Error('Passwords do not match');
      }
      return true;
    })
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('users/security', {
          title: 'Security Settings - LXCloud',
          user: req.user.toJSON(),
          error: errors.array()[0].msg
        });
      }

      const { currentPassword, newPassword } = req.body;
      
      // Verify current password
      const isValidPassword = await req.user.validatePassword(currentPassword);
      if (!isValidPassword) {
        return res.render('users/security', {
          title: 'Security Settings - LXCloud',
          user: req.user.toJSON(),
          error: 'Current password is incorrect'
        });
      }
      
      // Update password
      await req.user.updatePassword(newPassword);
      
      logger.info(`Password changed for user: ${req.user.email}`);
      res.redirect('/users/security?success=password');
      
    } catch (error) {
      logger.error('Password change error:', error);
      res.render('users/security', {
        title: 'Security Settings - LXCloud',
        user: req.user.toJSON(),
        error: 'An error occurred while changing your password'
      });
    }
  }
);

// Disable 2FA
router.post('/security/disable-2fa', async (req, res) => {
  try {
    if (!req.user.twoFaEnabled) {
      return res.redirect('/users/security');
    }
    
    await req.user.disableTwoFA();
    
    // Update session
    req.session.user = req.user.toJSON();
    req.session.twoFactorVerified = false;
    
    logger.info(`Two-factor authentication disabled for user: ${req.user.email}`);
    res.redirect('/users/security?success=2fa-disabled');
    
  } catch (error) {
    logger.error('2FA disable error:', error);
    res.render('users/security', {
      title: 'Security Settings - LXCloud',
      user: req.user.toJSON(),
      error: 'An error occurred while disabling two-factor authentication'
    });
  }
});

// Delete account page
router.get('/delete-account', (req, res) => {
  res.render('users/delete-account', {
    title: 'Delete Account - LXCloud',
    user: req.user.toJSON()
  });
});

// Delete account
router.post('/delete-account',
  [body('password').notEmpty().withMessage('Password is required')],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('users/delete-account', {
          title: 'Delete Account - LXCloud',
          user: req.user.toJSON(),
          error: errors.array()[0].msg
        });
      }

      const { password } = req.body;
      
      // Verify password
      const isValidPassword = await req.user.validatePassword(password);
      if (!isValidPassword) {
        return res.render('users/delete-account', {
          title: 'Delete Account - LXCloud',
          user: req.user.toJSON(),
          error: 'Password is incorrect'
        });
      }
      
      // Deactivate user (this unbinds all controllers)
      await req.user.deactivate();
      
      // Destroy session
      req.session.destroy();
      
      logger.info(`User account deleted: ${req.user.email}`);
      res.redirect('/auth/login?message=account-deleted');
      
    } catch (error) {
      logger.error('Account deletion error:', error);
      res.render('users/delete-account', {
        title: 'Delete Account - LXCloud',
        user: req.user.toJSON(),
        error: 'An error occurred while deleting your account'
      });
    }
  }
);

module.exports = router;