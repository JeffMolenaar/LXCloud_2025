/**
 * Simple Dependency Injection Container
 * Manages service dependencies and provides a centralized way to configure them
 */
class Container {
  constructor() {
    this.services = new Map();
    this.singletons = new Map();
  }

  /**
   * Register a service factory
   * @param {string} name - Service name
   * @param {Function} factory - Factory function that creates the service
   * @param {boolean} singleton - Whether to return the same instance every time
   */
  register(name, factory, singleton = true) {
    this.services.set(name, { factory, singleton });
  }

  /**
   * Get a service instance
   * @param {string} name - Service name
   * @returns {*} Service instance
   */
  get(name) {
    const service = this.services.get(name);
    if (!service) {
      throw new Error(`Service '${name}' not found`);
    }

    if (service.singleton) {
      if (!this.singletons.has(name)) {
        this.singletons.set(name, service.factory(this));
      }
      return this.singletons.get(name);
    }

    return service.factory(this);
  }

  /**
   * Check if a service is registered
   * @param {string} name - Service name
   * @returns {boolean}
   */
  has(name) {
    return this.services.has(name);
  }

  /**
   * Clear all services and singletons
   */
  clear() {
    this.services.clear();
    this.singletons.clear();
  }

  /**
   * Get all registered service names
   * @returns {string[]}
   */
  getServiceNames() {
    return Array.from(this.services.keys());
  }
}

module.exports = Container;