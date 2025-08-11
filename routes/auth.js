const express = require('express');
const QRCode = require('qrcode');
const { body, validationResult } = require('express-validator');
const container = require('../config/container');
const { loginLimiter, passwordLimiter } = require('../middleware/auth');
const logger = require('../config/logger');

const router = express.Router();

// Get services from container
const authService = container.get('authService');
const userService = container.get('userService');
const UserService = require('../services/UserService');

// Enhanced error handler for auth routes
const handleAuthError = (error, res, renderPage, formData = {}) => {
  logger.error('Auth route error:', error);
  
  const errorMessage = error.message || 'An unexpected error occurred';
  
  if (res.headersSent) {
    return;
  }

  // Check if it's an API request
  if (res.req.xhr || res.req.headers.accept?.indexOf('json') > -1) {
    return res.status(400).json({ error: errorMessage });
  }

  // Render error on the page
  res.render(renderPage, {
    title: renderPage.includes('login') ? 'Login - LXCloud' : 'Register - LXCloud',
    error: errorMessage,
    ...formData
  });
};

// Login page
router.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/dashboard');
  }
  res.render('auth/login', { 
    title: 'Login - LXCloud',
    error: null 
  });
});

// Enhanced login handling with better error handling
router.post('/login', 
  loginLimiter,
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').isLength({ min: 1 }).withMessage('Password is required')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return handleAuthError(
          new Error(errors.array()[0].msg),
          res,
          'auth/login'
        );
      }

      const { email, password, twoFactorToken, rememberMe } = req.body;
      
      // Authenticate user
      const user = await authService.authenticateUser(email, password, twoFactorToken);
      
      // Set session with enhanced data
      req.session.user = userService.sanitizeUser(user);
      req.session.loginTime = new Date();
      req.session.ipAddress = req.ip;
      
      // Handle 2FA verification flag
      if (user.twoFaEnabled && twoFactorToken) {
        req.session.twoFactorVerified = true;
      }

      // Extend session if remember me is checked
      if (rememberMe) {
        req.session.cookie.maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
      }

      logger.info(`Successful login for: ${user.email} from IP: ${req.ip}`);
      res.redirect('/dashboard');

    } catch (error) {
      const formData = {
        email: req.body.email,
        requireTwoFA: error.message.includes('Two-factor authentication code required'),
      };
      handleAuthError(error, res, 'auth/login', formData);
    }
  }
);

// Register page
router.get('/register', (req, res) => {
  if (req.session.user) {
    return res.redirect('/dashboard');
  }
  res.render('auth/register', { 
    title: 'Register - LXCloud',
    error: null 
  });
});

// Enhanced register handling
router.post('/register',
  UserService.getCreateValidationRules(),
  async (req, res) => {
    try {
      UserService.validateRequest(req);

      const { email, password, name, address } = req.body;

      // Create user
      const user = await userService.createUser({
        email,
        password,
        name,
        address: address || null
      });

      logger.info(`New user registered: ${user.email} from IP: ${req.ip}`);
      
      // Auto-login after registration
      req.session.user = userService.sanitizeUser(user);
      req.session.loginTime = new Date();
      req.session.ipAddress = req.ip;
      
      res.redirect('/dashboard');

    } catch (error) {
      handleAuthError(error, res, 'auth/register');
    }
  }
);

// Two-factor setup page
router.get('/two-factor-setup', async (req, res) => {
  if (!req.session.user) {
    return res.redirect('/auth/login');
  }

  try {
    const user = await userService.getUserById(req.session.user.id);
    if (user.twoFaEnabled) {
      return res.redirect('/dashboard');
    }

    const twoFAData = await authService.enableTwoFA(user.id);

    res.render('auth/two-factor-setup', {
      title: 'Two-Factor Authentication Setup - LXCloud',
      qrCode: twoFAData.qrCode,
      secret: twoFAData.secret,
      backupCodes: twoFAData.backupCodes
    });

  } catch (error) {
    logger.error('Two-factor setup error:', error);
    res.redirect('/dashboard');
  }
});

// Two-factor setup confirmation
router.post('/two-factor-setup',
  [body('token').isLength({ min: 6, max: 6 }).isNumeric().withMessage('Valid 6-digit code required')],
  async (req, res) => {
    if (!req.session.user) {
      return res.redirect('/auth/login');
    }

    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('auth/two-factor-setup', {
          title: 'Two-Factor Authentication Setup - LXCloud',
          error: errors.array()[0].msg
        });
      }

      const { token } = req.body;
      const isValid = await authService.confirmTwoFA(req.session.user.id, token);
      
      if (isValid) {
        req.session.twoFactorVerified = true;
        logger.info(`Two-factor authentication enabled for: ${req.session.user.email}`);
        res.redirect('/dashboard?twofa=enabled');
      } else {
        res.render('auth/two-factor-setup', {
          title: 'Two-Factor Authentication Setup - LXCloud',
          error: 'Invalid authentication code'
        });
      }

    } catch (error) {
      logger.error('Two-factor confirmation error:', error);
      res.redirect('/dashboard');
    }
  }
);

// Enhanced logout with session cleanup
router.post('/logout', async (req, res) => {
  try {
    if (req.session.user) {
      const userId = req.session.user.id;
      const sessionId = req.sessionID;
      
      // Logout through auth service for proper cleanup
      await authService.logout(userId, sessionId);
      
      logger.info(`User logged out: ${req.session.user.email} from IP: ${req.ip}`);
    }

    req.session.destroy((err) => {
      if (err) {
        logger.error('Session destruction error:', err);
      }
      res.redirect('/auth/login');
    });
  } catch (error) {
    logger.error('Logout error:', error);
    res.redirect('/auth/login');
  }
});

// Enhanced API endpoint for JWT token generation
router.post('/api/token',
  loginLimiter,
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').isLength({ min: 1 }).withMessage('Password is required')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ error: errors.array()[0].msg });
      }

      const { email, password, twoFactorToken } = req.body;
      
      // Authenticate user
      const user = await authService.authenticateUser(email, password, twoFactorToken);
      
      // Generate tokens
      const tokens = await authService.generateTokens(user);

      logger.info(`API token generated for: ${user.email} from IP: ${req.ip}`);

      res.json({
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
        user: userService.sanitizeUser(user)
      });

    } catch (error) {
      logger.error('Token generation error:', error);
      const statusCode = error.message.includes('Invalid') ? 401 : 500;
      res.status(statusCode).json({ error: error.message });
    }
  }
);

// Token refresh endpoint
router.post('/api/refresh',
  [body('refreshToken').isLength({ min: 1 }).withMessage('Refresh token is required')],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ error: errors.array()[0].msg });
      }

      const { refreshToken } = req.body;
      
      // Refresh tokens
      const tokens = await authService.refreshTokens(refreshToken);

      res.json({
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken
      });

    } catch (error) {
      logger.error('Token refresh error:', error);
      res.status(401).json({ error: 'Invalid refresh token' });
    }
  }
);

module.exports = router;