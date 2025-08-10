#!/usr/bin/env node

const http = require('http');
const querystring = require('querystring');

// Test configuration
const HOST = 'localhost';
const PORT = 3000;
const BASE_URL = `http://${HOST}:${PORT}`;

console.log('🧪 LXCloud Simple - Comprehensive Test Suite');
console.log(`Testing server at: ${BASE_URL}`);
console.log('=' .repeat(60));

let testsPassed = 0;
let testsFailed = 0;

function log(message, type = 'info') {
  const timestamp = new Date().toLocaleTimeString();
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  console.log(`[${timestamp}] ${icons[type] || 'ℹ️'} ${message}`);
}

function makeRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', reject);
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

async function test(name, testFn) {
  try {
    log(`Testing: ${name}`);
    await testFn();
    testsPassed++;
    log(`✓ PASS: ${name}`, 'success');
  } catch (error) {
    testsFailed++;
    log(`✗ FAIL: ${name} - ${error.message}`, 'error');
  }
}

async function runTests() {
  let sessionCookie = null;

  // Test 1: Health Check
  await test('Health check endpoint', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/health',
      method: 'GET'
    });
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200, got ${response.statusCode}`);
    }
    
    const health = JSON.parse(response.body);
    if (health.status !== 'ok') {
      throw new Error(`Expected status 'ok', got '${health.status}'`);
    }
    
    if (!health.version.includes('simple')) {
      throw new Error('Expected simple version identifier');
    }
  });

  // Test 2: Ping endpoint
  await test('Ping endpoint', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/ping',
      method: 'GET'
    });
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200, got ${response.statusCode}`);
    }
    
    const ping = JSON.parse(response.body);
    if (ping.status !== 'pong') {
      throw new Error(`Expected 'pong', got '${ping.status}'`);
    }
  });

  // Test 3: Root redirect
  await test('Root redirect to login', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/',
      method: 'GET'
    });
    
    if (response.statusCode !== 302) {
      throw new Error(`Expected 302 redirect, got ${response.statusCode}`);
    }
    
    if (response.headers.location !== '/login') {
      throw new Error(`Expected redirect to /login, got ${response.headers.location}`);
    }
  });

  // Test 4: Login page loads
  await test('Login page loads', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/login',
      method: 'GET'
    });
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200, got ${response.statusCode}`);
    }
    
    if (!response.body.includes('LXCloud Simple')) {
      throw new Error('Login page does not contain expected content');
    }
    
    if (!response.body.includes('admin@lxcloud.local')) {
      throw new Error('Default admin email not found on login page');
    }
  });

  // Test 5: Invalid login
  await test('Invalid login credentials', async () => {
    const postData = querystring.stringify({
      email: 'wrong@example.com',
      password: 'wrongpassword'
    });
    
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/login',
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, postData);
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200 (error page), got ${response.statusCode}`);
    }
    
    if (!response.body.includes('Invalid email or password')) {
      throw new Error('Expected error message not found');
    }
  });

  // Test 6: Valid login
  await test('Valid login credentials', async () => {
    const postData = querystring.stringify({
      email: 'admin@lxcloud.local',
      password: 'admin123'
    });
    
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/login',
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, postData);
    
    if (response.statusCode !== 302) {
      throw new Error(`Expected 302 redirect, got ${response.statusCode}`);
    }
    
    if (response.headers.location !== '/dashboard') {
      throw new Error(`Expected redirect to /dashboard, got ${response.headers.location}`);
    }
    
    // Extract session cookie
    const setCookie = response.headers['set-cookie'];
    if (!setCookie || !setCookie[0]) {
      throw new Error('No session cookie set');
    }
    
    sessionCookie = setCookie[0].split(';')[0];
    log(`Session cookie obtained: ${sessionCookie.substring(0, 50)}...`);
  });

  // Test 7: Dashboard access with session
  await test('Dashboard access with session', async () => {
    if (!sessionCookie) {
      throw new Error('No session cookie available');
    }
    
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/dashboard',
      method: 'GET',
      headers: {
        'Cookie': sessionCookie
      }
    });
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200, got ${response.statusCode}`);
    }
    
    if (!response.body.includes('Administrator')) {
      throw new Error('Dashboard does not show admin user');
    }
    
    if (!response.body.includes('File-based Authentication')) {
      throw new Error('Dashboard features not displayed');
    }
  });

  // Test 8: User management access
  await test('User management access', async () => {
    if (!sessionCookie) {
      throw new Error('No session cookie available');
    }
    
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/users',
      method: 'GET',
      headers: {
        'Cookie': sessionCookie
      }
    });
    
    if (response.statusCode !== 200) {
      throw new Error(`Expected 200, got ${response.statusCode}`);
    }
    
    if (!response.body.includes('User Management')) {
      throw new Error('User management page not loaded');
    }
    
    if (!response.body.includes('1 Total Users')) {
      throw new Error('User count not displayed correctly');
    }
  });

  // Test 9: Dashboard access without session
  await test('Dashboard access without session', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/dashboard',
      method: 'GET'
    });
    
    if (response.statusCode !== 302) {
      throw new Error(`Expected 302 redirect, got ${response.statusCode}`);
    }
    
    if (response.headers.location !== '/login') {
      throw new Error(`Expected redirect to /login, got ${response.headers.location}`);
    }
  });

  // Test 10: Local network restriction
  await test('Local network access restriction', async () => {
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/api/health',
      method: 'GET',
      headers: {
        'X-Forwarded-For': '8.8.8.8'  // Simulate external IP
      }
    });
    
    if (response.statusCode !== 403) {
      throw new Error(`Expected 403 forbidden, got ${response.statusCode}`);
    }
    
    const error = JSON.parse(response.body);
    if (!error.error.includes('local network only')) {
      throw new Error('Expected local network restriction message');
    }
  });

  // Test 11: Logout functionality
  await test('Logout functionality', async () => {
    if (!sessionCookie) {
      throw new Error('No session cookie available');
    }
    
    const response = await makeRequest({
      hostname: HOST,
      port: PORT,
      path: '/logout',
      method: 'POST',
      headers: {
        'Cookie': sessionCookie
      }
    });
    
    if (response.statusCode !== 302) {
      throw new Error(`Expected 302 redirect, got ${response.statusCode}`);
    }
    
    if (response.headers.location !== '/login') {
      throw new Error(`Expected redirect to /login, got ${response.headers.location}`);
    }
  });

  // Test 12: File system data storage
  await test('User data file created', async () => {
    const fs = require('fs');
    const path = require('path');
    
    const dataFile = path.join(__dirname, 'data', 'users.json');
    
    if (!fs.existsSync(dataFile)) {
      throw new Error('Users data file not created');
    }
    
    const users = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
    
    if (!Array.isArray(users) || users.length === 0) {
      throw new Error('Users data file is empty or invalid');
    }
    
    if (users[0].email !== 'admin@lxcloud.local') {
      throw new Error('Default admin user not found in data file');
    }
    
    log(`User data file contains ${users.length} user(s)`);
  });

  // Summary
  console.log('\n' + '='.repeat(60));
  log(`Tests completed: ${testsPassed + testsFailed} total`);
  log(`Passed: ${testsPassed}`, 'success');
  log(`Failed: ${testsFailed}`, testsFailed > 0 ? 'error' : 'success');
  
  if (testsFailed === 0) {
    log('🎉 All tests passed! LXCloud Simple is working correctly.', 'success');
    console.log('\n📋 Verified Features:');
    console.log('  ✅ HTTP-only access (no HTTPS redirects)');
    console.log('  ✅ Local network restriction enforced');
    console.log('  ✅ File-based authentication working');
    console.log('  ✅ Session management functional');
    console.log('  ✅ Dashboard and user management accessible');
    console.log('  ✅ Login/logout flow working');
    console.log('  ✅ Data persistence to JSON files');
    console.log('  ✅ API endpoints responding correctly');
    
    console.log('\n🚀 Ready for use:');
    console.log(`  • Visit: http://localhost:${PORT}`);
    console.log('  • Login: admin@lxcloud.local / admin123');
    console.log('  • Access restricted to local network only');
  } else {
    log('❌ Some tests failed. Please check the output above.', 'error');
    process.exit(1);
  }
}

// Run the tests
runTests().catch(error => {
  log(`Test suite failed: ${error.message}`, 'error');
  process.exit(1);
});