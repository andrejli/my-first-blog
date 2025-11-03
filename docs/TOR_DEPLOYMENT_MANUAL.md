# Terminal LMS Tor Network Deployment Manual

## 🚀 **Quick Start Guide**

**Deployment Time**: 30-45 minutes  
**Difficulty**: Intermediate  
**Requirements**: Ubuntu/Debian server, 2GB RAM, 20GB storage

---

## 📋 **Prerequisites**

### **Server Requirements**
```
Minimum Specs:
- OS: Ubuntu 20.04+ / Debian 11+
- CPU: 1 vCPU (2.4GHz)
- RAM: 2GB 
- Storage: 20GB SSD
- Network: 10 Mbps

Recommended Specs:
- OS: Ubuntu 22.04 LTS
- CPU: 2 vCPU (3.0GHz+)
- RAM: 4GB
- Storage: 50GB NVMe SSD
- Network: 100 Mbps
```

### **Required Software**
- Python 3.8+
- Nginx
- Tor
- Git
- SQLite3

---

## 🛠️ **Step 1: Server Setup**

### **1.1 Update System**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget gnupg2 software-properties-common
```

### **1.2 Install Dependencies**
```bash
# Install core packages
sudo apt install -y python3 python3-pip python3-venv nginx tor git sqlite3

# Install image optimization tools
sudo apt install -y jpegoptim optipng

# Install development tools
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### **1.3 Configure Firewall**
```bash
# Setup UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw enable
```

---

## 📁 **Step 2: Application Installation**

### **2.1 Create Application Directory**
```bash
# Create directory
sudo mkdir -p /opt/terminal-lms
sudo chown $USER:$USER /opt/terminal-lms
cd /opt/terminal-lms
```

### **2.2 Clone Repository**
```bash
# Clone Terminal LMS
git clone https://github.com/andrejli/my-first-blog.git .

# Verify files
ls -la
```

### **2.3 Setup Python Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### **2.4 Database Setup**
```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup themes
python manage.py setup_themes

# Collect static files
python manage.py collectstatic --noinput
```

---

## 🔐 **Step 3: Tor Configuration**

### **3.1 Configure Tor Hidden Service**
```bash
# Edit Tor configuration
sudo nano /etc/tor/torrc
```

Add the following lines:
```
# Terminal LMS Hidden Service
HiddenServiceDir /var/lib/tor/lms_hidden_service/
HiddenServicePort 80 127.0.0.1:8080
HiddenServiceVersion 3

# Security settings
HiddenServiceNumIntroductionPoints 5
HiddenServiceMaxStreams 100
HiddenServiceMaxStreamsCloseCircuit 1

# Performance settings
CircuitBuildTimeout 60
LearnCircuitBuildTimeout 0
MaxCircuitDirtiness 600
```

### **3.2 Start Tor Service**
```bash
# Start and enable Tor
sudo systemctl enable tor
sudo systemctl start tor

# Check status
sudo systemctl status tor

# Get onion address (wait 30 seconds first)
sleep 30
sudo cat /var/lib/tor/lms_hidden_service/hostname
```

**Save your onion address!** Example: `abc123def456ghi789.onion`

---

## ⚙️ **Step 4: Django Configuration**

### **4.1 Create Tor Settings File**
```bash
cd /opt/terminal-lms
cp mysite/settings.py mysite/settings_tor.py
nano mysite/settings_tor.py
```

### **4.2 Edit Tor Settings**
Replace the content with:
```python
# settings_tor.py - Tor optimized configuration
from .settings import *
import os

# Security settings
DEBUG = False
ALLOWED_HOSTS = ['your-onion-address.onion', 'localhost', '127.0.0.1']

# Replace 'your-onion-address.onion' with your actual onion address

# Tor-specific settings
SECURITY_TOR_POLICY = 'allow'
USE_TZ = True

# Session security
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF protection
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# File upload limits (reduced for Tor)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB

# Enhanced caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django-lms-tor-cache',
        'TIMEOUT': 900,
        'OPTIONS': {
            'MAX_ENTRIES': 2000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Database optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'OPTIONS': {
            'timeout': 60,
            'init_command': '''
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA cache_size=1000000;
                PRAGMA temp_store=MEMORY;
                PRAGMA mmap_size=268435456;
                PRAGMA foreign_keys=ON;
                PRAGMA optimize;
            '''
        }
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/lms/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

**Important**: Replace `'your-onion-address.onion'` with your actual onion address!

---

## 🌐 **Step 5: Nginx Configuration**

### **5.1 Create Nginx Site Configuration**
```bash
sudo nano /etc/nginx/sites-available/lms-onion
```

Add the following configuration:
```nginx
server {
    listen 127.0.0.1:8080;
    server_name your-onion-address.onion;
    
    # Tor-optimized settings
    client_max_body_size 5M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    keepalive_timeout 60s;
    proxy_read_timeout 60s;
    proxy_connect_timeout 30s;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto http;
    }
    
    # Static files
    location /static/ {
        alias /opt/terminal-lms/static/;
        expires 7d;
        gzip on;
        gzip_comp_level 6;
        gzip_types text/css text/javascript application/javascript;
    }
    
    # Media files
    location /media/ {
        alias /opt/terminal-lms/media/;
        expires 1h;
    }
    
    # Block sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(sql|db|sqlite|log)$ {
        deny all;
    }
}
```

**Replace `your-onion-address.onion` with your actual onion address!**

### **5.2 Enable Nginx Site**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/lms-onion /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 🚀 **Step 6: Django Service Setup**

### **6.1 Create Systemd Service**
```bash
sudo nano /etc/systemd/system/terminal-lms-tor.service
```

Add the following:
```ini
[Unit]
Description=Terminal LMS for Tor
After=network.target tor.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/terminal-lms
Environment=DJANGO_SETTINGS_MODULE=mysite.settings_tor
ExecStart=/opt/terminal-lms/venv/bin/python manage.py runserver 127.0.0.1:8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### **6.2 Setup Permissions and Logs**
```bash
# Create log directory
sudo mkdir -p /var/log/lms
sudo chown www-data:www-data /var/log/lms

# Set ownership
sudo chown -R www-data:www-data /opt/terminal-lms

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable terminal-lms-tor
sudo systemctl start terminal-lms-tor
```

---

## ✅ **Step 7: Testing and Verification**

### **7.1 Check All Services**
```bash
# Check service status
sudo systemctl status tor
sudo systemctl status nginx
sudo systemctl status terminal-lms-tor

# Check ports
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8080
```

### **7.2 Test Local Access**
```bash
# Test Django directly
curl -I http://127.0.0.1:8000/

# Test through Nginx
curl -I http://127.0.0.1:8080/

# Check logs
sudo journalctl -u terminal-lms-tor -f
tail -f /var/log/lms/django.log
```

### **7.3 Test Tor Access**
1. Install Tor Browser on your local machine
2. Navigate to your onion address: `http://your-onion-address.onion`
3. Verify the site loads correctly
4. Test login functionality
5. Test file upload (use small test file)

---

## 🔍 **Step 8: Monitoring and Maintenance**

### **8.1 Create Monitoring Script**
```bash
nano /opt/terminal-lms/monitor.sh
chmod +x /opt/terminal-lms/monitor.sh
```

Add the following:
```bash
#!/bin/bash
# Simple monitoring script

echo "=== Terminal LMS Tor Monitor ==="
echo "Date: $(date)"
echo ""

# Service status
echo "Services:"
echo "  Tor: $(systemctl is-active tor)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "  Django: $(systemctl is-active terminal-lms-tor)"
echo ""

# Disk usage
echo "Disk Usage:"
df -h /opt/terminal-lms | tail -1

# Memory usage
echo ""
echo "Memory Usage:"
free -h | grep "Mem:"

# Recent errors
echo ""
echo "Recent Errors:"
sudo journalctl -u terminal-lms-tor --since "1 hour ago" | grep -i error | tail -3
```

### **8.2 Setup Automated Backup**
```bash
nano /opt/terminal-lms/backup.sh
chmod +x /opt/terminal-lms/backup.sh
```

Add the following:
```bash
#!/bin/bash
# Simple backup script

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database and media
cd /opt/terminal-lms
tar -czf "$BACKUP_DIR/lms_backup_$DATE.tar.gz" \
    db.sqlite3 \
    media/ \
    mysite/settings_tor.py

echo "Backup created: $BACKUP_DIR/lms_backup_$DATE.tar.gz"

# Keep only last 5 backups
cd $BACKUP_DIR
ls -t lms_backup_*.tar.gz | tail -n +6 | xargs rm -f
```

### **8.3 Setup Cron Jobs**
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * /opt/terminal-lms/backup.sh

# Hourly monitoring
0 * * * * /opt/terminal-lms/monitor.sh >> /var/log/lms/monitor.log
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Service Won't Start**
```bash
# Check logs
sudo journalctl -u terminal-lms-tor -n 50
sudo journalctl -u tor -n 50
sudo journalctl -u nginx -n 50

# Common fixes
sudo systemctl restart terminal-lms-tor
sudo systemctl restart tor
sudo systemctl restart nginx
```

#### **2. Onion Address Not Working**
```bash
# Wait for Tor to fully start (can take 2-3 minutes)
sleep 180

# Check onion address
sudo cat /var/lib/tor/lms_hidden_service/hostname

# Restart Tor
sudo systemctl restart tor
```

#### **3. Permission Errors**
```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/terminal-lms
sudo chown -R www-data:www-data /var/log/lms

# Fix permissions
sudo chmod -R 755 /opt/terminal-lms
sudo chmod -R 644 /opt/terminal-lms/db.sqlite3
```

#### **4. Database Errors**
```bash
# Reset database (WARNING: This deletes all data!)
cd /opt/terminal-lms
source venv/bin/activate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

#### **5. Static Files Not Loading**
```bash
# Recollect static files
cd /opt/terminal-lms
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# Fix permissions
sudo chown -R www-data:www-data static/
```

---

## 🔐 **Security Checklist**

### **Essential Security Steps**
- [ ] Debug mode disabled (`DEBUG = False`)
- [ ] Strong superuser password created
- [ ] Secret key changed from default
- [ ] Firewall configured properly
- [ ] File upload limits set appropriately
- [ ] Regular backups scheduled
- [ ] Log monitoring in place
- [ ] Only necessary ports open
- [ ] Services running as non-root user
- [ ] Database file permissions secure

### **Optional Security Enhancements**
- [ ] Database encryption
- [ ] Log file encryption
- [ ] Intrusion detection system
- [ ] Automated security updates
- [ ] Two-factor authentication

---

## 📊 **Performance Optimization**

### **For Better Performance**
```bash
# Optimize database
cd /opt/terminal-lms
source venv/bin/activate
python manage.py dbshell
```

In SQLite shell:
```sql
PRAGMA optimize;
VACUUM;
.quit
```

### **Reduce File Sizes**
```bash
# Optimize images
find /opt/terminal-lms/media -name "*.jpg" -exec jpegoptim --max=85 {} \;
find /opt/terminal-lms/media -name "*.png" -exec optipng -o7 {} \;
```

### **Enable Compression**
Add to nginx configuration:
```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/json;
```

---

## 🎯 **Usage Guidelines**

### **Recommended Practices**
1. **File Uploads**: Keep files under 5MB for best performance
2. **User Management**: Regularly review superuser accounts
3. **Content**: Use text-heavy content over images when possible
4. **Backup**: Perform daily backups
5. **Monitoring**: Check logs weekly for issues
6. **Updates**: Keep system packages updated monthly

### **Expected Performance**
- **Page Load Time**: 3-8 seconds on average
- **File Upload**: 15-60 seconds for 5MB files
- **Concurrent Users**: 20-50 users comfortably
- **Database Size**: Will grow ~10MB per 1000 users

---

## 🔄 **Maintenance Schedule**

### **Daily Tasks**
- Check service status
- Review error logs
- Verify backup completion

### **Weekly Tasks**
- Review security logs
- Check disk space usage
- Test onion address accessibility
- Update content as needed

### **Monthly Tasks**
- Update system packages
- Review user accounts
- Optimize database
- Test backup restoration
- Check performance metrics

---

## 📞 **Support Resources**

### **Log Files**
- Django: `/var/log/lms/django.log`
- Nginx: `/var/log/nginx/error.log`
- System: `sudo journalctl -u terminal-lms-tor`
- Tor: `sudo journalctl -u tor`

### **Configuration Files**
- Django: `/opt/terminal-lms/mysite/settings_tor.py`
- Nginx: `/etc/nginx/sites-available/lms-onion`
- Tor: `/etc/tor/torrc`
- Service: `/etc/systemd/system/terminal-lms-tor.service`

### **Quick Commands**
```bash
# Restart all services
sudo systemctl restart tor nginx terminal-lms-tor

# Check onion address
sudo cat /var/lib/tor/lms_hidden_service/hostname

# View real-time logs
sudo journalctl -f -u terminal-lms-tor

# Test configuration
sudo nginx -t
```

---

## ✅ **Deployment Complete!**

Your Terminal LMS is now running on the Tor network! 

**Your onion address**: Check with `sudo cat /var/lib/tor/lms_hidden_service/hostname`

**Access your site**: Open Tor Browser and navigate to your onion address

**Admin access**: Log in with the superuser account you created

**Next steps**: 
1. Create courses and content
2. Set up user accounts
3. Configure themes and settings
4. Test all functionality thoroughly

---

*Terminal LMS Tor Deployment Manual v1.0*  
*Production Ready - November 3, 2025*