/**
 * Simple test to verify the auth/login endpoint is working
 */

const request = require('supertest');
const app = require('../server');

describe('Auth Login Endpoint', () => {
  
  test('GET /auth/login returns login page', async () => {
    const response = await request(app)
      .get('/auth/login')
      .expect(200);
    
    expect(response.text).toContain('LXCloud Login');
    expect(response.text).toContain('Email Address');
    expect(response.text).toContain('Password');
  });

  test('POST /auth/login with valid credentials redirects to dashboard', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        email: 'admin@lxcloud.local',
        password: 'admin123'
      })
      .expect(302);
    
    expect(response.headers.location).toBe('/dashboard');
  });

  test('POST /auth/login with invalid credentials shows error', async () => {
    const response = await request(app)
      .post('/auth/login')
      .send({
        email: 'invalid@example.com',
        password: 'wrongpassword'
      })
      .expect(200);
    
    expect(response.text).toContain('Invalid email or password');
  });

});