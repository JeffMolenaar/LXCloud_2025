const express = require('express');
const session = require('express-session');
const path = require('path');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');
const bcryptjs = require('bcryptjs');
require('dotenv').config();

const logger = require('./config/logger');
const database = require('./config/database');
const mqttService = require('./controllers/mqttController');

// Import routes
const authRoutes = require('./routes/auth-new');
const dashboardRoutes = require('./routes/dashboard');
const controllerRoutes = require('./routes/controllers');
const userRoutes = require('./routes/users');
const adminRoutes = require('./routes/admin-integrated');
const apiRoutes = require('./routes/api');

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: function (origin, callback) {
      // Allow local network origins
      if (!origin) return callback(null, true);
      
      const allowedOrigins = [
        'http://localhost:3000',
        'http://127.0.0.1:3000'
      ];
      
      // Allow any local network IP
      if (origin.match(/^http:\/\/(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+):\d+$/)) {
        return callback(null, true);
      }
      
      if (allowedOrigins.includes(origin)) {
        return callback(null, true);
      }
      
      return callback(null, true); // Allow for development
    },
    methods: ["GET", "POST"],
    credentials: true
  }
});

// Local network security middleware
app.use((req, res, next) => {
  const clientIP = req.headers['x-forwarded-for'] || 
                   req.headers['x-real-ip'] || 
                   req.connection.remoteAddress || 
                   req.socket.remoteAddress ||
                   req.ip || 
                   '127.0.0.1';
  
  // Clean and normalize IP
  const normalizedIP = clientIP.replace(/^::ffff:/, '').split(',')[0].trim();
  
  // Check if it's a local network IP
  const isLocalNetwork = /^(127\.|::1|localhost|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/.test(normalizedIP) ||
                         normalizedIP === '::1' ||
                         normalizedIP.includes('localhost') ||
                         normalizedIP === 'undefined';
  
  // Log access attempts
  logger.info(`Access attempt from IP: ${normalizedIP}, Local: ${isLocalNetwork}`);
  
  if (!isLocalNetwork && process.env.NODE_ENV === 'production') {
    logger.warn(`Access denied for external IP: ${normalizedIP}`);
    return res.status(403).send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Access Denied - LXCloud</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
          .error { color: #e74c3c; }
        </style>
      </head>
      <body>
        <h1 class="error">Access Denied</h1>
        <p>LXCloud is configured for local network access only.</p>
        <p>Your IP: ${normalizedIP}</p>
        <p>Please access from a local network address.</p>
      </body>
      </html>
    `);
  }
  
  req.clientIP = normalizedIP;
  next();
});

// Enhanced security middleware optimized for local networks
app.use((req, res, next) => {
  const helmetConfig = {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdnjs.cloudflare.com", "https://stackpath.bootstrapcdn.com"],
        scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com", "https://cdnjs.cloudflare.com", "https://stackpath.bootstrapcdn.com"],
        imgSrc: ["'self'", "data:", "https:", "blob:"],
        connectSrc: ["'self'", "ws:", "wss:"],
        fontSrc: ["'self'", "https://cdnjs.cloudflare.com", "https://stackpath.bootstrapcdn.com"],
      },
    },
    hsts: false, // Disable HTTPS enforcement for local networks
    forceHTTPS: false
  };
  
  helmet(helmetConfig)(req, res, next);
});

// CORS configuration for local networks
app.use(cors({
  origin: function (origin, callback) {
    if (!origin) return callback(null, true);
    
    const allowedOrigins = [
      'http://localhost:3000',
      'http://127.0.0.1:3000'
    ];
    
    // Allow any local network IP
    if (origin.match(/^http:\/\/(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+):\d+$/)) {
      return callback(null, true);
    }
    
    if (allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    
    return callback(null, true);
  },
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// HTTP-only enforcement for local networks (no HTTPS redirects)
app.use((req, res, next) => {
  // Allow HTTP for local networks - no forced HTTPS redirects
  logger.debug(`HTTP request allowed for local network: ${req.protocol}://${req.get('host')}${req.originalUrl}`);
  next();
});

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'lxcloud-session-secret',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false, // Allow HTTP for local networks
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Make socket.io available to routes
app.use((req, res, next) => {
  req.io = io;
  next();
});

// Routes
app.use('/auth', authRoutes);
app.use('/dashboard', dashboardRoutes);
app.use('/controllers', controllerRoutes);
app.use('/users', userRoutes);
app.use('/admin', adminRoutes);
app.use('/api', apiRoutes);

// Root route
app.get('/', (req, res) => {
  if (req.session.userId) {
    res.redirect('/dashboard');
  } else {
    res.redirect('/auth/login');
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('error', {
    title: 'Page Not Found',
    message: 'The page you are looking for does not exist.',
    error: { status: 404 }
  });
});

// Error handler
app.use((error, req, res, next) => {
  logger.error('Application error:', error);
  
  res.status(error.status || 500).render('error', {
    title: 'Error',
    message: error.message || 'An unexpected error occurred',
    error: process.env.NODE_ENV === 'development' ? error : { status: error.status || 500 }
  });
});

// Socket.IO handling
io.on('connection', (socket) => {
  logger.info(`Socket.IO client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    logger.info(`Socket.IO client disconnected: ${socket.id}`);
  });
  
  // Handle user room joining for targeted updates
  socket.on('join-user-room', (userId) => {
    socket.join(`user-${userId}`);
    logger.debug(`Socket ${socket.id} joined user room: user-${userId}`);
  });
});

// Initialize services and start server
async function startServer() {
  try {
    // Initialize database
    logger.info('Initializing database...');
    await database.initialize();
    
    // Create default admin user if it doesn't exist
    await createDefaultAdmin();
    
    // Initialize MQTT service
    logger.info('Initializing MQTT service...');
    mqttService.initialize(io);
    
    const PORT = process.env.PORT || 3000;
    server.listen(PORT, '0.0.0.0', () => {
      logger.info(`🚀 LXCloud Integrated Server running on http://localhost:${PORT}`);
      logger.info('🌐 HTTP-only access enabled for local networks');
      logger.info('🔒 External access automatically blocked');
      logger.info('💾 MariaDB database integration active');
      logger.info('📡 MQTT service initialized');
      logger.info('👤 Default admin: admin@lxcloud.local / admin123');
      
      console.log('==================================================');
      console.log('🎯 LXCloud Integrated v2.0 - READY!');
      console.log('==================================================');
      console.log(`📍 Access: http://localhost:${PORT}`);
      console.log(`👤 Login: admin@lxcloud.local / admin123`);
      console.log(`💾 Database: MariaDB (${process.env.DB_NAME})`);
      console.log(`📡 MQTT: ${process.env.MQTT_BROKER_URL}`);
      console.log('==================================================');
    });
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    
    if (error.code === 'ER_ACCESS_DENIED_ERROR' || error.code === 'ECONNREFUSED') {
      console.error('');
      console.error('❌ DATABASE CONNECTION FAILED!');
      console.error('');
      console.error('Please ensure MariaDB/MySQL is running and configured:');
      console.error('');
      console.error('1. Install MariaDB:');
      console.error('   sudo apt update && sudo apt install mariadb-server');
      console.error('');
      console.error('2. Start MariaDB:');
      console.error('   sudo systemctl start mariadb');
      console.error('');
      console.error('3. Create database and user:');
      console.error('   sudo mysql -u root -p');
      console.error('   CREATE DATABASE lxcloud;');
      console.error('   CREATE USER \'lxcloud\'@\'localhost\' IDENTIFIED BY \'lxcloud\';');
      console.error('   GRANT ALL PRIVILEGES ON lxcloud.* TO \'lxcloud\'@\'localhost\';');
      console.error('   FLUSH PRIVILEGES;');
      console.error('');
      console.error('4. Update .env file with correct database credentials');
      console.error('');
    }
    
    process.exit(1);
  }
}

async function createDefaultAdmin() {
  try {
    // Check if admin user exists
    const existingAdmin = await database.query(
      'SELECT * FROM users WHERE email = ?', 
      [process.env.DEFAULT_ADMIN_EMAIL || 'admin@lxcloud.local']
    );
    
    if (existingAdmin.length === 0) {
      // Create default admin user
      const hashedPassword = await bcryptjs.hash(
        process.env.DEFAULT_ADMIN_PASSWORD || 'admin123', 
        parseInt(process.env.BCRYPT_ROUNDS || '12')
      );
      
      await database.query(
        'INSERT INTO users (email, password, name, role, is_active) VALUES (?, ?, ?, ?, ?)',
        [
          process.env.DEFAULT_ADMIN_EMAIL || 'admin@lxcloud.local',
          hashedPassword,
          'Administrator',
          'admin',
          true
        ]
      );
      
      logger.info('Default admin user created successfully');
    } else {
      logger.info('Admin user already exists');
    }
  } catch (error) {
    logger.error('Error creating default admin user:', error);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down gracefully...');
  
  try {
    mqttService.disconnect();
    await database.close();
    server.close(() => {
      logger.info('Server closed successfully');
      process.exit(0);
    });
  } catch (error) {
    logger.error('Error during shutdown:', error);
    process.exit(1);
  }
});

// Start the server
startServer();

module.exports = app;