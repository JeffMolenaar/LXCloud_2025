const express = require('express');
const helmet = require('helmet');

// Create a minimal test app with just the middleware we want to test
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
  
  // Simple test route
  app.get('/', (req, res) => {
    res.send('OK');
  });
  
  return app;
}

describe('HTTPS Redirect Fix', () => {
  const request = require('supertest');
  let app;
  
  beforeEach(() => {
    app = createTestApp();
  });

  test('should allow HTTP access from local network IP', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '192.168.1.100');
    
    // Should not redirect to HTTPS
    expect(response.status).not.toBe(301);
    expect(response.status).not.toBe(302);
    expect(response.status).toBe(200);
    
    // Should not contain HTTPS redirect headers
    if (response.headers.location) {
      expect(response.headers.location).not.toMatch(/^https:/);
    }
    
    // Should have local network header
    expect(response.headers['x-local-network']).toBe('true');
  });

  test('should allow HTTP access from localhost', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '127.0.0.1');
    
    // Should not redirect to HTTPS
    expect(response.status).not.toBe(301);
    expect(response.status).not.toBe(302);
    expect(response.status).toBe(200);
    
    // Should have local network header
    expect(response.headers['x-local-network']).toBe('true');
  });

  test('should allow HTTP access from 10.x.x.x network', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '10.0.0.100');
    
    // Should not redirect to HTTPS
    expect(response.status).not.toBe(301);
    expect(response.status).not.toBe(302);
    expect(response.status).toBe(200);
    
    // Should have local network header
    expect(response.headers['x-local-network']).toBe('true');
  });

  test('should allow HTTP access from 172.16-31.x.x network', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '172.20.0.100');
    
    // Should not redirect to HTTPS
    expect(response.status).not.toBe(301);
    expect(response.status).not.toBe(302);
    expect(response.status).toBe(200);
    
    // Should have local network header
    expect(response.headers['x-local-network']).toBe('true');
  });

  test('should not set HSTS header for local network requests', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '192.168.1.100');
    
    // Should not have Strict-Transport-Security header
    expect(response.headers['strict-transport-security']).toBeUndefined();
  });
  
  test('should not redirect external IP requests but also should not set local network header', async () => {
    const response = await request(app)
      .get('/')
      .set('X-Real-IP', '8.8.8.8'); // External IP
    
    // Should not redirect to HTTPS (we disabled forceHTTPS globally)
    expect(response.status).not.toBe(301);
    expect(response.status).not.toBe(302);
    expect(response.status).toBe(200);
    
    // Should not have local network header
    expect(response.headers['x-local-network']).toBeUndefined();
  });
});