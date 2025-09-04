from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from pathlib import Path
import hashlib
import jwt
from datetime import datetime, timezone, timedelta

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
data_storage = {
    "users": {},
    "pages": {},
    "blog_posts": {},
    "contact_messages": [],
    "analytics": [],
    "settings": {}
}

# Security
JWT_SECRET = "sectorfive-secure-secret-key-2024"

# Create uploads directory
ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class Page(BaseModel):
    title: str
    slug: str
    content: str
    is_homepage: bool = False

class BlogPost(BaseModel):
    title: str
    slug: str
    content: str
    author: str = "Admin"
    published: bool = True

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Initialize default data
def initialize_data():
    # Create admin user
    admin_user = {
        "id": "admin-user-id",
        "username": "admin",
        "email": "admin@sectorfive.win",
        "password_hash": hash_password("admin"),
        "display_name": "Site Owner",
        "must_change_password": True,
        "is_owner": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    data_storage["users"]["admin"] = admin_user
    
    # Create default homepage
    homepage = {
        "id": "homepage-id",
        "title": "Home",
        "slug": "home",
        "content": "<h2>Welcome to Sectorfive.win!</h2><p>This is your personal website. You can edit this content in the Admin panel.</p>",
        "is_homepage": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    data_storage["pages"]["home"] = homepage
    
    # Create default settings
    default_settings = {
        "site_title": "Sectorfive Personal Website",
        "site_email": "admin@sectorfive.win",
        "meta_description": "Sectorfive Personal Website",
        "background_type": "default"
    }
    data_storage["settings"] = default_settings

# Initialize data on startup
initialize_data()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Auth endpoints
@app.post("/api/login")
async def login(user_data: UserLogin):
    user = data_storage["users"].get(user_data.username)
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user_data.username)
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "must_change_password": user.get("must_change_password", False)
    }

@app.get("/api/me")
async def me():
    # For simplicity, return admin user info
    user = data_storage["users"]["admin"]
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "display_name": user["display_name"],
        "must_change_password": user["must_change_password"],
        "is_owner": user["is_owner"]
    }

# Page endpoints
@app.get("/api/page/{slug}")
async def get_page(slug: str):
    page = data_storage["pages"].get(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@app.get("/api/pages")
async def get_pages():
    return list(data_storage["pages"].values())

# Blog endpoints
@app.get("/api/blog")
async def get_blog_posts():
    posts = list(data_storage["blog_posts"].values())
    # Sort by created_at descending
    posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return posts

@app.get("/api/blog/{slug}")
async def get_blog_post(slug: str):
    post = data_storage["blog_posts"].get(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Contact form
@app.post("/api/contact")
async def contact_form(contact: ContactForm, request: Request):
    message = {
        "id": f"msg-{len(data_storage['contact_messages'])+1}",
        "name": contact.name,
        "email": contact.email,
        "message": contact.message,
        "ip_address": request.client.host if request.client else "unknown",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    data_storage["contact_messages"].append(message)
    return {"message": "Message sent successfully"}

# Analytics tracking
@app.post("/api/track")
async def track_visit(request: Request):
    visit = {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "page_url": request.headers.get("referer", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    data_storage["analytics"].append(visit)
    return {"status": "tracked"}

# Settings
@app.get("/api/public-settings")
async def get_public_settings():
    return data_storage["settings"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)