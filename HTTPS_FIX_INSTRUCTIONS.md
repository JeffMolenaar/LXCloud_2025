# HTTPS Redirect Fix for LXCloud - Usage Instructions

## Problem
When accessing LXCloud from a local network device (phone, laptop, etc.), you get HTTPS redirects that prevent login. This commonly happens after SSL certificates are installed via `certbot --nginx`.

## Solution
The fix includes intelligent middleware that detects local network requests and ensures they can use HTTP without forced HTTPS redirects.

## How to Apply the Fix

### For New Installations
The fix is automatically included in new installations. Local network access will work over HTTP by default.

### For Existing Installations
If you're experiencing HTTPS redirect issues, run the fix script:

```bash
sudo /opt/LXCloud_2025/scripts/fix-https-redirect.sh
```

This script will:
1. Backup your current nginx configuration
2. Install the updated configuration with local network HTTP support
3. Restart nginx and LXCloud services
4. Verify everything is working

## What the Fix Does

### 1. Middleware Detection
The middleware automatically detects requests from local networks:
- `192.168.x.x` (most home networks)
- `10.x.x.x` (corporate/private networks)  
- `172.16-31.x.x` (Docker/private networks)
- `127.0.0.1` / `localhost` (local machine)

### 2. HTTP Headers Management
For local network requests:
- ✅ Removes `Strict-Transport-Security` headers (prevents HTTPS enforcement)
- ✅ Prevents Location redirects to HTTPS
- ✅ Adds `X-Local-Network: true` header for identification
- ✅ Allows session cookies over HTTP

### 3. Nginx Configuration
The nginx configuration explicitly:
- ✅ Listens on port 80 (HTTP) without redirects
- ✅ Disables HSTS for local networks
- ✅ Properly forwards local network headers

## Testing the Fix

After applying the fix, test from your local network device:

```bash
# From your phone/laptop on the same WiFi network:
curl -v http://192.168.1.xxx

# Should return HTTP 200, NOT a 301/302 redirect to HTTPS
```

## Verification

You can run the built-in test to verify the fix:

```bash
cd /opt/LXCloud_2025
./scripts/test-fix.sh
```

Expected output shows local network IPs are detected and handled correctly.

## Troubleshooting

### Still Getting HTTPS Redirects?
1. Verify the fix script completed successfully
2. Check nginx configuration: `sudo nginx -t`
3. Restart services: `sudo systemctl restart nginx lxcloud`
4. Check logs: `sudo journalctl -u lxcloud -f`

### External Access Still Works?
Yes! The fix only affects local network access. External users can still use HTTPS if SSL certificates are configured.

### SSL Certificate Issues?
The fix preserves SSL functionality for external access while allowing HTTP for local networks. Your SSL certificates remain functional.

## Manual Configuration

If you need to manually configure the fix:

1. **Update server.js** - Add the local network detection middleware
2. **Update nginx** - Use the configuration from `config/nginx-local.conf`
3. **Restart services** - `sudo systemctl restart nginx lxcloud`

## Compatibility

- ✅ Works with existing SSL certificates
- ✅ Maintains external HTTPS access
- ✅ Compatible with certbot renewals
- ✅ No impact on security for external access
- ✅ Preserves all existing functionality

The fix is surgical and only affects local network HTTP access, ensuring login works from your local devices while maintaining security.