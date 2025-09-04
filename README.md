# Sectorfive.win Retro Personal Website

A retro-styled personal website with admin dashboard, CMS (pages + blog), file uploads, analytics, contact form, and customizable background. Built with FastAPI + MongoDB backend and React frontend.

## What changed in this update

- Replaced TinyMCE (requires API key) with React Quill (Quill) which is open-source (MIT) and works well on older browsers supported by React 18
- Removed bracketed emoji fallback labels like `[SEND]` so buttons/labels are clean
- Added Reply button in Admin > Contacts that opens default mail app (mailto:) with recipient email, subject, and original message prefilled
- Contact messages were already stored; Admin can list, search, paginate, and delete. Now Quick Stats also includes counts for Pages, Posts, and Messages
- Window title color made black for visibility on gray backgrounds
- Background customization added under Settings: Default CSS (current), Solid Color, CSS Gradient, or Image (URL or upload). If not set, the original gradient remains
- Implemented public settings endpoint so background applies to public pages without login
- Headings and content styles tuned to be more distinct and readable

## Tech stack
- Backend: FastAPI, MongoDB (motor), JWT auth
- Frontend: React 18, React Router, Axios, React Quill editor

## Environment
- Frontend uses REACT_APP_BACKEND_URL from frontend/.env
- Backend connects to Mongo using MONGO_URL from backend/.env
- Backend runs at 0.0.0.0:8001 (managed by supervisor)

## API additions
- GET /api/public-settings: Returns site_title and background settings for public use
- PUT /api/settings now accepts optional fields: background_type, background_value, background_image_url

## Background options
- default: keeps current CSS gradient background
- color: set background_value to a color (e.g., #112233 or "teal")
- gradient: set background_value to a complete CSS gradient (e.g., `linear-gradient(135deg, #245edc, #1a4298)`)
- image: use background_image_url, or upload via Admin > Settings (uses /api/upload), which fills the URL automatically

## Compatibility
- Designed to work on modern and slightly older browsers supported by React 18 (e.g., Chrome 80+, Firefox 78 ESR, Safari 12+). CSS includes fallbacks for older flexbox implementations.

## Development
- Install frontend deps: yarn
- Install backend deps: pip install -r backend/requirements.txt
- Restart services after dependency changes: `sudo supervisorctl restart all`

## Default Admin
- Username: Sectorfive
- Password: KamenkoTV258!