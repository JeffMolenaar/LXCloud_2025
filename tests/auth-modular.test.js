/**
 * Comprehensive tests for the new modular authentication system
 */

const request = require('supertest');
const bcrypt = require('bcryptjs');

// Mock dependencies before importing the app
jest.mock('../config/database', () => ({
  initialize: jest.fn(),
  query: jest.fn(),
  mockMode: true,
  close: jest.fn()
}));

jest.mock('../controllers/mqttController', () => ({
  initialize: jest.fn()
}));

// Create a test app with minimal dependencies
const express = require('express');
const session = require('express-session');
const path = require('path');

// Test services
const AuthService = require('../services/AuthService');
const UserService = require('../services/UserService');
const UserRepository = require('../repositories/UserRepository');

describe('Modular Authentication System', () => {
  let app;
  let mockDatabase;
  let userRepository;
  let authService;
  let userService;

  beforeEach(() => {
    // Create mock database
    mockDatabase = {
      query: jest.fn()
    };

    // Create test services
    userRepository = new UserRepository(mockDatabase);
    authService = new AuthService(userRepository, null); // SessionService not needed for these tests
    userService = new UserService(userRepository, authService);

    // Create test app
    app = express();
    app.use(express.json());
    app.use(express.urlencoded({ extended: true }));
    app.use(session({
      secret: 'test-secret',
      resave: false,
      saveUninitialized: false,
      cookie: { secure: false }
    }));

    // Set up view engine for error responses
    app.set('views', path.join(__dirname, '..', 'views'));
    app.set('view engine', 'ejs');

    // Mock routes for testing
    app.post('/test/auth', async (req, res) => {
      try {
        const { email, password } = req.body;
        const user = await authService.authenticateUser(email, password);
        res.json({ success: true, user: userService.sanitizeUser(user) });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    app.post('/test/create-user', async (req, res) => {
      try {
        const user = await userService.createUser(req.body);
        res.json({ success: true, user: userService.sanitizeUser(user) });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });
  });

  describe('AuthService', () => {
    test('should authenticate valid user', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        password: await bcrypt.hash('password123', 12),
        twoFaEnabled: false
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(mockUser);
      userRepository.updateLastLogin = jest.fn().mockResolvedValue();

      const user = await authService.authenticateUser('test@example.com', 'password123');
      
      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(userRepository.updateLastLogin).toHaveBeenCalledWith(1);
    });

    test('should reject invalid password', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        password: await bcrypt.hash('password123', 12),
        twoFaEnabled: false
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(mockUser);

      await expect(
        authService.authenticateUser('test@example.com', 'wrongpassword')
      ).rejects.toThrow('Invalid email or password');
    });

    test('should reject non-existent user', async () => {
      userRepository.findByEmail = jest.fn().mockResolvedValue(null);

      await expect(
        authService.authenticateUser('nonexistent@example.com', 'password123')
      ).rejects.toThrow('Invalid email or password');
    });

    test('should require 2FA token when enabled', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        password: await bcrypt.hash('password123', 12),
        twoFaEnabled: true,
        twoFaSecret: 'testsecret'
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(mockUser);

      await expect(
        authService.authenticateUser('test@example.com', 'password123')
      ).rejects.toThrow('Two-factor authentication code required');
    });

    test('should hash passwords correctly', async () => {
      const password = 'testpassword123';
      const hash = await authService.hashPassword(password);
      
      expect(hash).toBeDefined();
      expect(hash).not.toBe(password);
      
      const isValid = await authService.validatePassword(password, hash);
      expect(isValid).toBe(true);
    });
  });

  describe('UserService', () => {
    test('should create user with valid data', async () => {
      const userData = {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User'
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(null); // User doesn't exist
      userRepository.create = jest.fn().mockResolvedValue({
        id: 1,
        ...userData,
        password: 'hashedpassword'
      });

      const user = await userService.createUser(userData);
      
      expect(user).toBeDefined();
      expect(user.email).toBe(userData.email);
      expect(userRepository.create).toHaveBeenCalled();
    });

    test('should reject duplicate email', async () => {
      const userData = {
        email: 'existing@example.com',
        password: 'password123',
        name: 'Test User'
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue({ id: 1 }); // User exists

      await expect(
        userService.createUser(userData)
      ).rejects.toThrow('Email already registered');
    });

    test('should sanitize user data', () => {
      const user = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        password: 'shouldnotbeincluded',
        twoFaSecret: 'shouldnotbeincluded',
        role: 'user'
      };

      const sanitized = userService.sanitizeUser(user);
      
      expect(sanitized.password).toBeUndefined();
      expect(sanitized.twoFaSecret).toBeUndefined();
      expect(sanitized.email).toBe(user.email);
      expect(sanitized.id).toBe(user.id);
    });
  });

  describe('UserRepository', () => {
    test('should map database row to user object', () => {
      const dbRow = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        two_fa_enabled: true,
        created_at: new Date(),
        is_active: true
      };

      const user = userRepository.mapRowToUser(dbRow);
      
      expect(user.id).toBe(dbRow.id);
      expect(user.email).toBe(dbRow.email);
      expect(user.twoFaEnabled).toBe(dbRow.two_fa_enabled);
      expect(user.createdAt).toBe(dbRow.created_at);
    });

    test('should handle database errors gracefully', async () => {
      mockDatabase.query = jest.fn().mockRejectedValue(new Error('Database error'));

      await expect(
        userRepository.findById(1)
      ).rejects.toThrow('Database error');
    });
  });

  describe('Integration Tests', () => {
    test('should handle complete authentication flow', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        password: await bcrypt.hash('password123', 12),
        name: 'Test User',
        twoFaEnabled: false,
        role: 'user'
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(mockUser);
      userRepository.updateLastLogin = jest.fn().mockResolvedValue();

      const response = await request(app)
        .post('/test/auth')
        .send({
          email: 'test@example.com',
          password: 'password123'
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.user.email).toBe('test@example.com');
      expect(response.body.user.password).toBeUndefined();
    });

    test('should handle authentication errors properly', async () => {
      userRepository.findByEmail = jest.fn().mockResolvedValue(null);

      const response = await request(app)
        .post('/test/auth')
        .send({
          email: 'nonexistent@example.com',
          password: 'password123'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Invalid email or password');
    });

    test('should handle user creation flow', async () => {
      const userData = {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User'
      };

      userRepository.findByEmail = jest.fn().mockResolvedValue(null);
      userRepository.create = jest.fn().mockResolvedValue({
        id: 1,
        ...userData,
        password: 'hashedpassword',
        role: 'user'
      });

      const response = await request(app)
        .post('/test/create-user')
        .send(userData);

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.user.email).toBe(userData.email);
      expect(response.body.user.password).toBeUndefined();
    });
  });

  describe('Password Security', () => {
    test('should enforce strong password hashing', async () => {
      const password = 'testpassword123';
      const hash1 = await authService.hashPassword(password);
      const hash2 = await authService.hashPassword(password);
      
      // Hashes should be different due to salt
      expect(hash1).not.toBe(hash2);
      
      // Both should validate correctly
      expect(await authService.validatePassword(password, hash1)).toBe(true);
      expect(await authService.validatePassword(password, hash2)).toBe(true);
      
      // Wrong password should fail
      expect(await authService.validatePassword('wrongpassword', hash1)).toBe(false);
    });

    test('should handle invalid hash formats', async () => {
      const result = await authService.validatePassword('password', 'invalid-hash');
      expect(result).toBe(false);
    });
  });

  describe('Error Handling', () => {
    test('should handle database connection errors', async () => {
      mockDatabase.query = jest.fn().mockRejectedValue(new Error('Connection failed'));

      await expect(
        userRepository.findById(1)
      ).rejects.toThrow();
    });

    test('should handle service initialization errors', () => {
      expect(() => {
        new AuthService(null, null);
      }).not.toThrow(); // Should handle null dependencies gracefully
    });
  });
});

module.exports = {
  AuthService,
  UserService,
  UserRepository
};