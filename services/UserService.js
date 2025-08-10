const { body, validationResult } = require('express-validator');
const logger = require('../config/logger');

class UserService {
  constructor(userRepository, authService) {
    this.userRepository = userRepository;
    this.authService = authService;
  }

  async createUser(userData) {
    try {
      const { email, password, name, address = null, role = 'user' } = userData;

      // Check if user already exists
      const existingUser = await this.userRepository.findByEmail(email);
      if (existingUser) {
        throw new Error('Email already registered');
      }

      // Hash password
      const hashedPassword = await this.authService.hashPassword(password);

      // Create user
      const user = await this.userRepository.create({
        email,
        password: hashedPassword,
        name,
        address,
        role
      });

      logger.info(`New user created: ${email}`);
      return user;
    } catch (error) {
      logger.error('User creation error:', error);
      throw error;
    }
  }

  async getUserById(id) {
    try {
      const user = await this.userRepository.findById(id);
      if (!user) {
        throw new Error('User not found');
      }
      return user;
    } catch (error) {
      logger.error('Get user error:', error);
      throw error;
    }
  }

  async getUserByEmail(email) {
    try {
      const user = await this.userRepository.findByEmail(email);
      if (!user) {
        throw new Error('User not found');
      }
      return user;
    } catch (error) {
      logger.error('Get user by email error:', error);
      throw error;
    }
  }

  async updateUser(userId, updateData) {
    try {
      const { name, email, address } = updateData;
      
      // Check if email is being changed and if it's already taken
      if (email) {
        const currentUser = await this.userRepository.findById(userId);
        if (email !== currentUser.email) {
          const existingUser = await this.userRepository.findByEmail(email);
          if (existingUser) {
            throw new Error('Email already in use');
          }
        }
      }

      await this.userRepository.update(userId, { name, email, address });
      logger.info(`User updated: ${userId}`);
      
      return await this.userRepository.findById(userId);
    } catch (error) {
      logger.error('User update error:', error);
      throw error;
    }
  }

  async changePassword(userId, currentPassword, newPassword) {
    try {
      const user = await this.userRepository.findById(userId);
      if (!user) {
        throw new Error('User not found');
      }

      // Validate current password
      const isValidPassword = await this.authService.validatePassword(
        currentPassword,
        user.password
      );
      if (!isValidPassword) {
        throw new Error('Current password is incorrect');
      }

      // Hash new password
      const hashedPassword = await this.authService.hashPassword(newPassword);
      
      // Update password
      await this.userRepository.updatePassword(userId, hashedPassword);
      
      logger.info(`Password changed for user: ${userId}`);
    } catch (error) {
      logger.error('Password change error:', error);
      throw error;
    }
  }

  async deactivateUser(userId) {
    try {
      await this.userRepository.deactivate(userId);
      logger.info(`User deactivated: ${userId}`);
    } catch (error) {
      logger.error('User deactivation error:', error);
      throw error;
    }
  }

  async getAllUsers(limit = 50, offset = 0) {
    try {
      return await this.userRepository.findAll(limit, offset);
    } catch (error) {
      logger.error('Get all users error:', error);
      throw error;
    }
  }

  async getUserControllers(userId) {
    try {
      return await this.userRepository.getControllers(userId);
    } catch (error) {
      logger.error('Get user controllers error:', error);
      throw error;
    }
  }

  async getUserDashboardCards(userId) {
    try {
      return await this.userRepository.getDashboardCards(userId);
    } catch (error) {
      logger.error('Get user dashboard cards error:', error);
      throw error;
    }
  }

  // Validation rules for user operations
  static getCreateValidationRules() {
    return [
      body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
      body('password')
        .isLength({ min: 8 })
        .withMessage('Password must be at least 8 characters')
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
        .withMessage('Password must contain at least one uppercase letter, one lowercase letter, and one number'),
      body('name').isLength({ min: 2 }).withMessage('Name must be at least 2 characters'),
      body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.password) {
          throw new Error('Passwords do not match');
        }
        return true;
      })
    ];
  }

  static getUpdateValidationRules() {
    return [
      body('email').optional().isEmail().normalizeEmail().withMessage('Valid email is required'),
      body('name').optional().isLength({ min: 2 }).withMessage('Name must be at least 2 characters'),
      body('address').optional()
    ];
  }

  static getPasswordChangeValidationRules() {
    return [
      body('currentPassword').isLength({ min: 1 }).withMessage('Current password is required'),
      body('newPassword')
        .isLength({ min: 8 })
        .withMessage('Password must be at least 8 characters')
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
        .withMessage('Password must contain at least one uppercase letter, one lowercase letter, and one number'),
      body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.newPassword) {
          throw new Error('Passwords do not match');
        }
        return true;
      })
    ];
  }

  static validateRequest(req) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      const errorMessage = errors.array()[0].msg;
      throw new Error(errorMessage);
    }
  }

  // Utility method to sanitize user data for API responses
  sanitizeUser(user) {
    if (!user) return null;
    
    const sanitized = {
      id: user.id,
      email: user.email,
      name: user.name,
      address: user.address,
      role: user.role,
      twoFaEnabled: user.twoFaEnabled,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
      lastLogin: user.lastLogin
    };

    return sanitized;
  }
}

module.exports = UserService;