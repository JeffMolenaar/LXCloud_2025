const bcrypt = require('bcryptjs');
const speakeasy = require('speakeasy');
const database = require('../config/database');

class User {
  constructor(data) {
    this.id = data.id;
    this.email = data.email;
    this.name = data.name;
    this.address = data.address;
    this.role = data.role;
    this.twoFaEnabled = data.two_fa_enabled;
    this.twoFaSecret = data.two_fa_secret;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
    this.lastLogin = data.last_login;
    this.isActive = data.is_active;
  }

  static async create(userData) {
    const { email, password, name, address = null, role = 'user' } = userData;
    
    // Hash password
    const hashedPassword = await bcrypt.hash(password, parseInt(process.env.BCRYPT_ROUNDS) || 12);
    
    const result = await database.query(
      'INSERT INTO users (email, password, name, address, role) VALUES (?, ?, ?, ?, ?)',
      [email, hashedPassword, name, address, role]
    );
    
    return await User.findById(result.insertId);
  }

  static async findById(id) {
    const rows = await database.query('SELECT * FROM users WHERE id = ? AND is_active = TRUE', [id]);
    return rows.length > 0 ? new User(rows[0]) : null;
  }

  static async findByEmail(email) {
    const rows = await database.query('SELECT * FROM users WHERE email = ? AND is_active = TRUE', [email]);
    return rows.length > 0 ? new User(rows[0]) : null;
  }

  static async findAll(limit = 50, offset = 0) {
    const rows = await database.query(
      'SELECT * FROM users WHERE is_active = TRUE ORDER BY created_at DESC LIMIT ? OFFSET ?',
      [limit, offset]
    );
    return rows.map(row => new User(row));
  }

  async validatePassword(password) {
    const rows = await database.query('SELECT password FROM users WHERE id = ?', [this.id]);
    if (rows.length === 0) return false;
    
    return await bcrypt.compare(password, rows[0].password);
  }

  async updatePassword(newPassword) {
    const hashedPassword = await bcrypt.hash(newPassword, parseInt(process.env.BCRYPT_ROUNDS) || 12);
    await database.query('UPDATE users SET password = ?, updated_at = NOW() WHERE id = ?', [hashedPassword, this.id]);
  }

  async update(data) {
    const { name, address, email } = data;
    await database.query(
      'UPDATE users SET name = ?, address = ?, email = ?, updated_at = NOW() WHERE id = ?',
      [name, address, email, this.id]
    );
    
    // Refresh data
    const updated = await User.findById(this.id);
    Object.assign(this, updated);
  }

  async enableTwoFA() {
    const secret = speakeasy.generateSecret({
      name: `LXCloud (${this.email})`,
      issuer: 'LXCloud'
    });
    
    await database.query(
      'UPDATE users SET two_fa_secret = ? WHERE id = ?',
      [secret.base32, this.id]
    );
    
    return secret;
  }

  async confirmTwoFA(token) {
    if (!this.twoFaSecret) return false;
    
    const verified = speakeasy.totp.verify({
      secret: this.twoFaSecret,
      encoding: 'base32',
      token: token,
      window: 2
    });
    
    if (verified) {
      await database.query(
        'UPDATE users SET two_fa_enabled = TRUE WHERE id = ?',
        [this.id]
      );
      this.twoFaEnabled = true;
    }
    
    return verified;
  }

  async disableTwoFA() {
    await database.query(
      'UPDATE users SET two_fa_enabled = FALSE, two_fa_secret = NULL WHERE id = ?',
      [this.id]
    );
    this.twoFaEnabled = false;
    this.twoFaSecret = null;
  }

  async verifyTwoFA(token) {
    if (!this.twoFaEnabled || !this.twoFaSecret) return false;
    
    return speakeasy.totp.verify({
      secret: this.twoFaSecret,
      encoding: 'base32',
      token: token,
      window: 2
    });
  }

  async updateLastLogin() {
    await database.query('UPDATE users SET last_login = NOW() WHERE id = ?', [this.id]);
  }

  async deactivate() {
    // Unbind all controllers
    await database.query('UPDATE controllers SET user_id = NULL WHERE user_id = ?', [this.id]);
    
    // Deactivate user
    await database.query('UPDATE users SET is_active = FALSE WHERE id = ?', [this.id]);
  }

  async getControllers() {
    const rows = await database.query(
      'SELECT * FROM controllers WHERE user_id = ? ORDER BY name, serial_number',
      [this.id]
    );
    return rows;
  }

  async getDashboardCards() {
    const rows = await database.query(
      'SELECT * FROM dashboard_cards WHERE user_id = ? AND is_visible = TRUE ORDER BY position_y, position_x',
      [this.id]
    );
    return rows;
  }

  toJSON() {
    return {
      id: this.id,
      email: this.email,
      name: this.name,
      address: this.address,
      role: this.role,
      twoFaEnabled: this.twoFaEnabled,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      lastLogin: this.lastLogin
    };
  }
}

module.exports = User;