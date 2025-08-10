const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');
const logger = require('../config/logger');

class AuthService {
  constructor(userRepository, sessionService) {
    this.userRepository = userRepository;
    this.sessionService = sessionService;
    this.maxLoginAttempts = 5;
    this.lockTimeMinutes = 15;
  }

  async authenticateUser(email, password, twoFactorToken = null) {
    try {
      // Find user by email
      const user = await this.userRepository.findByEmail(email);
      if (!user) {
        logger.warn(`Login attempt with invalid email: ${email}`);
        throw new Error('Invalid email or password');
      }

      // Check if account is locked
      if (await this.isAccountLocked(user.id)) {
        logger.warn(`Login attempt on locked account: ${email}`);
        throw new Error('Account temporarily locked due to multiple failed attempts');
      }

      // Validate password
      const isValidPassword = await this.validatePassword(password, user.password);
      if (!isValidPassword) {
        await this.recordFailedAttempt(user.id);
        logger.warn(`Failed login attempt for: ${email}`);
        throw new Error('Invalid email or password');
      }

      // Check 2FA if enabled
      if (user.twoFaEnabled) {
        if (!twoFactorToken) {
          throw new Error('Two-factor authentication code required');
        }

        const isValidTwoFA = await this.verifyTwoFA(user.twoFaSecret, twoFactorToken);
        if (!isValidTwoFA) {
          await this.recordFailedAttempt(user.id);
          logger.warn(`Failed 2FA attempt for: ${email}`);
          throw new Error('Invalid two-factor authentication code');
        }
      }

      // Clear failed attempts on successful login
      await this.clearFailedAttempts(user.id);
      
      // Update last login
      await this.userRepository.updateLastLogin(user.id);

      logger.info(`Successful login for: ${email}`);
      return user;

    } catch (error) {
      logger.error('Authentication error:', error);
      throw error;
    }
  }

  async generateTokens(user) {
    try {
      const tokenPayload = {
        userId: user.id,
        email: user.email,
        role: user.role
      };

      const accessToken = jwt.sign(
        tokenPayload,
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN || '15m' }
      );

      const refreshToken = jwt.sign(
        { userId: user.id },
        process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d' }
      );

      // Store refresh token
      await this.sessionService.storeRefreshToken(user.id, refreshToken);

      return { accessToken, refreshToken };
    } catch (error) {
      logger.error('Token generation error:', error);
      throw new Error('Failed to generate authentication tokens');
    }
  }

  async refreshTokens(refreshToken) {
    try {
      const decoded = jwt.verify(
        refreshToken,
        process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET
      );

      const user = await this.userRepository.findById(decoded.userId);
      if (!user) {
        throw new Error('User not found');
      }

      // Verify refresh token is valid and not expired
      const isValidRefreshToken = await this.sessionService.validateRefreshToken(
        user.id,
        refreshToken
      );
      if (!isValidRefreshToken) {
        throw new Error('Invalid refresh token');
      }

      // Generate new tokens
      const tokens = await this.generateTokens(user);
      
      // Revoke old refresh token
      await this.sessionService.revokeRefreshToken(refreshToken);

      return tokens;
    } catch (error) {
      logger.error('Token refresh error:', error);
      throw new Error('Failed to refresh tokens');
    }
  }

  async validatePassword(plainPassword, hashedPassword) {
    return await bcrypt.compare(plainPassword, hashedPassword);
  }

  async hashPassword(password) {
    const rounds = parseInt(process.env.BCRYPT_ROUNDS) || 12;
    return await bcrypt.hash(password, rounds);
  }

  async enableTwoFA(userId) {
    try {
      const user = await this.userRepository.findById(userId);
      if (!user) {
        throw new Error('User not found');
      }

      const secret = speakeasy.generateSecret({
        name: `LXCloud (${user.email})`,
        issuer: 'LXCloud'
      });

      await this.userRepository.updateTwoFASecret(userId, secret.base32);

      const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

      return {
        secret: secret.base32,
        qrCode: qrCodeUrl,
        backupCodes: this.generateBackupCodes()
      };
    } catch (error) {
      logger.error('Two-factor setup error:', error);
      throw new Error('Failed to enable two-factor authentication');
    }
  }

  async confirmTwoFA(userId, token) {
    try {
      const user = await this.userRepository.findById(userId);
      if (!user || !user.twoFaSecret) {
        throw new Error('Two-factor authentication not initialized');
      }

      const isValid = this.verifyTwoFA(user.twoFaSecret, token);
      if (!isValid) {
        return false;
      }

      await this.userRepository.enableTwoFA(userId);
      logger.info(`Two-factor authentication enabled for user: ${user.email}`);
      return true;
    } catch (error) {
      logger.error('Two-factor confirmation error:', error);
      throw new Error('Failed to confirm two-factor authentication');
    }
  }

  async disableTwoFA(userId) {
    try {
      await this.userRepository.disableTwoFA(userId);
      logger.info(`Two-factor authentication disabled for user ID: ${userId}`);
    } catch (error) {
      logger.error('Two-factor disable error:', error);
      throw new Error('Failed to disable two-factor authentication');
    }
  }

  verifyTwoFA(secret, token) {
    if (!secret || !token) return false;
    
    return speakeasy.totp.verify({
      secret: secret,
      encoding: 'base32',
      token: token,
      window: 2
    });
  }

  generateBackupCodes() {
    const codes = [];
    for (let i = 0; i < 10; i++) {
      codes.push(Math.random().toString(36).substr(2, 8).toUpperCase());
    }
    return codes;
  }

  async recordFailedAttempt(userId) {
    // This would be implemented to track failed login attempts
    // For now, we'll use a simple in-memory approach
    // In production, this should be stored in database
    logger.warn(`Recording failed login attempt for user ID: ${userId}`);
  }

  async clearFailedAttempts(userId) {
    // Clear failed attempts after successful login
    logger.info(`Clearing failed login attempts for user ID: ${userId}`);
  }

  async isAccountLocked(userId) {
    // For now, return false - implement proper lockout logic later
    return false;
  }

  async logout(userId, sessionId = null) {
    try {
      if (sessionId) {
        await this.sessionService.destroySession(sessionId);
      }
      await this.sessionService.revokeAllRefreshTokens(userId);
      logger.info(`User logged out: ${userId}`);
    } catch (error) {
      logger.error('Logout error:', error);
      throw new Error('Failed to logout');
    }
  }
}

module.exports = AuthService;