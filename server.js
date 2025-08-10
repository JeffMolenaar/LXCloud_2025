const express = require('express');
const session = require('express-session');
const path = require('path');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');
require('dotenv').config();

const logger = require('./config/logger');
const database = require('./config/database');
const container = require('./config/container');
const mqttService = require('./controllers/mqttController');

// Import routes
const authRoutes = require('./routes/auth-new');
const dashboardRoutes = require('./routes/dashboard');
const controllerRoutes = require('./routes/controllers');
const userRoutes = require('./routes/users');
const adminRoutes = require('./routes/admin');
const apiRoutes = require('./routes/api');

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.NODE_ENV === 'production' ? 
      ["http://192.168.2.171:3000", "http://localhost:3000"] : 
      ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.2.171:3000"],
    methods: ["GET", "POST"],
    credentials: true
  }
});

// Enhanced security middleware with better local network detection
app.use((req, res, next) => {
  const clientIP = req.headers['x-forwarded-for'] || 
                   req.headers['x-real-ip'] || 
                   req.connection.remoteAddress || 
                   req.socket.remoteAddress ||
                   req.ip || 
                   '127.0.0.1';
  
  const isLocalNetwork = /^(127\.|::1|localhost|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/.test(clientIP) ||
                         clientIP === '::1' ||
                         clientIP.includes('localhost') ||
                         clientIP === 'undefined';
  
  const helmetConfig = {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdnjs.cloudflare.com"],
        scriptSrc: ["'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdnjs.cloudflare.com"],
        imgSrc: ["'self'", "data:", "https:", "blob:"],
        connectSrc: ["'self'", "ws:", "wss:"],
        fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      },
    },
    hsts: false,
    forceHTTPS: false
  };
  
  helmet(helmetConfig)(req, res, next);
});

// CORS configuration
app.use(cors({
  origin: function (origin, callback) {
    if (!origin) return callback(null, true);
    
    const allowedOrigins = [
      'http://localhost:3000',
      'http://127.0.0.1:3000',
      'http://192.168.2.171:3000'
    ];
    
    if (allowedOrigins.includes(origin) || origin.match(/^http:\/\/192\.168\.\d+\.\d+:\d+$/)) {
      return callback(null, true);
    }
    
    return callback(null, true);
  },
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// HTTP enforcement disabling for local networks
app.use((req, res, next) => {
  const clientIP = req.headers['x-forwarded-for'] || 
                   req.headers['x-real-ip'] || 
                   req.connection.remoteAddress || 
                   req.socket.remoteAddress ||
                   req.ip || 
                   '127.0.0.1';
  
  const isLocalNetwork = /^(127\.|::1|localhost|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/.test(clientIP) ||
                         clientIP === '::1' ||
                         clientIP.includes('localhost') ||
                         clientIP === 'undefined';
  
  if (isLocalNetwork || process.env.FORCE_HTTP === 'true') {
    res.removeHeader('Strict-Transport-Security');
    res.removeHeader('Location');
    res.setHeader('X-Local-Network', 'true');
    res.setHeader('X-HTTPS-Redirect', 'disabled');
  }
  
  next();
});

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Enhanced session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false,
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000
  },
  // Add session store configuration for production
  ...(process.env.NODE_ENV === 'production' && {
    store: new (require('express-session').MemoryStore)()
  })
}));

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// View engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Make socket.io and container available to routes
app.use((req, res, next) => {
  req.io = io;
  req.container = container;
  next();
});

// Routes with improved error handling
app.use('/auth', authRoutes);
app.use('/dashboard', dashboardRoutes);
app.use('/controllers', controllerRoutes);
app.use('/users', userRoutes);
app.use('/admin', adminRoutes);
app.use('/api', apiRoutes);

// Enhanced health check endpoint
app.get('/api/health', (req, res) => {
  const sessionService = container.get('sessionService');
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    mockMode: database.mockMode,
    version: process.env.npm_package_version || '1.0.0',
    services: {
      database: database.mockMode ? 'mock' : 'connected',
      session: 'available',
      auth: 'available'
    }
  });
});

// Root route
app.get('/', (req, res) => {
  if (req.session.user) {
    res.redirect('/dashboard');
  } else {
    res.redirect('/auth/login');
  }
});

// Enhanced 404 handler
app.use((req, res) => {
  logger.warn(`404 - Page not found: ${req.url} from IP: ${req.ip}`);
  res.status(404).render('error', { 
    title: 'Page Not Found',
    message: 'The page you are looking for does not exist.',
    error: { status: 404 }
  });
});

// Enhanced error handler
app.use((err, req, res, next) => {
  logger.error(`Error on ${req.method} ${req.url}:`, err);
  
  const status = err.status || 500;
  const message = process.env.NODE_ENV === 'development' ? err.message : 'Internal server error';
  
  if (req.xhr || req.headers.accept?.indexOf('json') > -1) {
    res.status(status).json({ error: message });
  } else {
    res.status(status).render('error', {
      title: 'Error',
      message: message,
      error: process.env.NODE_ENV === 'development' ? err : {}
    });
  }
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`New client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });

  socket.on('join-user-room', (userId) => {
    socket.join(`user-${userId}`);
    logger.info(`User ${userId} joined room`);
  });
});

// Enhanced server initialization with proper service setup
async function startServer() {
  try {
    // Initialize database
    await database.initialize();
    logger.info('Database connected successfully');
    
    // Initialize session service tables
    const sessionService = container.get('sessionService');
    await sessionService.initializeTables();
    logger.info('Session service initialized');
    
    // Initialize MQTT service
    mqttService.initialize(io);
    logger.info('MQTT service initialized');
    
    // Start periodic session cleanup
    setInterval(async () => {
      try {
        await sessionService.cleanupExpiredSessions();
      } catch (error) {
        logger.error('Session cleanup error:', error);
      }
    }, 60 * 60 * 1000); // Every hour
    
    // Start server
    const PORT = process.env.PORT || 3000;
    const HOST = process.env.HOST || '0.0.0.0';
    
    server.listen(PORT, HOST, () => {
      logger.info(`LXCloud server running on ${HOST}:${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Server accessible via: http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
      logger.info('Services initialized: Database, Auth, Session, MQTT');
    });
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    database.close();
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    database.close();
    process.exit(0);
  });
});

startServer();

module.exports = app;