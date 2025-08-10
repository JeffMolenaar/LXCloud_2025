const logger = require('../config/logger');

class SessionService {
  constructor(database) {
    this.database = database;
  }

  async createSession(userId, sessionData, expiresIn = 86400000) { // 24 hours default
    try {
      const sessionId = this.generateSessionId();
      const expiresAt = new Date(Date.now() + expiresIn);
      
      await this.database.query(
        'INSERT INTO sessions (session_id, user_id, data, expires_at) VALUES (?, ?, ?, ?)',
        [sessionId, userId, JSON.stringify(sessionData), expiresAt]
      );

      logger.info(`Session created for user: ${userId}`);
      return sessionId;
    } catch (error) {
      logger.error('Session creation error:', error);
      throw new Error('Failed to create session');
    }
  }

  async getSession(sessionId) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM sessions WHERE session_id = ? AND expires_at > NOW()',
        [sessionId]
      );

      if (rows.length === 0) {
        return null;
      }

      const session = rows[0];
      return {
        sessionId: session.session_id,
        userId: session.user_id,
        data: JSON.parse(session.data),
        expiresAt: session.expires_at,
        createdAt: session.created_at
      };
    } catch (error) {
      logger.error('Session retrieval error:', error);
      throw new Error('Failed to retrieve session');
    }
  }

  async updateSession(sessionId, sessionData) {
    try {
      await this.database.query(
        'UPDATE sessions SET data = ?, updated_at = NOW() WHERE session_id = ?',
        [JSON.stringify(sessionData), sessionId]
      );
    } catch (error) {
      logger.error('Session update error:', error);
      throw new Error('Failed to update session');
    }
  }

  async destroySession(sessionId) {
    try {
      await this.database.query(
        'DELETE FROM sessions WHERE session_id = ?',
        [sessionId]
      );
      logger.info(`Session destroyed: ${sessionId}`);
    } catch (error) {
      logger.error('Session destruction error:', error);
      throw new Error('Failed to destroy session');
    }
  }

  async destroyUserSessions(userId) {
    try {
      await this.database.query(
        'DELETE FROM sessions WHERE user_id = ?',
        [userId]
      );
      logger.info(`All sessions destroyed for user: ${userId}`);
    } catch (error) {
      logger.error('User sessions destruction error:', error);
      throw new Error('Failed to destroy user sessions');
    }
  }

  async extendSession(sessionId, additionalTime = 86400000) { // 24 hours default
    try {
      await this.database.query(
        'UPDATE sessions SET expires_at = DATE_ADD(expires_at, INTERVAL ? SECOND) WHERE session_id = ?',
        [Math.floor(additionalTime / 1000), sessionId]
      );
    } catch (error) {
      logger.error('Session extension error:', error);
      throw new Error('Failed to extend session');
    }
  }

  async storeRefreshToken(userId, refreshToken, expiresIn = 604800000) { // 7 days default
    try {
      const expiresAt = new Date(Date.now() + expiresIn);
      
      await this.database.query(
        'INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
        [userId, this.hashToken(refreshToken), expiresAt]
      );

      logger.info(`Refresh token stored for user: ${userId}`);
    } catch (error) {
      logger.error('Refresh token storage error:', error);
      throw new Error('Failed to store refresh token');
    }
  }

  async validateRefreshToken(userId, refreshToken) {
    try {
      const tokenHash = this.hashToken(refreshToken);
      const rows = await this.database.query(
        'SELECT * FROM refresh_tokens WHERE user_id = ? AND token_hash = ? AND expires_at > NOW() AND is_revoked = FALSE',
        [userId, tokenHash]
      );

      return rows.length > 0;
    } catch (error) {
      logger.error('Refresh token validation error:', error);
      return false;
    }
  }

  async revokeRefreshToken(refreshToken) {
    try {
      const tokenHash = this.hashToken(refreshToken);
      await this.database.query(
        'UPDATE refresh_tokens SET is_revoked = TRUE WHERE token_hash = ?',
        [tokenHash]
      );
    } catch (error) {
      logger.error('Refresh token revocation error:', error);
      throw new Error('Failed to revoke refresh token');
    }
  }

  async revokeAllRefreshTokens(userId) {
    try {
      await this.database.query(
        'UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = ?',
        [userId]
      );
      logger.info(`All refresh tokens revoked for user: ${userId}`);
    } catch (error) {
      logger.error('All refresh tokens revocation error:', error);
      throw new Error('Failed to revoke all refresh tokens');
    }
  }

  async cleanupExpiredSessions() {
    try {
      // Clean up expired sessions
      const sessionResult = await this.database.query(
        'DELETE FROM sessions WHERE expires_at <= NOW()'
      );

      // Clean up expired refresh tokens
      const tokenResult = await this.database.query(
        'DELETE FROM refresh_tokens WHERE expires_at <= NOW() OR is_revoked = TRUE'
      );

      logger.info(`Cleaned up ${sessionResult.affectedRows || 0} expired sessions and ${tokenResult.affectedRows || 0} expired tokens`);
    } catch (error) {
      logger.error('Session cleanup error:', error);
    }
  }

  generateSessionId() {
    return require('crypto').randomBytes(32).toString('hex');
  }

  hashToken(token) {
    return require('crypto').createHash('sha256').update(token).digest('hex');
  }

  async getUserActiveSessions(userId) {
    try {
      const rows = await this.database.query(
        'SELECT session_id, created_at, expires_at, data FROM sessions WHERE user_id = ? AND expires_at > NOW() ORDER BY created_at DESC',
        [userId]
      );

      return rows.map(session => ({
        sessionId: session.session_id,
        createdAt: session.created_at,
        expiresAt: session.expires_at,
        data: JSON.parse(session.data)
      }));
    } catch (error) {
      logger.error('Get active sessions error:', error);
      throw new Error('Failed to get active sessions');
    }
  }

  // Initialize database tables for sessions and refresh tokens
  async initializeTables() {
    try {
      // Sessions table
      await this.database.query(`
        CREATE TABLE IF NOT EXISTS sessions (
          session_id VARCHAR(64) PRIMARY KEY,
          user_id INT NOT NULL,
          data TEXT,
          expires_at TIMESTAMP NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_user_id (user_id),
          INDEX idx_expires_at (expires_at),
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      // Refresh tokens table
      await this.database.query(`
        CREATE TABLE IF NOT EXISTS refresh_tokens (
          id INT PRIMARY KEY AUTO_INCREMENT,
          user_id INT NOT NULL,
          token_hash VARCHAR(64) NOT NULL,
          expires_at TIMESTAMP NOT NULL,
          is_revoked BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_user_id (user_id),
          INDEX idx_token_hash (token_hash),
          INDEX idx_expires_at (expires_at),
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
      `);

      logger.info('Session tables initialized');
    } catch (error) {
      logger.error('Session table initialization error:', error);
      throw error;
    }
  }
}

module.exports = SessionService;