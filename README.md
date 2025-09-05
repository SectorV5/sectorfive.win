# Personal Website Template

A modern, retro-styled personal website template built with React, FastAPI, and MongoDB. Features a complete content management system, advanced blog functionality with search and tagging, image gallery, file uploads, analytics, and extensive admin configuration options.

Inspired by Windows XP/Vista/7 Aero design with a nostalgic feel and modern functionality.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)

## ✨ Features

### Core Features
- **Retro Windows Aero-Style UI** - Nostalgic design with modern functionality
- **Admin Authentication** - Secure JWT-based authentication with configurable credentials
- **Content Management** - Create, edit, and manage pages with rich text editor
- **Advanced Blog System** - Full-featured blog with search, tagging, and filtering
- **File Upload System** - Secure file uploads with configurable size limits
- **Analytics Dashboard** - Track visitors, page views, and user behavior
- **Contact Form** - Rate-limited contact form with admin management
- **Responsive Design** - Works perfectly on all devices

### Advanced Blog Features
- **Full-Text Search** - Search across titles, content, and excerpts with highlighting
- **Advanced Filtering** - Filter by tags, authors, date ranges
- **Tag System** - Simple comma-separated tagging with tag cloud
- **Auto Excerpts** - Automatic excerpt generation from content
- **Featured Images** - Support for blog post featured images
- **Draft System** - Publish/unpublish posts

### Admin Configuration
- **Theme Customization** - Colors, fonts, backgrounds, custom CSS
- **SEO Settings** - Meta tags, Google Analytics, Search Console
- **Social Media Integration** - Links to all major platforms
- **Email Notifications** - SMTP configuration for contact/blog notifications
- **Content Settings** - Posts per page, excerpt length, default author
- **Dynamic robots.txt and sitemap.xml**

## 🛠 Tech Stack

- **Frontend**: React 18, Tailwind CSS, React Router, Axios
- **Backend**: FastAPI (Python 3.11), Motor (Async MongoDB)
- **Database**: MongoDB 6
- **Authentication**: JWT tokens
- **File Storage**: Local filesystem
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB free disk space

### For Manual Installation
- Python 3.11+
- Node.js 18+
- MongoDB 6+
- Yarn package manager

## 🚀 Installation

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/personal-website-template.git
   cd personal-website-template
   ```

2. **Install Docker (Ubuntu)**
   ```bash
   # Run the provided script
   sudo chmod +x scripts/ubuntu-install-docker.sh
   sudo bash scripts/ubuntu-install-docker.sh
   ```

3. **Deploy the application**
   ```bash
   # Make the deployment script executable
   sudo chmod +x scripts/run_compose.sh
   
   # Deploy the application
   sudo bash scripts/run_compose.sh
   ```

4. **Access the application**
   - Website: http://your-server-ip:8080/
   - Admin Panel: http://your-server-ip:8080/ (login required)
   - API: http://your-server-ip:8001/api/

### Option 2: Manual Installation (Ubuntu)

1. **Install system dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y
   
   # Install Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install Yarn
   npm install -g yarn
   
   # Install MongoDB 6
   wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
   echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
   sudo apt-get update
   sudo apt-get install -y mongodb-org
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

2. **Clone and setup the project**
   ```bash
   git clone https://github.com/yourusername/personal-website-template.git
   cd personal-website-template
   ```

3. **Setup Backend**
   ```bash
   cd backend
   
   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file
   cat > .env << EOF
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=personal_website_db
   CORS_ORIGINS=http://localhost:3000
   EOF
   
   # Start backend
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

4. **Setup Frontend** (in new terminal)
   ```bash
   cd frontend
   
   # Install dependencies
   yarn install
   
   # Create .env file
   cat > .env << EOF
   REACT_APP_BACKEND_URL=http://localhost:8001/api
   EOF
   
   # Start frontend
   yarn start
   ```

## ⚙️ Configuration

### Initial Admin Setup

1. **Access the website** at http://your-domain/
2. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin`
3. **Change credentials immediately** when prompted
4. **Configure settings** through Admin → Settings

### Environment Variables

#### Backend (.env)
```bash
MONGO_URL=mongodb://mongo:27017
DB_NAME=personal_website_db
CORS_ORIGINS=*
```

#### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001/api
```

### Admin Settings Categories

#### Basic Settings
- Site title and email
- File upload size limits
- Contact form cooldown

#### Appearance
- Background (color, gradient, image)
- Theme colors (primary, secondary, accent)
- Custom fonts and CSS

#### SEO Configuration
- Meta description and keywords
- Google Analytics integration
- Search Console verification
- Custom robots.txt

#### Social Media
- Facebook, Twitter, Instagram
- LinkedIn, GitHub, YouTube

#### Email Notifications
- SMTP server configuration
- Contact form notifications
- New blog post alerts

#### Blog Settings
- Posts per page
- Auto-excerpt length
- Default author
- Comments system

## 📖 Usage

### Content Management

#### Pages
1. Go to **Admin → Pages**
2. Create new pages or edit existing ones
3. Use the rich text editor for formatting
4. Set custom slugs for SEO-friendly URLs

#### Blog Posts
1. Go to **Admin → Blog**
2. Create new posts with:
   - Title and slug
   - Rich content with images
   - Tags (comma-separated)
   - Author and featured image
   - Publish/draft status

#### Advanced Search
- **Text Search**: Search titles, content, excerpts
- **Tag Filtering**: Filter by specific tags
- **Author Filter**: Find posts by author
- **Date Range**: Search within date ranges
- **Highlighting**: Search terms highlighted in results

### File Management
1. Go to **Admin → Files**
2. Upload images, documents, videos
3. Copy URLs for use in content
4. Manage uploaded files

### Analytics
- View visitor statistics
- Track page popularity
- Monitor user behavior
- Export analytics data

## 🐳 Docker Deployment

### Production Deployment

1. **Update docker-compose.yml for production**
   ```yaml
   version: "3.9"
   services:
     frontend:
       build:
         args:
           - REACT_APP_BACKEND_URL=https://yourdomain.com/api
   ```

2. **Configure reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:80;
       }
       
       location /api {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Enable SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

### Environment-Specific Deployments

#### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

#### Staging
```bash
docker-compose -f docker-compose.staging.yml up
```

#### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/login` - User login
- `GET /api/me` - Get current user
- `POST /api/change-password` - Change password
- `POST /api/change-credentials` - Change username/password

### Blog Endpoints
- `GET /api/blog` - Get blog posts (with pagination, filtering)
- `POST /api/blog/search` - Advanced blog search
- `GET /api/blog/tags` - Get all tags
- `GET /api/blog/authors` - Get all authors
- `GET /api/blog/{slug}` - Get specific post
- `POST /api/blog` - Create post (admin)
- `PUT /api/blog/{id}` - Update post (admin)
- `DELETE /api/blog/{id}` - Delete post (admin)

### Content Management
- `GET /api/pages` - Get all pages (admin)
- `GET /api/page/{slug}` - Get specific page
- `POST /api/pages` - Create page (admin)
- `PUT /api/pages/{id}` - Update page (admin)
- `DELETE /api/pages/{id}` - Delete page (admin)

### File Management
- `POST /api/upload` - Upload file (admin)
- `GET /api/uploads/{filename}` - Get uploaded file

### Settings & Configuration
- `GET /api/settings` - Get all settings (admin)
- `PUT /api/settings` - Update settings (admin)
- `GET /api/public-settings` - Get public settings
- `GET /api/robots.txt` - Dynamic robots.txt
- `GET /api/sitemap.xml` - Dynamic sitemap

## 🔧 Development

### Local Development Setup

1. **Start services**
   ```bash
   # Backend
   cd backend && uvicorn server:app --reload --port 8001
   
   # Frontend
   cd frontend && yarn start
   
   # MongoDB
   mongod
   ```

2. **Development Tools**
   ```bash
   # Format Python code
   black backend/
   
   # Format React code
   cd frontend && yarn format
   
   # Run tests
   cd backend && pytest
   cd frontend && yarn test
   ```

### Project Structure
```
sectorfive-website/
├── backend/
│   ├── server.py          # FastAPI main application
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile        # Backend container
│   └── uploads/          # File upload directory
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   ├── App.css       # Styling
│   │   └── index.js      # React entry point
│   ├── public/           # Static assets
│   ├── package.json      # Node dependencies
│   └── Dockerfile        # Frontend container
├── scripts/
│   ├── ubuntu-install-docker.sh  # Docker installation
│   └── run_compose.sh            # Deployment script
├── docker-compose.yml    # Container orchestration
└── README.md            # This file
```

### Making Changes

1. **Backend Changes**
   - Edit `backend/server.py`
   - Update `requirements.txt` if adding dependencies
   - Restart backend service

2. **Frontend Changes**
   - Edit files in `frontend/src/`
   - Hot reload is enabled in development
   - Build production: `yarn build`

3. **Database Changes**
   - Models are defined in `server.py`
   - MongoDB handles schema flexibility
   - Use admin interface for data management

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make changes and commit**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open Pull Request**

### Code Style
- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Use Prettier, ESLint configuration
- **Commit**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Update `docker-compose.yml` with production URLs
- [ ] Configure SSL certificates
- [ ] Set up backup strategy for MongoDB
- [ ] Configure monitoring and logging
- [ ] Update DNS records

### Post-Deployment
- [ ] Change default admin credentials
- [ ] Configure all settings through admin panel
- [ ] Test all functionality
- [ ] Set up automated backups
- [ ] Configure monitoring alerts

## 📈 Performance Tips

- **Database**: Create indexes for frequently queried fields
- **Images**: Optimize uploaded images for web
- **Caching**: Implement Redis for session storage in production
- **CDN**: Use CDN for static assets
- **Monitoring**: Set up application performance monitoring

---

**Made with ❤️ for the retro web enthusiasts**