const express = require('express');
const session = require('express-session');
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');

const app = express();

// Simple logging
function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

// Middleware setup
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Session configuration - HTTP only, no secure flag
app.use(session({
  secret: 'lxcloud-simple-secret',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false, // HTTP only
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// View engine
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Simple user storage (file-based)
const USERS_FILE = path.join(__dirname, 'data', 'users.json');
const DATA_DIR = path.join(__dirname, 'data');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Initialize users file with default admin user
function initializeUsers() {
  if (!fs.existsSync(USERS_FILE)) {
    const defaultAdmin = {
      id: 1,
      email: 'admin@lxcloud.local',
      password: bcrypt.hashSync('admin123', 10),
      name: 'Administrator',
      role: 'admin',
      created_at: new Date().toISOString()
    };
    
    fs.writeFileSync(USERS_FILE, JSON.stringify([defaultAdmin], null, 2));
    log('Created default admin user: admin@lxcloud.local / admin123');
  }
}

// User management functions
function getUsers() {
  try {
    if (fs.existsSync(USERS_FILE)) {
      return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8'));
    }
    return [];
  } catch (error) {
    log(`Error reading users: ${error.message}`);
    return [];
  }
}

function saveUsers(users) {
  try {
    fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
    return true;
  } catch (error) {
    log(`Error saving users: ${error.message}`);
    return false;
  }
}

function findUserByEmail(email) {
  const users = getUsers();
  return users.find(user => user.email === email);
}

function findUserById(id) {
  const users = getUsers();
  return users.find(user => user.id === id);
}

// Middleware to check if user is authenticated
function requireAuth(req, res, next) {
  if (req.session.user) {
    next();
  } else {
    res.redirect('/login');
  }
}

// Middleware to check if user is admin
function requireAdmin(req, res, next) {
  if (req.session.user && req.session.user.role === 'admin') {
    next();
  } else {
    res.status(403).render('error', {
      title: 'Access Denied',
      message: 'Admin access required',
      error: { status: 403 }
    });
  }
}

// Middleware to ensure local network access only
function requireLocalNetwork(req, res, next) {
  const clientIP = req.headers['x-forwarded-for'] || 
                   req.headers['x-real-ip'] || 
                   req.connection.remoteAddress || 
                   req.socket.remoteAddress ||
                   req.ip || 
                   '127.0.0.1';
  
  // Clean the IP address
  const cleanIP = clientIP.replace(/^::ffff:/, '');
  
  const isLocalNetwork = /^(127\.|::1|localhost|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/.test(cleanIP) ||
                         cleanIP === '::1' ||
                         cleanIP.includes('localhost') ||
                         cleanIP === 'undefined';
  
  if (!isLocalNetwork) {
    log(`Blocked access from non-local IP: ${cleanIP}`);
    return res.status(403).json({ error: 'Access denied - local network only' });
  }
  
  next();
}

// Apply local network restriction to all routes
app.use(requireLocalNetwork);

// Routes
app.get('/', (req, res) => {
  if (req.session.user) {
    res.redirect('/dashboard');
  } else {
    res.redirect('/login');
  }
});

// Login page
app.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/dashboard');
  }
  
  res.render('auth/login-simple', {
    title: 'LXCloud Login',
    error: null,
    email: ''
  });
});

// Login handler
app.post('/login', async (req, res) => {
  const { email, password } = req.body;
  
  if (!email || !password) {
    return res.render('auth/login-simple', {
      title: 'LXCloud Login',
      error: 'Email and password are required',
      email: email || ''
    });
  }
  
  const user = findUserByEmail(email);
  
  if (!user) {
    return res.render('auth/login-simple', {
      title: 'LXCloud Login',
      error: 'Invalid email or password',
      email: email
    });
  }
  
  const passwordMatch = await bcrypt.compare(password, user.password);
  
  if (!passwordMatch) {
    return res.render('auth/login-simple', {
      title: 'LXCloud Login',
      error: 'Invalid email or password',
      email: email
    });
  }
  
  // Set session
  req.session.user = {
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role
  };
  
  log(`User logged in: ${user.email}`);
  res.redirect('/dashboard');
});

// Logout
app.post('/logout', (req, res) => {
  const userEmail = req.session.user ? req.session.user.email : 'unknown';
  req.session.destroy((err) => {
    if (err) {
      log(`Logout error for ${userEmail}: ${err.message}`);
    } else {
      log(`User logged out: ${userEmail}`);
    }
    res.redirect('/login');
  });
});

// Dashboard
app.get('/dashboard', requireAuth, (req, res) => {
  res.render('dashboard/dashboard-simple', {
    title: 'LXCloud Dashboard',
    user: req.session.user,
    stats: {
      totalControllers: 0,
      onlineControllers: 0,
      totalUsers: getUsers().length,
      systemStatus: 'running'
    }
  });
});

// User management (admin only)
app.get('/users', requireAuth, requireAdmin, (req, res) => {
  const users = getUsers();
  res.render('admin/users-simple', {
    title: 'User Management',
    user: req.session.user,
    users: users
  });
});

// API endpoints
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: '2.0.0-simple',
    environment: 'simple',
    services: {
      database: 'file-based',
      session: 'available',
      auth: 'available'
    },
    mockMode: false
  });
});

app.get('/api/ping', (req, res) => {
  res.json({
    status: 'pong',
    timestamp: new Date().toISOString(),
    server: 'LXCloud-Simple'
  });
});

// Error handling
app.use((req, res) => {
  res.status(404).render('error', {
    title: 'Page Not Found',
    message: 'The page you are looking for does not exist.',
    error: { status: 404 }
  });
});

app.use((err, req, res, next) => {
  log(`Error: ${err.message}`);
  res.status(err.status || 500).render('error', {
    title: 'Error',
    message: err.message || 'Internal server error',
    error: { status: err.status || 500 }
  });
});

// Start server
function startServer() {
  const PORT = process.env.PORT || 3000;
  const HOST = '0.0.0.0'; // Listen on all interfaces for local network access
  
  // Initialize data
  initializeUsers();
  
  app.listen(PORT, HOST, (err) => {
    if (err) {
      log(`Failed to start server: ${err.message}`);
      process.exit(1);
    }
    
    log(`LXCloud Simple server running on ${HOST}:${PORT}`);
    log(`Environment: simplified`);
    log(`Server accessible via: http://localhost:${PORT}`);
    log('Features: File-based auth, Local network only, HTTP only');
    
    // Log network interfaces for easier access
    try {
      const os = require('os');
      const interfaces = os.networkInterfaces();
      log('Network interfaces:');
      Object.keys(interfaces).forEach(name => {
        interfaces[name].forEach(iface => {
          if (iface.family === 'IPv4' && !iface.internal) {
            log(`  ${name}: http://${iface.address}:${PORT}`);
          }
        });
      });
    } catch (error) {
      // Ignore network interface errors
    }
  });
}

startServer();

module.exports = app;