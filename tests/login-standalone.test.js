/**
 * Standalone test for login page functionality without database dependency
 */

const express = require('express');
const session = require('express-session');
const path = require('path');
const helmet = require('helmet');
const request = require('supertest');

// Create a test app with minimal login functionality
function createTestApp() {
  const app = express();
  
  // Security middleware - disable HTTPS enforcement for local networks
  app.use((req, res, next) => {
    const clientIP = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection.remoteAddress || req.ip;
    const isLocalNetwork = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1|localhost)/.test(clientIP);
    
    // Configure helmet based on request source
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
      hsts: false, // Always disable HTTP Strict Transport Security
      forceHTTPS: false // Always ensure no HTTPS redirection
    };
    
    // Apply helmet with local network friendly settings
    helmet(helmetConfig)(req, res, next);
  });

  // Middleware to prevent HTTPS redirects for local network requests
  app.use((req, res, next) => {
    const clientIP = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection.remoteAddress || req.ip;
    const isLocalNetwork = /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1|localhost)/.test(clientIP);
    
    // For local network requests, ensure HTTP is allowed
    if (isLocalNetwork) {
      // Override any HTTPS redirect headers that might have been set
      res.removeHeader('Strict-Transport-Security');
      res.removeHeader('Location');
      
      // Set headers to allow HTTP for local networks
      res.setHeader('X-Local-Network', 'true');
    }
    
    next();
  });

  // Body parsing middleware
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // Session configuration
  app.use(session({
    secret: 'test-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: false, // Always use HTTP, never force HTTPS
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
  }));

  // Static files
  app.use(express.static(path.join(__dirname, '..', 'public')));

  // View engine setup
  app.set('views', path.join(__dirname, '..', 'views'));
  app.set('view engine', 'ejs');

  // Login page route
  app.get('/auth/login', (req, res) => {
    if (req.session.user) {
      return res.redirect('/dashboard');
    }
    res.render('auth/login', { 
      title: 'Login - LXCloud',
      error: null 
    });
  });

  // Register page route
  app.get('/auth/register', (req, res) => {
    if (req.session.user) {
      return res.redirect('/dashboard');
    }
    res.render('auth/register', { 
      title: 'Register - LXCloud',
      error: null 
    });
  });

  // Mock login endpoint for testing
  app.post('/auth/login', (req, res) => {
    const { email, password } = req.body;
    
    // Mock successful login
    if (email && password) {
      req.session.user = { email: email, id: 1 };
      return res.redirect('/dashboard');
    }
    
    res.render('auth/login', {
      title: 'Login - LXCloud',
      error: 'Invalid email or password'
    });
  });

  // Mock dashboard route
  app.get('/dashboard', (req, res) => {
    if (!req.session.user) {
      return res.redirect('/auth/login');
    }
    res.send('Dashboard - Login successful!');
  });

  // Root route
  app.get('/', (req, res) => {
    if (req.session.user) {
      res.redirect('/dashboard');
    } else {
      res.redirect('/auth/login');
    }
  });

  return app;
}

describe('Login Page Functionality (Standalone)', () => {
  let app;

  beforeEach(() => {
    app = createTestApp();
  });

  test('GET /auth/login should render login page successfully', async () => {
    const response = await request(app)
      .get('/auth/login')
      .expect(200);
    
    expect(response.text).toContain('LXCloud Login');
    expect(response.text).toContain('Email Address');
    expect(response.text).toContain('Password');
    expect(response.text).toContain('Sign In');
  });

  test('GET /auth/register should render register page successfully', async () => {
    const response = await request(app)
      .get('/auth/register')
      .expect(200);
    
    expect(response.text).toContain('Create Account');
    expect(response.text).toContain('Email Address');
    expect(response.text).toContain('Password');
    expect(response.text).toContain('Create Account');
  });

  test('Root route should redirect to login page', async () => {
    const response = await request(app)
      .get('/')
      .expect(302);
    
    expect(response.headers.location).toBe('/auth/login');
  });

  test('Login page should allow HTTP access from local network', async () => {
    const response = await request(app)
      .get('/auth/login')
      .set('X-Real-IP', '192.168.1.100')
      .expect(200);
    
    // Should not redirect to HTTPS
    expect(response.status).toBe(200);
    expect(response.headers['x-local-network']).toBe('true');
    expect(response.headers['strict-transport-security']).toBeUndefined();
  });

  test('POST /auth/login with credentials should work', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        email: 'test@example.com',
        password: 'testpassword'
      })
      .expect(302);
    
    expect(response.headers.location).toBe('/dashboard');
  });

  test('Login should work over HTTP for local network requests', async () => {
    const response = await request(app)
      .post('/auth/login')
      .set('X-Real-IP', '192.168.1.100')
      .send({
        email: 'test@example.com',
        password: 'testpassword'
      })
      .expect(302);
    
    expect(response.headers.location).toBe('/dashboard');
    expect(response.headers['x-local-network']).toBe('true');
  });

});