# LXCloud Simple v2.0

A completely reworked, simplified version of LXCloud that eliminates database dependencies and complex setup requirements. This version provides core functionality with HTTP-only access restricted to local networks.

## ✨ Features

- **🚀 Zero Database Setup** - Uses file-based JSON storage, no MySQL/MariaDB required
- **🔒 Local Network Only** - Automatically restricts access to local network IPs only
- **🌐 HTTP Only** - No HTTPS redirects or enforcement for local network simplicity  
- **👤 Simple Authentication** - File-based user management with bcrypt encryption
- **📊 Clean Dashboard** - Modern, responsive interface with system statistics
- **⚡ Fast Startup** - No complex initialization or database migrations
- **🛡️ Secure Sessions** - HTTP-only session cookies with proper management

## 🚦 Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start the Server**
   ```bash
   npm start
   ```

3. **Access the Dashboard**
   - Open: http://localhost:3000
   - Login: admin@lxcloud.local / admin123

## 📱 Screenshots

### Login Page
![Login Page](https://github.com/user-attachments/assets/8601451b-3872-4a74-bc49-97011d322887)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/47b210d1-0658-4717-ae70-c8de551a7546)

## 🔧 Configuration

### Environment Variables
No environment configuration required! The application works out-of-the-box with sensible defaults.

### Default Admin User
- **Email:** admin@lxcloud.local
- **Password:** admin123
- **Role:** admin

### Data Storage
- **Users:** `data/users.json`
- **Format:** JSON with bcrypt-hashed passwords
- **Backup:** Automatically created on first run

## 🛡️ Security Features

### Local Network Restriction
Access is automatically restricted to:
- `127.0.0.1` / `localhost` (local machine)
- `192.168.x.x` (home networks)
- `10.x.x.x` (corporate networks)
- `172.16-31.x.x` (Docker/private networks)

External IPs receive a 403 Forbidden response.

### Session Security
- HTTP-only cookies (no client-side access)
- 24-hour session expiration
- Secure session data handling
- Automatic cleanup

## 🧪 Testing

Run the comprehensive test suite:
```bash
node test-simple.js
```

Tests verify:
- ✅ Authentication flow
- ✅ Local network restrictions
- ✅ Session management
- ✅ File-based storage
- ✅ Dashboard functionality
- ✅ HTTP-only access
- ✅ API endpoints

## 📁 Project Structure

```
├── server-simple.js           # Main application server
├── views/
│   ├── auth/
│   │   └── login-simple.ejs   # Login page
│   ├── dashboard/
│   │   └── dashboard-simple.ejs # Main dashboard
│   └── admin/
│       └── users-simple.ejs   # User management
├── data/
│   └── users.json            # User storage (created automatically)
├── public/                   # Static assets
├── test-simple.js           # Comprehensive test suite
└── package.json             # Dependencies and scripts
```

## 🆚 Differences from Original

| Feature | Original LXCloud | LXCloud Simple |
|---------|------------------|----------------|
| Database | MySQL/MariaDB required | File-based JSON |
| Setup | Complex installation | `npm install && npm start` |
| HTTPS | Forced redirects | HTTP only |
| Access | Public + Local | Local network only |
| Auth | Database + JWT | File + Sessions |
| Dependencies | 50+ packages | Essential only |
| Config | Multiple .env files | Zero config |

## 🐛 Troubleshooting

### "Access Denied" Error
- Ensure you're accessing from a local network IP
- Check that you're using HTTP (not HTTPS)

### Login Issues
- Use default credentials: admin@lxcloud.local / admin123
- Check `data/users.json` file exists

### Port Already in Use
```bash
# Check what's using port 3000
lsof -i :3000

# Kill the process if needed
kill -9 <PID>
```

## 🔄 Migration from Original

To switch from the original LXCloud to the simplified version:

1. **Backup your data** (if needed)
2. **Update npm script:**
   ```bash
   npm run start  # Now runs simplified version
   npm run start-original  # Runs original version
   ```
3. **Access via HTTP only:** http://localhost:3000

## 🚀 Production Deployment

For production use on a local network:

1. **Set custom port** (optional):
   ```bash
   PORT=8080 npm start
   ```

2. **Run as service** (systemd example):
   ```ini
   [Unit]
   Description=LXCloud Simple
   
   [Service]
   Type=simple
   User=lxcloud
   WorkingDirectory=/opt/lxcloud
   ExecStart=/usr/bin/npm start
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Access from network devices:**
   - Find server IP: `ip addr show`
   - Access: `http://[SERVER-IP]:3000`

## 📝 API Endpoints

- `GET /api/health` - System health check
- `GET /api/ping` - Connectivity test
- `POST /login` - User authentication
- `POST /logout` - Session termination
- `GET /dashboard` - Main dashboard (auth required)
- `GET /users` - User management (admin required)

## 🤝 Contributing

This simplified version focuses on core functionality. For feature requests:

1. Ensure it aligns with the "simple" philosophy
2. No external database dependencies
3. Maintain local-network-only access
4. Keep HTTP-only for simplicity

## 📄 License

MIT License - see LICENSE file for details.

---

**LXCloud Simple v2.0** - Simplified cloud dashboard for local network environments.