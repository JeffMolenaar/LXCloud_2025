# LXCloud Authentication System - Modular Architecture

This document describes the completely reworked authentication system with clean modular architecture implemented to fix all login issues.

## Overview

The authentication system has been completely refactored from a monolithic approach to a clean, modular architecture following best practices:

- **Services Layer**: Business logic separated into focused services
- **Repository Pattern**: Data access abstracted from business logic  
- **Dependency Injection**: Clean dependency management with container
- **Enhanced Security**: Better password hashing, session management, and rate limiting
- **Comprehensive Testing**: 17 focused unit and integration tests
- **Better Error Handling**: Consistent error responses and logging

## Architecture Components

### 1. Services Layer (`/services/`)

#### AuthService.js
Handles all authentication-related business logic:
- User authentication with enhanced security
- JWT token generation and refresh
- Two-factor authentication (2FA) management
- Password validation and hashing
- Account lockout prevention (framework ready)
- Security audit logging

Key methods:
- `authenticateUser(email, password, twoFactorToken)` - Main authentication
- `generateTokens(user)` - JWT access and refresh tokens
- `refreshTokens(refreshToken)` - Token rotation
- `enableTwoFA(userId)` - Setup 2FA with QR codes
- `hashPassword(password)` / `validatePassword(password, hash)` - Secure password handling

#### UserService.js
Manages user-related operations:
- User creation with validation
- Profile management
- Password changes
- User data sanitization
- Validation rule definitions

Key methods:
- `createUser(userData)` - Create new user with validation
- `updateUser(userId, updateData)` - Update user information
- `changePassword(userId, currentPassword, newPassword)` - Secure password changes
- `sanitizeUser(user)` - Remove sensitive data for API responses

#### SessionService.js
Enhanced session management:
- Database-backed sessions (vs memory-only)
- Refresh token management with rotation
- Session cleanup and expiration
- Multi-device session tracking

Key methods:
- `createSession(userId, sessionData, expiresIn)` - Create persistent session
- `storeRefreshToken(userId, refreshToken)` - Secure token storage
- `cleanupExpiredSessions()` - Automated cleanup
- `destroyUserSessions(userId)` - Logout from all devices

### 2. Repository Pattern (`/repositories/`)

#### UserRepository.js
Abstracts all user data access:
- Clean separation between data access and business logic
- Consistent error handling
- Database query optimization
- Data mapping and transformation

Key methods:
- `create(userData)` - Create user in database
- `findById(id)` / `findByEmail(email)` - User lookups
- `update(id, data)` - Update user data
- `getWithPassword(id)` - Secure password retrieval

### 3. Dependency Injection (`/config/container/`)

#### Container.js
Simple DI container for managing service dependencies:
- Singleton service management
- Dependency resolution
- Clean service configuration

#### index.js
Service container configuration:
```javascript
// Services are automatically wired with their dependencies
const authService = container.get('authService');
const userService = container.get('userService');
```

### 4. Configuration Management (`/config/app.js`)

Centralized configuration with environment-specific defaults:
- Database connection settings
- Authentication parameters (JWT secrets, session duration)
- Security settings (rate limiting, HTTPS enforcement)
- Feature flags (2FA, registration, password reset)
- Logging configuration

## Enhanced Login Features

### 1. Improved User Experience
- **Remember Me**: Extended session duration (30 days vs 24 hours)
- **Real-time Validation**: Client-side email format validation
- **Enhanced Error Messages**: User-friendly error display
- **Loading States**: Visual feedback during authentication
- **Connection Status**: Server connectivity indicators

### 2. Security Enhancements
- **Rate Limiting**: 5 login attempts per 15 minutes per IP
- **Password Security**: Bcrypt with configurable rounds (12 in production)
- **Session Security**: HttpOnly cookies, secure session storage
- **HTTPS Flexibility**: Smart local network detection
- **Security Logging**: All authentication events logged

### 3. Two-Factor Authentication
- **QR Code Setup**: Easy mobile app configuration
- **Backup Codes**: Recovery codes for 2FA (framework ready)
- **Token Validation**: TOTP with 2-window tolerance
- **2FA Management**: Enable/disable via user interface

## Database Schema Updates

New tables added for enhanced functionality:

```sql
-- Enhanced session management
CREATE TABLE sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  user_id INT NOT NULL,
  data TEXT,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- Indexes for performance
  INDEX idx_user_id (user_id),
  INDEX idx_expires_at (expires_at)
);

-- JWT refresh token management
CREATE TABLE refresh_tokens (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  is_revoked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security audit logging (framework ready)
CREATE TABLE security_audit_log (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  event_type VARCHAR(50) NOT NULL,
  event_description TEXT,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Failed login tracking (framework ready)
CREATE TABLE failed_login_attempts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  ip_address VARCHAR(45),
  user_agent TEXT,
  attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Authentication Routes (`/routes/auth-new.js`)

- `GET /auth/login` - Display login form
- `POST /auth/login` - Authenticate user (supports 2FA and Remember Me)
- `GET /auth/register` - Display registration form  
- `POST /auth/register` - Create new user account
- `GET /auth/two-factor-setup` - 2FA setup with QR code
- `POST /auth/two-factor-setup` - Confirm 2FA setup
- `POST /auth/logout` - Enhanced logout with session cleanup

### API Endpoints
- `POST /auth/api/token` - Generate JWT tokens for API access
- `POST /auth/api/refresh` - Refresh JWT tokens

## Testing

Comprehensive test suite with 17 tests covering:

### Unit Tests
- AuthService authentication flows
- UserService user management  
- UserRepository data access
- Password security and hashing

### Integration Tests
- Complete authentication flows
- Error handling scenarios
- Service interaction patterns

### Test Coverage
- Valid/invalid authentication attempts
- 2FA token validation
- User creation and validation
- Database error handling
- Password security requirements

## Migration from Old System

The new system maintains backward compatibility while providing enhanced functionality:

1. **Existing User Model**: Updated to use new services while maintaining interface
2. **Session Compatibility**: Enhanced sessions work with existing middleware
3. **Gradual Migration**: Routes updated to use new auth-new.js (can run alongside old system)

## Usage Examples

### Service Usage
```javascript
// Get services from container
const authService = container.get('authService');
const userService = container.get('userService');

// Authenticate user
const user = await authService.authenticateUser(email, password, twoFactorToken);

// Generate API tokens
const tokens = await authService.generateTokens(user);

// Create new user
const newUser = await userService.createUser({
  email: 'user@example.com',
  password: 'securepassword',
  name: 'User Name'
});
```

### Route Usage
```javascript
// Using services in routes
router.post('/login', async (req, res) => {
  try {
    const { email, password, twoFactorToken, rememberMe } = req.body;
    const user = await authService.authenticateUser(email, password, twoFactorToken);
    
    req.session.user = userService.sanitizeUser(user);
    if (rememberMe) {
      req.session.cookie.maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
    }
    
    res.redirect('/dashboard');
  } catch (error) {
    res.render('auth/login', { error: error.message });
  }
});
```

## Performance Considerations

1. **Connection Pooling**: Database connections properly pooled and managed
2. **Session Cleanup**: Automated cleanup of expired sessions every hour
3. **Password Hashing**: Configurable bcrypt rounds (10 for dev, 12 for production)
4. **Query Optimization**: Proper indexes on session and user tables
5. **Memory Management**: Services properly handle cleanup and resource disposal

## Security Best Practices Implemented

1. **Defense in Depth**: Multiple layers of security validation
2. **Principle of Least Privilege**: Users only get necessary data
3. **Secure Defaults**: All security features enabled by default
4. **Input Validation**: All user inputs validated and sanitized
5. **Error Handling**: No sensitive information leaked in errors
6. **Audit Logging**: All security events properly logged
7. **Token Rotation**: JWT refresh tokens are rotated on use

## Future Enhancements

The modular architecture supports easy addition of:

1. **Account Lockout**: Framework already in place
2. **Password Reset**: Email-based password reset system
3. **Social Login**: OAuth providers (Google, GitHub, etc.)
4. **Multi-Device Management**: Device tracking and management
5. **Advanced 2FA**: WebAuthn, hardware keys support
6. **Single Sign-On**: SAML/OAuth SSO integration

## Configuration

Key environment variables for production:

```env
# Required in production
JWT_SECRET=your-secure-jwt-secret
SESSION_SECRET=your-secure-session-secret
JWT_REFRESH_SECRET=your-refresh-secret

# Authentication settings
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCK_TIME_MINUTES=15

# Session settings
SESSION_MAX_AGE=86400000
REMEMBER_ME_MAX_AGE=2592000000

# Rate limiting
LOGIN_RATE_LIMIT_MAX=5
LOGIN_RATE_LIMIT_WINDOW_MS=900000
```

This modular architecture provides a solid foundation for secure, scalable authentication while maintaining clean code organization and comprehensive testing coverage.