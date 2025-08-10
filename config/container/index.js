const Container = require('./Container');
const database = require('../database');

// Services
const AuthService = require('../../services/AuthService');
const UserService = require('../../services/UserService');
const SessionService = require('../../services/SessionService');

// Repositories
const UserRepository = require('../../repositories/UserRepository');

/**
 * Configure and setup the dependency injection container
 * @returns {Container} Configured container instance
 */
function createContainer() {
  const container = new Container();

  // Register database
  container.register('database', () => database);

  // Register repositories
  container.register('userRepository', (c) => new UserRepository(c.get('database')));

  // Register services
  container.register('sessionService', (c) => new SessionService(c.get('database')));
  
  container.register('authService', (c) => new AuthService(
    c.get('userRepository'),
    c.get('sessionService')
  ));

  container.register('userService', (c) => new UserService(
    c.get('userRepository'),
    c.get('authService')
  ));

  return container;
}

// Create and export the container instance
const container = createContainer();

module.exports = container;