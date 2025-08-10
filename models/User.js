const container = require('../config/container');

class User {
  constructor(data) {
    this.id = data.id;
    this.email = data.email;
    this.name = data.name;
    this.address = data.address;
    this.role = data.role;
    this.twoFaEnabled = data.twoFaEnabled || data.two_fa_enabled;
    this.twoFaSecret = data.twoFaSecret || data.two_fa_secret;
    this.createdAt = data.createdAt || data.created_at;
    this.updatedAt = data.updatedAt || data.updated_at;
    this.lastLogin = data.lastLogin || data.last_login;
    this.isActive = data.isActive || data.is_active;
    this.password = data.password; // Only include when needed
  }

  // Static methods that delegate to the repository
  static async create(userData) {
    const userService = container.get('userService');
    return await userService.createUser(userData);
  }

  static async findById(id) {
    const userRepository = container.get('userRepository');
    const userData = await userRepository.findById(id);
    return userData ? new User(userData) : null;
  }

  static async findByEmail(email) {
    const userRepository = container.get('userRepository');
    const userData = await userRepository.findByEmail(email);
    return userData ? new User(userData) : null;
  }

  static async findAll(limit = 50, offset = 0) {
    const userRepository = container.get('userRepository');
    const usersData = await userRepository.findAll(limit, offset);
    return usersData.map(userData => new User(userData));
  }

  // Instance methods that delegate to services
  async validatePassword(password) {
    const authService = container.get('authService');
    const userRepository = container.get('userRepository');
    
    // Get user with password
    const userWithPassword = await userRepository.getWithPassword(this.id);
    if (!userWithPassword) return false;
    
    return await authService.validatePassword(password, userWithPassword.password);
  }

  async updatePassword(newPassword) {
    const userService = container.get('userService');
    await userService.changePassword(this.id, null, newPassword);
  }

  async update(data) {
    const userService = container.get('userService');
    const updatedUser = await userService.updateUser(this.id, data);
    
    // Update current instance
    Object.assign(this, updatedUser);
  }

  async enableTwoFA() {
    const authService = container.get('authService');
    return await authService.enableTwoFA(this.id);
  }

  async confirmTwoFA(token) {
    const authService = container.get('authService');
    return await authService.confirmTwoFA(this.id, token);
  }

  async disableTwoFA() {
    const authService = container.get('authService');
    await authService.disableTwoFA(this.id);
    this.twoFaEnabled = false;
    this.twoFaSecret = null;
  }

  async verifyTwoFA(token) {
    const authService = container.get('authService');
    return authService.verifyTwoFA(this.twoFaSecret, token);
  }

  async updateLastLogin() {
    const userRepository = container.get('userRepository');
    await userRepository.updateLastLogin(this.id);
  }

  async deactivate() {
    const userService = container.get('userService');
    await userService.deactivateUser(this.id);
  }

  async getControllers() {
    const userService = container.get('userService');
    return await userService.getUserControllers(this.id);
  }

  async getDashboardCards() {
    const userService = container.get('userService');
    return await userService.getUserDashboardCards(this.id);
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