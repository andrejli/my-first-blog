# LAN Deployment Guide - Terminal LMS Blog

This guide explains how to deploy your Django blog application locally and make it accessible from other devices on your Local Area Network (LAN) for development and testing purposes.

## 📋 Prerequisites

- Python 3.x installed
- Django project properly configured
- Virtual environment activated
- Network access to your development machine

## 🔧 Step 1: Configure Django Settings

### 1.1 Update ALLOWED_HOSTS

Edit your `mysite/settings.py` file to allow connections from your local network:

```python
# Find your local IP address first (see Step 2)
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.1.100',  # Replace with your actual local IP
    '192.168.1.*',    # Allow entire subnet (optional)
    '10.0.0.*',       # For different network ranges
    '*',              # WARNING: Only for development! Not for production!
]
```

### 1.2 Debug Mode (Development Only)

Ensure debug mode is enabled for development:

```python
DEBUG = True
```

**⚠️ WARNING**: Never deploy to production with `DEBUG = True` and `ALLOWED_HOSTS = ['*']`

## 🌐 Step 2: Find Your Local IP Address

### On Windows (PowerShell/Command Prompt):
```powershell
ipconfig
```
Look for "IPv4 Address" under your active network adapter (usually Ethernet or Wi-Fi).

### On macOS/Linux:
```bash
ifconfig
# or
ip addr show
```
Look for `inet` address (not 127.0.0.1).

### Alternative Method:
```python
# Run this Python script to find your IP
import socket
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"Your local IP address: {local_ip}")
```

## 🚀 Step 3: Start Development Server

### 3.1 Activate Virtual Environment
```powershell
# Windows PowerShell
.\venv\Scripts\activate

# Windows Command Prompt
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### 3.2 Start Django Server on All Interfaces
```bash
# Basic command (binds to all available interfaces)
python manage.py runserver 0.0.0.0:8000

# Specific IP and port
python manage.py runserver 192.168.1.100:8000

# Custom port
python manage.py runserver 0.0.0.0:9000
```

### 3.3 Verify Server is Running
You should see output like:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 19, 2025 - 14:30:00
Django version 5.2.x, using settings 'mysite.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

## 🔗 Step 4: Access from Other Devices

### 4.1 From the Same Machine:
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `http://YOUR_LOCAL_IP:8000`

### 4.2 From Other Devices on LAN:
- `http://YOUR_LOCAL_IP:8000`
- Example: `http://192.168.1.100:8000`

### 4.3 Test Connectivity
From another device, you can test if the server is reachable:

#### Windows:
```cmd
telnet 192.168.1.100 8000
```

#### macOS/Linux:
```bash
nc -zv 192.168.1.100 8000
# or
telnet 192.168.1.100 8000
```

## 🔥 Step 5: Firewall Configuration

### Windows Firewall:
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change Settings" → "Allow another app"
4. Browse to your Python executable or add port 8000
5. Check both "Private" and "Public" networks

#### PowerShell Command (Run as Administrator):
```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "Django Dev Server" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Or allow specific program
New-NetFirewallRule -DisplayName "Python Django" -Direction Inbound -Program "C:\Python\python.exe" -Action Allow
```

### macOS Firewall:
```bash
# Check if firewall is enabled
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Add Python to allowed applications
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
```

### Linux (Ubuntu/Debian):
```bash
# Using UFW
sudo ufw allow 8000
sudo ufw reload

# Using iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

## 📱 Step 6: Mobile Device Testing

### Find Mobile Device IP Range:
Most home networks use:
- `192.168.1.x` (common)
- `192.168.0.x` (also common)
- `10.0.0.x` (some routers)

### Mobile Browser Testing:
1. Connect mobile device to same Wi-Fi network
2. Open browser on mobile device
3. Navigate to: `http://YOUR_COMPUTER_IP:8000`
4. Test responsive design and functionality

## 🛠️ Step 7: Advanced Configuration

### 7.1 Custom Port Configuration
```python
# In settings.py, you can define custom port
import os
PORT = int(os.environ.get('PORT', 8000))
```

```bash
# Then run with environment variable
PORT=9000 python manage.py runserver 0.0.0.0:$PORT
```

### 7.2 Multiple Network Interfaces
```bash
# Bind to specific interface only
python manage.py runserver 192.168.1.100:8000

# Bind to all interfaces (0.0.0.0)
python manage.py runserver 0.0.0.0:8000
```

### 7.3 HTTPS for Testing (Optional)
```bash
# Using Django Extensions (install first: pip install django-extensions)
python manage.py runserver_plus --cert-file cert.crt 0.0.0.0:8000
```

## 🐛 Troubleshooting

### Common Issues:

#### 1. "Invalid HTTP_HOST header"
**Problem**: Django rejects requests with unrecognized host headers.
**Solution**: Add the requesting IP/hostname to `ALLOWED_HOSTS` in settings.py

#### 2. Connection Refused
**Problem**: Firewall blocking connections or server not binding to correct interface.
**Solutions**:
- Check firewall settings
- Ensure using `0.0.0.0` not `127.0.0.1`
- Verify port isn't already in use

#### 3. Can't Access from Mobile
**Problem**: Mobile device can't reach development server.
**Solutions**:
- Verify both devices on same network
- Check router's client isolation settings
- Try different port (some networks block certain ports)

#### 4. Static Files Not Loading
**Problem**: CSS/JS files not loading from LAN access.
**Solution**: Ensure `STATIC_URL` and `STATIC_ROOT` are properly configured:

```python
# In settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Collect static files
python manage.py collectstatic
```

### Debug Commands:

```bash
# Check which processes are using port 8000
netstat -tulpn | grep :8000  # Linux/macOS
netstat -an | findstr :8000  # Windows

# Test network connectivity
ping YOUR_COMPUTER_IP
nmap -p 8000 YOUR_COMPUTER_IP
```

## 📊 Network Information Commands

### Get Detailed Network Info:
```bash
# Windows
ipconfig /all
netstat -rn

# macOS/Linux
ifconfig -a
route -n
ip route show
```

## 🔒 Security Considerations

### For Development Only:
- ✅ Use `DEBUG = True`
- ✅ Use `ALLOWED_HOSTS = ['*']` for easy testing
- ✅ Allow all firewall connections

### Before Production:
- ❌ Never use `DEBUG = True`
- ❌ Never use `ALLOWED_HOSTS = ['*']`
- ❌ Don't expose development server to internet
- ✅ Use proper web server (Apache/Nginx)
- ✅ Use HTTPS
- ✅ Configure proper firewall rules

## 📋 Quick Start Checklist

- [ ] Update `ALLOWED_HOSTS` in settings.py
- [ ] Find your local IP address
- [ ] Configure firewall to allow port 8000
- [ ] Start server with `python manage.py runserver 0.0.0.0:8000`
- [ ] Test access from same machine
- [ ] Test access from another device on LAN
- [ ] Test mobile device access
- [ ] Verify all functionality works correctly

## 🎯 Example Complete Setup

```bash
# 1. Activate environment
.\venv\Scripts\activate

# 2. Find IP address
ipconfig | findstr IPv4

# 3. Update settings.py with your IP
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100', '*']

# 4. Configure firewall (if needed)
# Windows: Allow Python through Windows Defender Firewall

# 5. Start server
python manage.py runserver 0.0.0.0:8000

# 6. Access from other devices
# http://192.168.1.100:8000
```

## 📞 Support

If you encounter issues:
1. Check Django documentation: https://docs.djangoproject.com/
2. Verify network connectivity with ping/telnet
3. Check firewall and antivirus settings
4. Ensure all devices are on the same network
5. Try different ports (8080, 9000, etc.)

---

**Note**: This setup is intended for development and testing only. For production deployment, use proper web servers like Apache or Nginx with appropriate security configurations.