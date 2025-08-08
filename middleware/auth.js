const jwt = require('jsonwebtoken');
const User = require('../models/User');
const logger = require('../config/logger');

// Authentication middleware
const authenticateToken = async (req, res, next) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
      // Check session for web interface
      if (req.session && req.session.user) {
        req.user = await User.findById(req.session.user.id);
        if (req.user) {
          return next();
        }
      }
      return res.status(401).json({ error: 'Access token required' });
    }

    jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
      if (err) {
        return res.status(403).json({ error: 'Invalid or expired token' });
      }

      req.user = await User.findById(decoded.userId);
      if (!req.user) {
        return res.status(403).json({ error: 'User not found' });
      }

      next();
    });
  } catch (error) {
    logger.error('Authentication error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// Session-based authentication for web interface
const requireAuth = async (req, res, next) => {
  try {
    if (!req.session || !req.session.user) {
      if (req.xhr || req.headers.accept.indexOf('json') > -1) {
        return res.status(401).json({ error: 'Authentication required' });
      }
      return res.redirect('/auth/login');
    }

    req.user = await User.findById(req.session.user.id);
    if (!req.user) {
      req.session.destroy();
      if (req.xhr || req.headers.accept.indexOf('json') > -1) {
        return res.status(401).json({ error: 'User not found' });
      }
      return res.redirect('/auth/login');
    }

    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// Admin role middleware
const requireAdmin = (req, res, next) => {
  if (!req.user || req.user.role !== 'admin') {
    if (req.xhr || req.headers.accept.indexOf('json') > -1) {
      return res.status(403).json({ error: 'Admin access required' });
    }
    return res.status(403).render('error', {
      title: 'Access Denied',
      message: 'Admin access required',
      error: { status: 403 }
    });
  }
  next();
};

// Two-factor authentication middleware
const requireTwoFA = (req, res, next) => {
  if (req.user && req.user.twoFaEnabled && !req.session.twoFactorVerified) {
    if (req.xhr || req.headers.accept.indexOf('json') > -1) {
      return res.status(403).json({ error: 'Two-factor authentication required' });
    }
    return res.redirect('/auth/two-factor');
  }
  next();
};

// Rate limiting for sensitive operations
const createRateLimiter = (windowMs, max, message) => {
  const rateLimit = require('express-rate-limit');
  return rateLimit({
    windowMs,
    max,
    message: { error: message },
    standardHeaders: true,
    legacyHeaders: false,
  });
};

// Login rate limiter
const loginLimiter = createRateLimiter(
  15 * 60 * 1000, // 15 minutes
  5, // limit each IP to 5 login requests per windowMs
  'Too many login attempts, please try again later'
);

// Password change rate limiter
const passwordLimiter = createRateLimiter(
  60 * 60 * 1000, // 1 hour
  3, // limit each IP to 3 password change requests per hour
  'Too many password change attempts, please try again later'
);

module.exports = {
  authenticateToken,
  requireAuth,
  requireAdmin,
  requireTwoFA,
  loginLimiter,
  passwordLimiter
};