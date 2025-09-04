from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import shutil
from pathlib import Path
import hashlib
import jwt
import uuid
import mimetypes
from urllib.parse import unquote
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
JWT_SECRET = "retro-personal-website-secret-key-2024"
security = HTTPBearer(auto_error=False)

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
    excerpt: Optional[str] = None
    author: str = "Admin"
    tags: List[str] = []
    featured_image: Optional[str] = None
    published: bool = True
    meta_description: Optional[str] = None

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class UserUpdate(BaseModel):
    username: str
    email: str
    display_name: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class Settings(BaseModel):
    site_title: str
    site_email: str
    meta_description: str
    background_type: str
    social_links: Dict[str, str] = {}
    seo_settings: Dict[str, Any] = {}
    theme_settings: Dict[str, Any] = {}

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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("username")
        if not username or username not in data_storage["users"]:
            raise HTTPException(status_code=401, detail="Invalid token")
        return data_storage["users"][username]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize default data
def initialize_data():
    # Create admin user
    admin_user = {
        "id": "admin-user-id",
        "username": "admin",
        "email": "admin@localhost",
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
        "content": "<h2>Welcome to Your Personal Website!</h2><p>This is your personal website template. You can edit this content in the Admin panel.</p><p>Features include:</p><ul><li>Retro Windows-style design</li><li>Blog system with rich text editor</li><li>Contact form management</li><li>Analytics dashboard</li><li>Full admin panel</li></ul>",
        "is_homepage": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    data_storage["pages"]["home"] = homepage
    
    # Create sample blog posts
    sample_post1 = {
        "id": "sample-post-1",
        "title": "Welcome to Your New Blog!",
        "slug": "welcome-to-your-new-blog",
        "content": "<p>This is your first blog post! You can edit or delete this post from the admin panel.</p><p>Your blog supports:</p><ul><li>Rich text editing with ReactQuill</li><li>Advanced search and filtering</li><li>Tag system with tag clouds</li><li>Draft and publish system</li><li>Featured images</li><li>Auto-generated excerpts</li><li>SEO optimization</li></ul><p>Start creating amazing content!</p>",
        "excerpt": "Welcome to your new blog! This post showcases the advanced features available in your personal website template.",
        "author": "Admin",
        "tags": ["welcome", "getting-started", "blog"],
        "featured_image": None,
        "published": True,
        "meta_description": "Welcome post for the personal website template blog",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    data_storage["blog_posts"]["welcome-to-your-new-blog"] = sample_post1
    
    sample_post2 = {
        "id": "sample-post-2",
        "title": "Blog Features Overview",
        "slug": "blog-features-overview",
        "content": "<h2>Advanced Blog Features</h2><p>Your personal website template includes a comprehensive blog system with modern features:</p><h3>Content Management</h3><ul><li><strong>Rich Text Editor:</strong> Create beautiful posts with ReactQuill</li><li><strong>Draft System:</strong> Save drafts and publish when ready</li><li><strong>Auto Excerpts:</strong> Automatic excerpt generation</li></ul><h3>Organization</h3><ul><li><strong>Tagging System:</strong> Organize posts with tags</li><li><strong>Search:</strong> Full-text search across all content</li><li><strong>Filtering:</strong> Filter by tags, authors, and dates</li></ul><h3>SEO & Performance</h3><ul><li><strong>Meta Descriptions:</strong> Custom SEO descriptions</li><li><strong>Featured Images:</strong> Social media ready</li><li><strong>Responsive Design:</strong> Works on all devices</li></ul>",
        "excerpt": "Discover the advanced features available in your blog system, from rich text editing to SEO optimization.",
        "author": "Admin",
        "tags": ["features", "blogging", "tutorial"],
        "featured_image": None,
        "published": True,
        "meta_description": "Overview of advanced blog features in the personal website template",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    }
    data_storage["blog_posts"]["blog-features-overview"] = sample_post2
    
    # Create default settings
    default_settings = {
        "site_title": "Personal Website Template",
        "site_email": "admin@localhost",
        "meta_description": "A retro-styled personal website template with modern functionality",
        "background_type": "default",
        "social_links": {},
        "seo_settings": {},
        "theme_settings": {}
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
async def me(current_user = Depends(verify_token)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "display_name": current_user["display_name"],
        "must_change_password": current_user["must_change_password"],
        "is_owner": current_user["is_owner"]
    }

@app.post("/api/change-credentials")
async def change_credentials(old_password: str, new_username: str, new_password: str, current_user = Depends(verify_token)):
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid current password")
    
    # Update credentials
    old_username = current_user["username"]
    current_user["username"] = new_username
    current_user["password_hash"] = hash_password(new_password)
    current_user["must_change_password"] = False
    
    # Update storage key if username changed
    if old_username != new_username:
        data_storage["users"][new_username] = current_user
        del data_storage["users"][old_username]
    
    return {"message": "Credentials updated successfully"}

# Page endpoints
@app.get("/api/page/{slug}")
async def get_page(slug: str):
    page = data_storage["pages"].get(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@app.get("/api/pages")
async def get_pages(current_user = Depends(verify_token)):
    return list(data_storage["pages"].values())

@app.post("/api/pages")
async def create_page(page: Page, current_user = Depends(verify_token)):
    page_id = str(uuid.uuid4())
    new_page = {
        "id": page_id,
        "title": page.title,
        "slug": page.slug,
        "content": page.content,
        "is_homepage": page.is_homepage,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if page.slug in data_storage["pages"]:
        raise HTTPException(status_code=400, detail="Page with this slug already exists")
    
    data_storage["pages"][page.slug] = new_page
    return new_page

@app.put("/api/pages/{page_id}")
async def update_page(page_id: str, title: str, content: str, current_user = Depends(verify_token)):
    # Find page by ID
    page_to_update = None
    page_slug = None
    for slug, page in data_storage["pages"].items():
        if page["id"] == page_id:
            page_to_update = page
            page_slug = slug
            break
    
    if not page_to_update:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page_to_update["title"] = title
    page_to_update["content"] = content
    page_to_update["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return page_to_update

@app.delete("/api/pages/{page_id}")
async def delete_page(page_id: str, current_user = Depends(verify_token)):
    # Find and delete page by ID
    page_to_delete = None
    page_slug = None
    for slug, page in data_storage["pages"].items():
        if page["id"] == page_id:
            if page.get("is_homepage"):
                raise HTTPException(status_code=400, detail="Cannot delete homepage")
            page_to_delete = page
            page_slug = slug
            break
    
    if not page_to_delete:
        raise HTTPException(status_code=404, detail="Page not found")
    
    del data_storage["pages"][page_slug]
    return {"message": "Page deleted successfully"}

# Blog tags and analytics
@app.get("/api/blog/tags")
async def get_blog_tags():
    """Get all unique tags with usage counts"""
    tag_counts = {}
    for post in data_storage["blog_posts"].values():
        if post.get("published", True):  # Only count published posts
            for tag in post.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by usage count descending
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"name": tag, "count": count} for tag, count in sorted_tags]

@app.get("/api/blog/stats")
async def get_blog_stats(current_user = Depends(verify_token)):
    """Get blog statistics for admin dashboard"""
    posts = list(data_storage["blog_posts"].values())
    published_posts = [p for p in posts if p.get("published", True)]
    draft_posts = [p for p in posts if not p.get("published", True)]
    
    # Get authors
    authors = list(set(p.get("author", "Unknown") for p in posts))
    
    # Get recent posts
    recent_posts = sorted(posts, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    
    return {
        "total_posts": len(posts),
        "published_posts": len(published_posts),
        "draft_posts": len(draft_posts),
        "total_authors": len(authors),
        "authors": authors,
        "recent_posts": recent_posts
    }

# Blog endpoints with advanced features
@app.get("/api/blog")
async def get_blog_posts(
    search: str = "",
    tags: str = "",
    author: str = "", 
    published: Optional[bool] = None,
    date_from: str = "",
    date_to: str = "",
    page: int = 1,
    limit: int = 10
):
    posts = list(data_storage["blog_posts"].values())
    
    # Filter by published status
    if published is not None:
        posts = [p for p in posts if p.get("published", True) == published]
    
    # Filter by search term (title, content, excerpt)
    if search:
        search_lower = search.lower()
        posts = [p for p in posts if (
            search_lower in p.get("title", "").lower() or
            search_lower in p.get("content", "").lower() or
            search_lower in p.get("excerpt", "").lower()
        )]
    
    # Filter by tags
    if tags:
        tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
        posts = [p for p in posts if any(
            tag in [t.lower() for t in p.get("tags", [])]
            for tag in tag_list
        )]
    
    # Filter by author
    if author:
        posts = [p for p in posts if author.lower() in p.get("author", "").lower()]
    
    # Filter by date range
    if date_from:
        posts = [p for p in posts if p.get("created_at", "") >= date_from]
    if date_to:
        posts = [p for p in posts if p.get("created_at", "") <= date_to]
    
    # Sort by created_at descending
    posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_posts = posts[start:end]
    
    # Generate auto excerpts for posts without them
    for post in paginated_posts:
        if not post.get("excerpt"):
            content = post.get("content", "")
            # Strip HTML tags for excerpt
            import re
            plain_text = re.sub(r'<[^>]+>', '', content)
            post["excerpt"] = plain_text[:200] + "..." if len(plain_text) > 200 else plain_text
    
    return {
        "posts": paginated_posts,
        "pagination": {
            "current_page": page,
            "total_pages": (len(posts) + limit - 1) // limit,
            "total_results": len(posts),
            "per_page": limit
        }
    }

@app.get("/api/blog/{slug}")
async def get_blog_post(slug: str):
    post = data_storage["blog_posts"].get(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.post("/api/blog")
async def create_blog_post(post: BlogPost, current_user = Depends(verify_token)):
    post_id = str(uuid.uuid4())
    
    # Auto-generate excerpt if not provided
    excerpt = post.excerpt
    if not excerpt and post.content:
        import re
        plain_text = re.sub(r'<[^>]+>', '', post.content)
        excerpt = plain_text[:200] + "..." if len(plain_text) > 200 else plain_text
    
    new_post = {
        "id": post_id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": excerpt,
        "author": post.author,
        "tags": post.tags,
        "featured_image": post.featured_image,
        "published": post.published,
        "meta_description": post.meta_description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if post.slug in data_storage["blog_posts"]:
        raise HTTPException(status_code=400, detail="Post with this slug already exists")
    
    data_storage["blog_posts"][post.slug] = new_post
    return new_post

@app.put("/api/blog/{post_id}")
async def update_blog_post(
    post_id: str, 
    title: str, 
    content: str, 
    excerpt: Optional[str] = None,
    tags: Optional[List[str]] = None,
    featured_image: Optional[str] = None,
    published: Optional[bool] = None,
    meta_description: Optional[str] = None,
    current_user = Depends(verify_token)
):
    # Find post by ID
    post_to_update = None
    post_slug = None
    for slug, post in data_storage["blog_posts"].items():
        if post["id"] == post_id:
            post_to_update = post
            post_slug = slug
            break
    
    if not post_to_update:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Update fields
    post_to_update["title"] = title
    post_to_update["content"] = content
    post_to_update["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if excerpt is not None:
        post_to_update["excerpt"] = excerpt
    elif content:  # Auto-generate excerpt if not provided
        import re
        plain_text = re.sub(r'<[^>]+>', '', content)
        post_to_update["excerpt"] = plain_text[:200] + "..." if len(plain_text) > 200 else plain_text
    
    if tags is not None:
        post_to_update["tags"] = tags
    if featured_image is not None:
        post_to_update["featured_image"] = featured_image
    if published is not None:
        post_to_update["published"] = published
    if meta_description is not None:
        post_to_update["meta_description"] = meta_description
    
    return post_to_update

@app.delete("/api/blog/{post_id}")
async def delete_blog_post(post_id: str, current_user = Depends(verify_token)):
    # Find and delete post by ID
    post_to_delete = None
    post_slug = None
    for slug, post in data_storage["blog_posts"].items():
        if post["id"] == post_id:
            post_to_delete = post
            post_slug = slug
            break
    
    if not post_to_delete:
        raise HTTPException(status_code=404, detail="Post not found")
    
    del data_storage["blog_posts"][post_slug]
    return {"message": "Post deleted successfully"}

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

# Contact messages management
@app.get("/api/contact-messages")
async def get_contact_messages(page: int = 1, limit: int = 20, search: str = "", current_user = Depends(verify_token)):
    messages = data_storage["contact_messages"]
    
    # Filter by search term
    if search:
        messages = [m for m in messages if search.lower() in m["name"].lower() or search.lower() in m["email"].lower() or search.lower() in m["message"].lower()]
    
    # Sort by newest first
    messages.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_messages = messages[start:end]
    
    return {
        "messages": paginated_messages,
        "pagination": {
            "current_page": page,
            "total_pages": (len(messages) + limit - 1) // limit,
            "total_results": len(messages),
            "per_page": limit
        }
    }

@app.delete("/api/contact-messages/{message_id}")
async def delete_contact_message(message_id: str, current_user = Depends(verify_token)):
    data_storage["contact_messages"] = [m for m in data_storage["contact_messages"] if m["id"] != message_id]
    return {"message": "Contact message deleted successfully"}

# Analytics tracking
@app.post("/api/track")
async def track_visit(request: Request):
    visit = {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "page_url": request.headers.get("referer", ""),
        "browser": request.headers.get("user-agent", "").split()[0] if request.headers.get("user-agent") else "Unknown",
        "country": "Unknown",  # Would need GeoIP service for real country detection
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    data_storage["analytics"].append(visit)
    return {"status": "tracked"}

@app.get("/api/analytics")
async def get_analytics(page: int = 1, limit: int = 20, search: str = "", country: str = "", current_user = Depends(verify_token)):
    visits = data_storage["analytics"]
    
    # Filter by search term and country
    if search:
        visits = [v for v in visits if search.lower() in v.get("ip_address", "").lower() or search.lower() in v.get("page_url", "").lower() or search.lower() in v.get("browser", "").lower()]
    
    if country and country != "all":
        visits = [v for v in visits if v.get("country", "") == country]
    
    # Sort by newest first
    visits.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Calculate stats
    total_visits = len(data_storage["analytics"])
    unique_visitors = len(set(v["ip_address"] for v in data_storage["analytics"]))
    
    # Get top countries and browsers
    countries = {}
    browsers = {}
    for visit in data_storage["analytics"]:
        country = visit.get("country", "Unknown")
        browser = visit.get("browser", "Unknown")
        countries[country] = countries.get(country, 0) + 1
        browsers[browser] = browsers.get(browser, 0) + 1
    
    top_countries = [{"_id": k, "count": v} for k, v in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]]
    top_browsers = [{"_id": k, "count": v} for k, v in sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated_visits = visits[start:end]
    
    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "recent_visits": paginated_visits,
        "top_countries": top_countries,
        "top_browsers": top_browsers,
        "pagination": {
            "current_page": page,
            "total_pages": (len(visits) + limit - 1) // limit,
            "total_results": len(visits),
            "per_page": limit
        }
    }

# Settings management
@app.get("/api/settings")
async def get_settings(current_user = Depends(verify_token)):
    return data_storage["settings"]

@app.get("/api/public-settings")
async def get_public_settings():
    return data_storage["settings"]

@app.put("/api/settings")
async def update_settings(settings: Settings, current_user = Depends(verify_token)):
    data_storage["settings"] = {
        "site_title": settings.site_title,
        "site_email": settings.site_email,
        "meta_description": settings.meta_description,
        "background_type": settings.background_type,
        "social_links": settings.social_links,
        "seo_settings": settings.seo_settings,
        "theme_settings": settings.theme_settings
    }
    return data_storage["settings"]

# File upload system
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user = Depends(verify_token)):
    # Validate file type and size
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"]
    max_size = 10 * 1024 * 1024  # 10MB
    
    # Check file type
    content_type = file.content_type
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "filename": unique_filename,
        "original_name": file.filename,
        "size": len(content),
        "url": f"/api/uploads/{unique_filename}"
    }

@app.get("/api/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=content_type)

# Backup and restore functionality
@app.post("/api/backup")
async def create_backup(current_user = Depends(verify_token)):
    backup_data = {
        "users": data_storage["users"],
        "pages": data_storage["pages"],
        "blog_posts": data_storage["blog_posts"],
        "settings": data_storage["settings"],
        "contact_messages": data_storage["contact_messages"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = UPLOAD_DIR / backup_filename
    
    with open(backup_path, "w") as f:
        json.dump(backup_data, f, indent=2)
    
    return {
        "message": "Backup created successfully",
        "filename": backup_filename,
        "download_url": f"/api/uploads/{backup_filename}"
    }

@app.post("/api/restore")
async def restore_backup(file: UploadFile = File(...), current_user = Depends(verify_token)):
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
        
        # Validate backup structure
        required_keys = ["users", "pages", "blog_posts", "settings"]
        for key in required_keys:
            if key not in backup_data:
                raise HTTPException(status_code=400, detail=f"Invalid backup file: missing {key}")
        
        # Restore data
        data_storage["users"] = backup_data["users"]
        data_storage["pages"] = backup_data["pages"]
        data_storage["blog_posts"] = backup_data["blog_posts"]
        data_storage["settings"] = backup_data["settings"]
        data_storage["contact_messages"] = backup_data.get("contact_messages", [])
        
        return {"message": "Backup restored successfully"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring backup: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)