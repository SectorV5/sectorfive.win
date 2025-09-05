# Personal Website Template - Deployment Guide

This guide will help you deploy the Personal Website Template on your Ubuntu 24.04 server.

## 🚀 Quick Start (Ubuntu 24.04)

### Option 1: One-Click Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/personal-website-template.git
   cd personal-website-template
   ```

2. **Run the deployment menu**
   ```bash
   chmod +x scripts/deploy-menu.sh
   ./scripts/deploy-menu.sh
   ```

3. **Follow the interactive menu**
   - Choose option 1 to install Docker (if needed)
   - Choose option 2 to deploy the website
   - Access your website at `http://your-server-ip:8080`

### Option 2: Manual Deployment

1. **Install Docker**
   ```bash
   chmod +x scripts/ubuntu-install-docker.sh
   sudo ./scripts/ubuntu-install-docker.sh
   ```

2. **Deploy the application**
   ```bash
   chmod +x scripts/run_compose.sh
   ./scripts/run_compose.sh
   ```

## ⚙️ Configuration

### Security Configuration (IMPORTANT)

1. **Change JWT Secret** (Required for production)
   ```bash
   # Edit docker-compose.yml and replace:
   JWT_SECRET=your-super-secure-jwt-secret-key-here-CHANGE-THIS-IN-PRODUCTION
   ```

2. **Change Default Admin Credentials**
   - Login with: `admin` / `admin`
   - You'll be forced to change these on first login

3. **Configure CORS for Production**
   ```bash
   # In docker-compose.yml, replace:
   CORS_ORIGINS=*
   # With your actual domain:
   CORS_ORIGINS=https://yourdomain.com
   ```

### Environment Variables

#### Backend Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
cd backend
cp .env.example .env
```

```env
MONGO_URL=mongodb://mongo:27017
DB_NAME=personal_website_db
JWT_SECRET=your-super-secure-jwt-secret-key-here
CORS_ORIGINS=https://yourdomain.com
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE=5000000000
BASE_URL=https://yourdomain.com
```

#### Frontend Environment Variables
```bash
cd frontend
cp .env.example .env
```

For production, update `docker-compose.yml` with your domain:
```yaml
args:
  - REACT_APP_BACKEND_URL=https://yourdomain.com/api
```

## 🐳 Docker Configuration

### Production Docker Compose

For production deployment, create a `docker-compose.prod.yml`:

```yaml
services:
  mongo:
    image: mongo:6
    restart: unless-stopped
    volumes:
      - mongo_data:/data/db
      - ./backups:/backups
    environment:
      - MONGO_INITDB_DATABASE=personal_website_db
    networks:
      - website_network
    # Remove port exposure for security
    
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - MONGO_URL=mongodb://mongo:27017
      - DB_NAME=personal_website_db
      - CORS_ORIGINS=https://yourdomain.com
      - UPLOAD_PATH=/app/uploads
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - mongo
    restart: unless-stopped
    ports:
      - "127.0.0.1:8001:8001"  # Bind only to localhost
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backups:/app/backups
    networks:
      - website_network
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_BACKEND_URL=https://yourdomain.com/api
    depends_on:
      - backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:80"  # Bind only to localhost
    networks:
      - website_network

volumes:
  mongo_data:

networks:
  website_network:
    driver: bridge
```

## 🔧 Nginx Reverse Proxy (Recommended for Production)

### Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### Configure Nginx
Create `/etc/nginx/sites-available/personal-website`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # File uploads (adjust max size as needed)
    client_max_body_size 5G;
}
```

### Enable the site
```bash
sudo ln -s /etc/nginx/sites-available/personal-website /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🔒 Security Hardening

### Firewall Configuration (UFW)
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 80
sudo ufw allow 443
```

### Docker Security
1. **Bind services to localhost only** (done in production compose)
2. **Use strong JWT secrets**
3. **Regular security updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose pull
   docker-compose up -d --build
   ```

### Application Security
1. **Change default admin credentials immediately**
2. **Use strong passwords for all admin users**
3. **Configure proper CORS origins**
4. **Set reasonable file upload limits**
5. **Regular backups**

## 💾 Backup and Restore

### Manual Backup
```bash
# Using the deployment menu
./scripts/deploy-menu.sh
# Choose option 5: Backup Data
```

### Automated Backup Script
Create `/etc/cron.daily/website-backup`:

```bash
#!/bin/bash
cd /path/to/personal-website-template
./scripts/deploy-menu.sh <<< "5"
```

Make it executable:
```bash
sudo chmod +x /etc/cron.daily/website-backup
```

## 📊 Monitoring

### Basic Health Checks
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### System Resources
```bash
# Monitor resource usage
docker stats

# Check disk usage
df -h
du -sh /var/lib/docker/
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo chown -R $USER:$USER ./backend/uploads
   ```

2. **Port Already in Use**
   ```bash
   sudo netstat -tulpn | grep :8080
   sudo systemctl stop apache2  # If Apache is running
   ```

3. **Database Connection Issues**
   ```bash
   docker-compose logs mongo
   docker-compose restart mongo
   ```

4. **Frontend Build Issues**
   ```bash
   docker-compose build --no-cache frontend
   ```

### Log Locations
- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`
- MongoDB logs: `docker-compose logs mongo`
- Nginx logs: `/var/log/nginx/`

## 🔄 Updates

### Updating the Application
```bash
# Using deployment menu
./scripts/deploy-menu.sh
# Choose option 7: Update Application

# Or manually:
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## ✅ Post-Deployment Checklist

- [ ] Changed default admin credentials
- [ ] Updated JWT_SECRET in production
- [ ] Configured proper CORS origins
- [ ] Set up SSL certificate
- [ ] Configured firewall (UFW)
- [ ] Set up automated backups
- [ ] Tested all functionality
- [ ] Configured monitoring/logging
- [ ] Updated DNS records
- [ ] Performed security audit

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review application logs
3. Verify all configuration files
4. Ensure all prerequisites are installed
5. Check firewall and network settings

For additional help, create an issue in the GitHub repository.