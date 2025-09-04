# sectorfive.win — Retro Personal Website

Full-stack app: FastAPI + MongoDB + React, with retro UI, pages/blog CMS, file uploads, analytics, contact form, and customizable background.

Repository: https://github.com/SectorV5/sectorfive.win

Highlights
- Open-source editor (Quill) — no API keys, GPLv3-compatible
- Admin dashboard with Pages, Blog, Analytics, Contacts, Settings
- Contact messages stored, Reply opens default mail app
- Background customization: default, color, gradient, or image
- First-time admin credential change flow for security

Quick start on Ubuntu (recommended: Docker Compose)
1) Install Docker + Compose plugin
- curl -fsSL https://raw.githubusercontent.com/SectorV5/sectorfive.win/main/scripts/ubuntu-install-docker.sh -o ubuntu-install-docker.sh
- bash ubuntu-install-docker.sh
- Log out and back in (if needed) so your user can run docker without sudo

2) Clone and run
- git clone https://github.com/SectorV5/sectorfive.win.git
- cd sectorfive.win
- bash scripts/run_compose.sh

That’s it. Services
- Frontend: http://YOUR_SERVER_IP/ (served by nginx)
- Backend: http://YOUR_SERVER_IP:8001/api
- MongoDB: localhost:27017 (internal by compose)

Persistent data
- MongoDB data is persisted in the docker volume mongo_data
- Uploaded files are kept inside backend image’s uploads folder while running. To persist uploads across rebuilds, map a host volume to backend at ./backend/uploads via docker-compose (optional):

  volumes:
    - ./backend/uploads:/app/uploads

Production tuning
- Set a real email in Settings for contact messages
- Configure a domain and TLS termination with Caddy/Nginx/Traefik. The frontend container listens on port 80
- For single-domain setups, frontend proxies /api to backend automatically

Run on boot
- Docker’s restart policies are already set to unless-stopped so the app auto-starts after reboot.
- Ensure Docker is enabled: sudo systemctl enable docker

First-time admin login and credential change
- Default admin credentials: username admin, password admin
- After login, you will be prompted to change username and password. You cannot proceed to the admin dashboard without doing this in the UI

Manual (non-Docker) setup (optional)
- Backend: Python 3.11+, pip install -r backend/requirements.txt, set env vars MONGO_URL and DB_NAME, run: python -m uvicorn server:app --host 0.0.0.0 --port 8001
- MongoDB: Install and run locally
- Frontend: Node 18+, yarn install, REACT_APP_BACKEND_URL should point to your backend (or leave unset and it will use same-origin /api), yarn build and serve via nginx or use yarn start for dev

Environment variables
- Backend: MONGO_URL (mongo connection), DB_NAME (database name), CORS_ORIGINS (optional)
- Frontend build arg: REACT_APP_BACKEND_URL (optional, for same-origin leave empty and nginx will proxy /api)

Security notes
- Change admin/admin immediately at first login (the UI forces it)
- Use HTTPS in production
- Keep Docker and host packages updated

Troubleshooting
- docker compose logs -f backend
- docker compose logs -f frontend
- If port 80 is busy, change the port mapping in docker-compose.yml under frontend

Default routes
- Public:
  - GET /api/page/home
  - GET /api/blog, GET /api/blog/:slug
  - POST /api/contact
  - GET /api/public-settings
- Admin (require login):
  - POST /api/login, GET /api/me
  - POST /api/change-credentials (first-time change)
  - POST /api/change-password
  - Pages: /api/pages CRUD
  - Blog: /api/blog CRUD
  - Analytics: /api/analytics
  - Uploads: /api/upload, GET /api/uploads/:filename

Default admin
- Username: admin
- Password: admin
- First login will require changing both username and password