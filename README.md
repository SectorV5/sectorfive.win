# Sectorfive Personal Website

A retro-styled personal website with Windows XP/Vista/7 aesthetic, featuring a complete content management system, blog, analytics, and admin interface.

## 🌟 Features

- **Retro Design**: Windows XP/Vista/7 skeuomorphic interface
- **Content Management**: Rich text editor for pages and blog posts
- **Blog System**: Full blogging capabilities with TinyMCE editor
- **File Upload**: Support for large files (up to 5GB configurable)
- **Analytics**: Custom visitor tracking with IP, country, browser data
- **Contact Form**: Spam-protected contact system with cooldown
- **Admin Panel**: Hidden admin interface at `/management-panel`
- **Old Browser Support**: Compatible with IE6+, Netscape, and legacy browsers
- **Anti-Spam**: Rate limiting and cooldown protection
- **Search & Filter**: Advanced analytics filtering and contact management

## 🚀 Quick Start

### Prerequisites

- Ubuntu 24.04 Server
- Python 3.8+
- Node.js 16+
- MongoDB
- UFW Firewall configured

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sectorfive-website
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   # or if you prefer yarn:
   yarn install
   ```

4. **Database Setup**
   ```bash
   # Install MongoDB
   sudo apt update
   sudo apt install -y mongodb
   sudo systemctl start mongodb
   sudo systemctl enable mongodb
   ```

5. **Environment Configuration**
   
   Backend `.env` file (`backend/.env`):
   ```env
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=sectorfive_website
   CORS_ORIGINS=https://sectorfive.win,https://www.sectorfive.win
   ```
   
   Frontend `.env` file (`frontend/.env`):
   ```env
   REACT_APP_BACKEND_URL=https://sectorfive.win
   ```

## 🖥️ Production Deployment

### 1. Build Frontend
```bash
cd frontend
npm run build
```

### 2. Install Process Manager
```bash
sudo npm install -g pm2
```

### 3. Create PM2 Ecosystem File
Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'sectorfive-backend',
      script: 'backend/server.py',
      interpreter: 'python3',
      cwd: '/path/to/your/website',
      env: {
        PORT: 8001,
        NODE_ENV: 'production'
      }
    }
  ]
};
```

### 4. Nginx Configuration
Create `/etc/nginx/sites-available/sectorfive.win`:
```nginx
server {
    listen 80;
    server_name sectorfive.win www.sectorfive.win;
    
    # Frontend files
    location / {
        root /path/to/your/website/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # File uploads
    client_max_body_size 5G;
}
```

### 5. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/sectorfive.win /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate (Optional but Recommended)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d sectorfive.win -d www.sectorfive.win
```

### 7. Start Services
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 8. Firewall Configuration
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 🔧 Configuration

### Admin Access
- **URL**: `https://sectorfive.win/management-panel`
- **Username**: `Sectorfive`
- **Password**: `KamenkoTV258!`

### Default Settings
- **Max File Size**: 5GB (configurable in admin)
- **Contact Cooldown**: 5 minutes (configurable)
- **Site Email**: admin@sectorfive.win

### Customization
1. **Homepage Content**: Edit via admin panel at `/management-panel`
2. **Blog Posts**: Create and edit via admin blog section
3. **Pages**: Add custom pages via admin pages section
4. **Settings**: Modify site settings in admin settings tab

## 🛠️ Development

### Running Locally
```bash
# Backend
cd backend
source venv/bin/activate
python server.py

# Frontend (in another terminal)
cd frontend
npm start
```

### File Structure
```
sectorfive-website/
├── backend/
│   ├── server.py          # FastAPI backend
│   ├── requirements.txt   # Python dependencies
│   ├── uploads/          # File upload directory
│   └── .env              # Backend environment
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   └── App.css       # Retro styling
│   ├── build/            # Production build
│   ├── package.json      # Node dependencies
│   └── .env              # Frontend environment
└── README.md
```

## 🎨 Customization Guide

### Changing Colors/Theme
Edit `frontend/src/App.css` - look for:
- `background: #245edc` (main background)
- `#0078d4` (primary blue)
- `#003d6b` (dark blue)

### Adding New Pages
1. Go to `/management-panel`
2. Click "Pages" tab
3. Click "Create New Page"
4. Use TinyMCE editor for rich content

### Blog Management
1. Access admin panel
2. Go to "Blog" tab
3. Create/edit/delete posts
4. Upload images and files as needed

### Analytics
- Automatic visitor tracking
- Filter by country, IP, browser
- Search functionality
- Export capabilities

## 🛡️ Security Features

- JWT-based authentication
- Rate limiting on contact form
- Input sanitization
- CORS protection
- Hidden admin panel
- Secure file uploads

## 🔍 Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if backend is running: `pm2 status`
   - Check logs: `pm2 logs sectorfive-backend`

2. **File Upload Fails**
   - Check disk space
   - Verify upload directory permissions
   - Check file size limits

3. **Analytics Not Working**
   - Ensure MongoDB is running
   - Check database permissions

### Logs
```bash
# PM2 logs
pm2 logs

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

## 📈 Maintenance

### Regular Backups
```bash
# Database backup
mongodump --db sectorfive_website --out /backup/mongo/

# File uploads backup
tar -czf /backup/uploads.tar.gz backend/uploads/
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Rebuild and restart
npm run build
pm2 restart sectorfive-backend
```

## 🌐 Browser Compatibility

- **Modern Browsers**: Full functionality
- **IE 9+**: Full functionality with graceful fallbacks
- **IE 6-8**: Basic functionality, emoji fallbacks
- **Netscape**: Basic functionality
- **Mobile**: Responsive design

## 📞 Support

For issues or questions:
- **Email**: admin@sectorfive.win
- **Discord**: sectorfive
- **Telegram**: @Sectorfive

## 📝 License

Personal use only. Created specifically for Sectorfive's personal website.

---

**🎉 Enjoy your retro personal website! 🎉**