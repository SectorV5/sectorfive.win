# Sectorfive Personal Website - Replit Setup

## Overview
This is a full-stack personal website imported from GitHub and adapted for the Replit environment. The project features a retro-styled interface with a FastAPI backend and HTML/JavaScript frontend.

## Architecture
- **Backend**: FastAPI (Python) running on port 8000
- **Frontend**: HTML/JavaScript with Python HTTP server on port 5000
- **Database**: In-memory storage (simplified from original MongoDB setup)
- **Deployment**: VM deployment target for persistent server state

## Recent Changes (Sept 4, 2025)
- ✅ Imported GitHub project and adapted for Replit environment
- ✅ Simplified backend to use in-memory storage instead of MongoDB
- ✅ Created working HTML/JavaScript frontend with retro styling
- ✅ Configured CORS and proper host settings for Replit environment
- ✅ Set up workflows for both backend (port 8000) and frontend (port 5000)
- ✅ Configured deployment settings for VM target

## Project Structure
- `backend/server_simple.py` - Simplified FastAPI backend with in-memory storage
- `frontend/index.html` - Main frontend application with retro styling
- `frontend/simple_server.py` - Python HTTP server for frontend

## Features Working
- ✅ Homepage with customizable content
- ✅ Blog system (ready for content)
- ✅ Contact form with backend integration
- ✅ Admin login system (default: admin/admin)
- ✅ Retro Windows Aero-style UI
- ✅ CORS-enabled API for frontend-backend communication

## Default Credentials
- Username: `admin`
- Password: `admin`
- Note: Password should be changed on first login

## Technical Notes
- Backend uses port 8000 (allowed in Replit)
- Frontend uses port 5000 (standard for Replit webview)
- VM deployment ensures persistent server state
- CORS configured for cross-origin requests
- Auto-detects Replit environment for proper API URLs

## User Preferences
- Retro/nostalgic design aesthetic maintained
- Simple, functional interface prioritized
- Security considerations for admin access