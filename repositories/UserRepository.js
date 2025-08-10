const logger = require('../config/logger');

class UserRepository {
  constructor(database) {
    this.database = database;
  }

  async create(userData) {
    try {
      const { email, password, name, address = null, role = 'user' } = userData;
      
      const result = await this.database.query(
        'INSERT INTO users (email, password, name, address, role) VALUES (?, ?, ?, ?, ?)',
        [email, password, name, address, role]
      );
      
      return await this.findById(result.insertId);
    } catch (error) {
      logger.error('User creation error:', error);
      throw error;
    }
  }

  async findById(id) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM users WHERE id = ? AND is_active = TRUE',
        [id]
      );
      return rows.length > 0 ? this.mapRowToUser(rows[0]) : null;
    } catch (error) {
      logger.error('Find user by ID error:', error);
      throw error;
    }
  }

  async findByEmail(email) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM users WHERE email = ? AND is_active = TRUE',
        [email]
      );
      return rows.length > 0 ? this.mapRowToUser(rows[0]) : null;
    } catch (error) {
      logger.error('Find user by email error:', error);
      throw error;
    }
  }

  async findAll(limit = 50, offset = 0) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM users WHERE is_active = TRUE ORDER BY created_at DESC LIMIT ? OFFSET ?',
        [limit, offset]
      );
      return rows.map(row => this.mapRowToUser(row));
    } catch (error) {
      logger.error('Find all users error:', error);
      throw error;
    }
  }

  async update(id, data) {
    try {
      const { name, address, email } = data;
      await this.database.query(
        'UPDATE users SET name = ?, address = ?, email = ?, updated_at = NOW() WHERE id = ?',
        [name, address, email, id]
      );
      
      return await this.findById(id);
    } catch (error) {
      logger.error('User update error:', error);
      throw error;
    }
  }

  async updatePassword(id, hashedPassword) {
    try {
      await this.database.query(
        'UPDATE users SET password = ?, updated_at = NOW() WHERE id = ?',
        [hashedPassword, id]
      );
    } catch (error) {
      logger.error('Password update error:', error);
      throw error;
    }
  }

  async updateLastLogin(id) {
    try {
      await this.database.query(
        'UPDATE users SET last_login = NOW() WHERE id = ?',
        [id]
      );
    } catch (error) {
      logger.error('Last login update error:', error);
      throw error;
    }
  }

  async updateTwoFASecret(id, secret) {
    try {
      await this.database.query(
        'UPDATE users SET two_fa_secret = ? WHERE id = ?',
        [secret, id]
      );
    } catch (error) {
      logger.error('Two-FA secret update error:', error);
      throw error;
    }
  }

  async enableTwoFA(id) {
    try {
      await this.database.query(
        'UPDATE users SET two_fa_enabled = TRUE WHERE id = ?',
        [id]
      );
    } catch (error) {
      logger.error('Two-FA enable error:', error);
      throw error;
    }
  }

  async disableTwoFA(id) {
    try {
      await this.database.query(
        'UPDATE users SET two_fa_enabled = FALSE, two_fa_secret = NULL WHERE id = ?',
        [id]
      );
    } catch (error) {
      logger.error('Two-FA disable error:', error);
      throw error;
    }
  }

  async deactivate(id) {
    try {
      // Unbind all controllers
      await this.database.query(
        'UPDATE controllers SET user_id = NULL WHERE user_id = ?',
        [id]
      );
      
      // Deactivate user
      await this.database.query(
        'UPDATE users SET is_active = FALSE WHERE id = ?',
        [id]
      );
    } catch (error) {
      logger.error('User deactivation error:', error);
      throw error;
    }
  }

  async getControllers(userId) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM controllers WHERE user_id = ? ORDER BY name, serial_number',
        [userId]
      );
      return rows;
    } catch (error) {
      logger.error('Get user controllers error:', error);
      throw error;
    }
  }

  async getDashboardCards(userId) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM dashboard_cards WHERE user_id = ? AND is_visible = TRUE ORDER BY position_y, position_x',
        [userId]
      );
      return rows;
    } catch (error) {
      logger.error('Get dashboard cards error:', error);
      throw error;
    }
  }

  async getUserStats(userId) {
    try {
      const [controllerCount] = await this.database.query(
        'SELECT COUNT(*) as count FROM controllers WHERE user_id = ?',
        [userId]
      );

      const [onlineControllers] = await this.database.query(
        'SELECT COUNT(*) as count FROM controllers WHERE user_id = ? AND status = "online"',
        [userId]
      );

      return {
        totalControllers: controllerCount.count,
        onlineControllers: onlineControllers.count
      };
    } catch (error) {
      logger.error('Get user stats error:', error);
      throw error;
    }
  }

  async getWithPassword(id) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM users WHERE id = ? AND is_active = TRUE',
        [id]
      );
      return rows.length > 0 ? rows[0] : null;
    } catch (error) {
      logger.error('Get user with password error:', error);
      throw error;
    }
  }

  async count() {
    try {
      const rows = await this.database.query(
        'SELECT COUNT(*) as count FROM users WHERE is_active = TRUE'
      );
      return rows[0].count;
    } catch (error) {
      logger.error('User count error:', error);
      throw error;
    }
  }

  async findByRole(role, limit = 50, offset = 0) {
    try {
      const rows = await this.database.query(
        'SELECT * FROM users WHERE role = ? AND is_active = TRUE ORDER BY created_at DESC LIMIT ? OFFSET ?',
        [role, limit, offset]
      );
      return rows.map(row => this.mapRowToUser(row));
    } catch (error) {
      logger.error('Find users by role error:', error);
      throw error;
    }
  }

  // Map database row to user object (excluding sensitive data)
  mapRowToUser(row) {
    return {
      id: row.id,
      email: row.email,
      name: row.name,
      address: row.address,
      role: row.role,
      twoFaEnabled: row.two_fa_enabled,
      twoFaSecret: row.two_fa_secret, // Only include when needed
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      lastLogin: row.last_login,
      isActive: row.is_active,
      // Include password only when specifically requested
      ...(row.password && { password: row.password })
    };
  }

  // Get user object without sensitive data for API responses
  mapToPublicUser(row) {
    return {
      id: row.id,
      email: row.email,
      name: row.name,
      address: row.address,
      role: row.role,
      twoFaEnabled: row.two_fa_enabled,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      lastLogin: row.last_login
    };
  }
}

module.exports = UserRepository;