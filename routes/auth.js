const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const QRCode = require('qrcode');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');
const { loginLimiter, passwordLimiter } = require('../middleware/auth');
const logger = require('../config/logger');

const router = express.Router();

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

// Login handling
router.post('/login', 
  loginLimiter,
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 1 })
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('auth/login', {
          title: 'Login - LXCloud',
          error: 'Please provide valid email and password'
        });
      }

      const { email, password, twoFactorToken } = req.body;
      
      // Find user
      const user = await User.findByEmail(email);
      if (!user) {
        return res.render('auth/login', {
          title: 'Login - LXCloud',
          error: 'Invalid email or password'
        });
      }

      // Validate password
      const isValidPassword = await user.validatePassword(password);
      if (!isValidPassword) {
        return res.render('auth/login', {
          title: 'Login - LXCloud',
          error: 'Invalid email or password'
        });
      }

      // Check 2FA if enabled
      if (user.twoFaEnabled) {
        if (!twoFactorToken) {
          return res.render('auth/login', {
            title: 'Login - LXCloud',
            error: 'Two-factor authentication code required',
            requireTwoFA: true,
            email: email
          });
        }

        const isValidTwoFA = await user.verifyTwoFA(twoFactorToken);
        if (!isValidTwoFA) {
          return res.render('auth/login', {
            title: 'Login - LXCloud',
            error: 'Invalid two-factor authentication code',
            requireTwoFA: true,
            email: email
          });
        }

        req.session.twoFactorVerified = true;
      }

      // Update last login
      await user.updateLastLogin();

      // Set session
      req.session.user = user.toJSON();
      
      logger.info(`User logged in: ${user.email}`);
      res.redirect('/dashboard');

    } catch (error) {
      logger.error('Login error:', error);
      res.render('auth/login', {
        title: 'Login - LXCloud',
        error: 'An error occurred during login'
      });
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

// Register handling
router.post('/register',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
    body('name').isLength({ min: 2 }).withMessage('Name must be at least 2 characters'),
    body('confirmPassword').custom((value, { req }) => {
      if (value !== req.body.password) {
        throw new Error('Passwords do not match');
      }
      return true;
    })
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.render('auth/register', {
          title: 'Register - LXCloud',
          error: errors.array()[0].msg
        });
      }

      const { email, password, name, address } = req.body;

      // Check if user already exists
      const existingUser = await User.findByEmail(email);
      if (existingUser) {
        return res.render('auth/register', {
          title: 'Register - LXCloud',
          error: 'Email already registered'
        });
      }

      // Create user
      const user = await User.create({
        email,
        password,
        name,
        address: address || null
      });

      logger.info(`New user registered: ${user.email}`);
      
      // Auto-login after registration
      req.session.user = user.toJSON();
      res.redirect('/dashboard');

    } catch (error) {
      logger.error('Registration error:', error);
      res.render('auth/register', {
        title: 'Register - LXCloud',
        error: 'An error occurred during registration'
      });
    }
  }
);

// Two-factor setup page
router.get('/two-factor-setup', async (req, res) => {
  if (!req.session.user) {
    return res.redirect('/auth/login');
  }

  try {
    const user = await User.findById(req.session.user.id);
    if (user.twoFaEnabled) {
      return res.redirect('/dashboard');
    }

    const secret = await user.enableTwoFA();
    const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

    res.render('auth/two-factor-setup', {
      title: 'Two-Factor Authentication Setup - LXCloud',
      qrCode: qrCodeUrl,
      secret: secret.base32
    });

  } catch (error) {
    logger.error('Two-factor setup error:', error);
    res.redirect('/dashboard');
  }
});

// Two-factor setup confirmation
router.post('/two-factor-setup',
  [body('token').isLength({ min: 6, max: 6 }).isNumeric()],
  async (req, res) => {
    if (!req.session.user) {
      return res.redirect('/auth/login');
    }

    try {
      const { token } = req.body;
      const user = await User.findById(req.session.user.id);
      
      const isValid = await user.confirmTwoFA(token);
      if (isValid) {
        req.session.twoFactorVerified = true;
        logger.info(`Two-factor authentication enabled for: ${user.email}`);
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

// Logout
router.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      logger.error('Logout error:', err);
    }
    res.redirect('/auth/login');
  });
});

// API endpoint for JWT token generation
router.post('/api/token',
  loginLimiter,
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 1 })
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ error: 'Invalid email or password' });
      }

      const { email, password, twoFactorToken } = req.body;
      
      const user = await User.findByEmail(email);
      if (!user || !await user.validatePassword(password)) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }

      if (user.twoFaEnabled) {
        if (!twoFactorToken || !await user.verifyTwoFA(twoFactorToken)) {
          return res.status(401).json({ error: 'Invalid two-factor authentication code' });
        }
      }

      const token = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN || '1h' }
      );

      const refreshToken = jwt.sign(
        { userId: user.id },
        process.env.JWT_REFRESH_SECRET,
        { expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d' }
      );

      await user.updateLastLogin();

      res.json({
        token,
        refreshToken,
        user: user.toJSON()
      });

    } catch (error) {
      logger.error('Token generation error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

module.exports = router;