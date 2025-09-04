from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import jwt
import aiofiles
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from user_agents import parse
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Security
JWT_SECRET = "sectorfive-secure-secret-key-2024"
security = HTTPBearer()

# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class UserPermissions(BaseModel):
    # Blog permissions
    blog_read_all: bool = True
    blog_write_new: bool = False
    blog_edit_own: bool = False
    blog_edit_all: bool = False
    blog_delete_posts: bool = False
    
    # Page permissions
    page_edit_homepage: bool = False
    page_edit_specific: List[str] = Field(default_factory=list)  # List of page IDs
    page_edit_all: bool = False
    page_create: bool = False
    page_delete: bool = False
    
    # Settings permissions
    settings_view_only: bool = True
    settings_edit_theme: bool = False
    settings_edit_seo: bool = False
    settings_edit_social: bool = False
    settings_edit_email: bool = False
    settings_edit_blog: bool = False
    settings_full_admin: bool = False
    
    # User management permissions
    users_view: bool = False
    users_create: bool = False
    users_edit: bool = False
    users_delete: bool = False
    
    # File management permissions
    files_upload: bool = False
    files_delete: bool = False
    files_manage_all: bool = False
    
    # Analytics permissions
    analytics_view: bool = False
    
    # Contact form permissions
    contact_view: bool = False
    contact_delete: bool = False

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    display_name: str = ""
    must_change_password: bool = True
    is_owner: bool = False  # The original admin user
    is_active: bool = True
    permissions: UserPermissions = Field(default_factory=UserPermissions)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    created_by: Optional[str] = None  # User ID who created this user

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    display_name: str = ""
    permissions: Optional[UserPermissions] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[UserPermissions] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    is_homepage: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PageCreate(BaseModel):
    title: str
    slug: str
    content: str

class PageUpdate(BaseModel):
    title: str
    content: str

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    author: str = "Admin"
    featured_image: Optional[str] = None
    published: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BlogPostCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = "Admin"
    featured_image: Optional[str] = None
    published: bool = True

class BlogPostUpdate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = "Admin"
    featured_image: Optional[str] = None
    published: bool = True

class BlogSearchRequest(BaseModel):
    query: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    published_only: bool = True
    page: int = 1
    limit: int = 10

class Analytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: str
    user_agent: str
    page_url: str
    referer: Optional[str] = None
    country: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Basic Settings
    max_file_size: int = 5368709120  # 5GB in bytes
    site_title: str = "Sectorfive Personal Website"
    site_email: str = "admin@sectorfive.win"
    contact_cooldown: int = 300  # 5 minutes in seconds
    
    # Appearance
    background_type: str = "default"  # default | color | gradient | image
    background_value: Optional[str] = None
    background_image_url: Optional[str] = None
    
    # Theme Customization
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    accent_color: str = "#28a745"
    font_family: str = "Arial, sans-serif"
    custom_css: Optional[str] = None
    
    # SEO Settings
    meta_description: str = "Sectorfive Personal Website"
    meta_keywords: str = "personal, website, blog, portfolio"
    google_analytics_id: Optional[str] = None
    google_search_console: Optional[str] = None
    robots_txt: str = "User-agent: *\nAllow: /"
    
    # Social Media Links
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # Email Notification Settings
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    notification_email: Optional[str] = None
    notify_on_contact: bool = False
    notify_on_new_blog: bool = False
    
    # Blog Settings
    posts_per_page: int = 10
    enable_comments: bool = False
    auto_excerpt_length: int = 200
    default_author: str = "Admin"

class ContactMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    message: str
    ip_address: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def parse_user_agent(user_agent_string: str) -> Dict[str, str]:
    user_agent = parse(user_agent_string)
    return {
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}"
    }

def get_country_from_ip(ip: str) -> str:
    # Simple placeholder
    return "Unknown"

def extract_excerpt(content: str, length: int = 200) -> str:
    """Extract plain text excerpt from HTML content"""
    import re
    # Remove HTML tags
    plain_text = re.sub('<[^<]+?>', '', content)
    # Clean whitespace
    plain_text = ' '.join(plain_text.split())
    # Truncate to desired length
    if len(plain_text) <= length:
        return plain_text
    return plain_text[:length].rsplit(' ', 1)[0] + '...'

def highlight_search_terms(text: str, query: str) -> str:
    """Highlight search terms in text"""
    if not query or not text:
        return text
    import re
    words = query.split()
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(f'<mark>{word}</mark>', text)
    return text

async def build_blog_search_query(search_request: BlogSearchRequest):
    """Build MongoDB query for blog search"""
    query = {}
    
    # Published filter
    if search_request.published_only:
        query["published"] = True
    
    # Text search
    search_conditions = []
    if search_request.query:
        search_term = search_request.query
        search_conditions.extend([
            {"title": {"$regex": search_term, "$options": "i"}},
            {"content": {"$regex": search_term, "$options": "i"}},
            {"excerpt": {"$regex": search_term, "$options": "i"}},
            {"tags": {"$regex": search_term, "$options": "i"}}
        ])
    
    # Tags filter
    if search_request.tags:
        search_conditions.append({"tags": {"$in": search_request.tags}})
    
    # Author filter
    if search_request.author:
        search_conditions.append({"author": {"$regex": search_request.author, "$options": "i"}})
    
    # Date range filter
    date_conditions = []
    if search_request.date_from:
        date_conditions.append({"created_at": {"$gte": search_request.date_from}})
    if search_request.date_to:
        date_conditions.append({"created_at": {"$lte": search_request.date_to}})
    
    # Combine all conditions
    if search_conditions:
        query["$or"] = search_conditions
    if date_conditions:
        query.update({k: v for d in date_conditions for k, v in d.items()})
    
    return query

async def check_rate_limit(ip: str, endpoint: str, limit_seconds: int = 300):
    key = f"{ip}:{endpoint}"
    current_time = time.time()
    if key in rate_limit_storage:
        last_request = rate_limit_storage[key]
        if current_time - last_request < limit_seconds:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please wait {int(limit_seconds - (current_time - last_request))} seconds."
            )
    rate_limit_storage[key] = current_time

async def track_visit(request: Request, page_url: str):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    referer = request.headers.get("referer")
    agent_info = parse_user_agent(user_agent)
    country = get_country_from_ip(client_ip)
    analytics_data = Analytics(
        ip_address=client_ip,
        user_agent=user_agent,
        page_url=page_url,
        referer=referer,
        country=country,
        browser=agent_info["browser"],
        os=agent_info["os"]
    )
    await db.analytics.insert_one(analytics_data.dict())

# Initialize default data
async def initialize_data():
    # Ensure an 'admin' user exists as the owner with full permissions
    admin_user = await db.users.find_one({"username": "admin"})
    if not admin_user:
        # Create owner permissions (full access to everything)
        owner_permissions = UserPermissions(
            # Blog permissions
            blog_read_all=True,
            blog_write_new=True,
            blog_edit_own=True,
            blog_edit_all=True,
            blog_delete_posts=True,
            # Page permissions
            page_edit_homepage=True,
            page_edit_all=True,
            page_create=True,
            page_delete=True,
            # Settings permissions
            settings_full_admin=True,
            settings_edit_theme=True,
            settings_edit_seo=True,
            settings_edit_social=True,
            settings_edit_email=True,
            settings_edit_blog=True,
            # User management permissions
            users_view=True,
            users_create=True,
            users_edit=True,
            users_delete=True,
            # File management permissions
            files_upload=True,
            files_delete=True,
            files_manage_all=True,
            # Analytics permissions
            analytics_view=True,
            # Contact form permissions
            contact_view=True,
            contact_delete=True
        )
        
        admin = User(
            username="admin",
            email="admin@sectorfive.win",
            display_name="Site Owner",
            password_hash=hash_password("admin"),
            must_change_password=True,
            is_owner=True,
            permissions=owner_permissions
        )
        await db.users.insert_one(admin.dict())

    # Create default settings if missing
    existing_settings = await db.settings.find_one()
    if not existing_settings:
        await db.settings.insert_one(Settings().dict())

    # Create default homepage if missing
    existing_homepage = await db.pages.find_one({"is_homepage": True})
    if not existing_homepage:
        homepage = Page(
            title="Home",
            slug="home",
            content="""<h2>Welcome!</h2><p>Edit this content in Admin → Pages.</p>""",
            is_homepage=True
        )
        await db.pages.insert_one(homepage.dict())

# Auth endpoints
@api_router.post("/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user_data.username)
    return {"access_token": token, "token_type": "bearer", "must_change_password": user.get("must_change_password", False)}

@api_router.get("/me")
async def me(current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"username": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update last login
    await db.users.update_one(
        {"username": current_user},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email"),
        "display_name": user.get("display_name", ""),
        "must_change_password": user.get("must_change_password", False),
        "is_owner": user.get("is_owner", False),
        "permissions": user.get("permissions", {}),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login")
    }

@api_router.post("/change-credentials")
async def change_credentials(username: str = Form(...), password: str = Form(...), current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"username": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if new username already exists (if different from current)
    if username != current_user:
        existing_user = await db.users.find_one({"username": username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Update credentials
    await db.users.update_one(
        {"username": current_user},
        {"$set": {
            "username": username,
            "password_hash": hash_password(password),
            "must_change_password": False,
            "last_login": datetime.now(timezone.utc)
        }}
    )
    
    # Return new token with new username
    token = create_token(username)
    return {"access_token": token, "token_type": "bearer", "must_change_password": False}

# Permission checking utilities
async def check_permission(username: str, permission_path: str) -> bool:
    """Check if user has specific permission"""
    user = await db.users.find_one({"username": username})
    if not user or not user.get("is_active", True):
        return False
    
    # Owner has all permissions
    if user.get("is_owner", False):
        return True
    
    permissions = user.get("permissions", {})
    
    # Navigate nested permission path (e.g., "blog.read_all")
    parts = permission_path.split(".")
    current = permissions
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, False)
        else:
            return False
    
    return bool(current)

async def require_permission(username: str, permission: str):
    """Raise HTTP exception if user lacks permission"""
    if not await check_permission(username, permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")

async def get_user_with_permissions(username: str):
    """Get user with full permission details"""
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# User management endpoints
@api_router.get("/users")
async def get_users(current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_view")
    
    users = []
    async for user in db.users.find({}):
        users.append({
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user.get("display_name", ""),
            "is_owner": user.get("is_owner", False),
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"],
            "last_login": user.get("last_login"),
            "created_by": user.get("created_by")
        })
    
    return {"users": users}

@api_router.post("/users")
async def create_user(user_data: UserCreate, current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_create")
    
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Get creator info
    creator = await db.users.find_one({"username": current_user})
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        password_hash=hash_password(user_data.password),
        must_change_password=True,
        is_owner=False,
        permissions=user_data.permissions or UserPermissions(),
        created_by=creator["id"] if creator else None
    )
    
    await db.users.insert_one(new_user.dict())
    
    return {"message": "User created successfully", "id": new_user.id}

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_view")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    return user

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_edit")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow editing owner user unless you are the owner
    current_user_data = await db.users.find_one({"username": current_user})
    if user.get("is_owner", False) and not current_user_data.get("is_owner", False):
        raise HTTPException(status_code=403, detail="Cannot edit owner user")
    
    # Build update data
    update_data = {}
    if user_data.email is not None:
        # Check if email already exists
        existing_email = await db.users.find_one({"email": user_data.email, "id": {"$ne": user_id}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data["email"] = user_data.email
    
    if user_data.display_name is not None:
        update_data["display_name"] = user_data.display_name
    
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    if user_data.permissions is not None:
        update_data["permissions"] = user_data.permissions.dict()
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {"message": "User updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_delete")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting owner user
    if user.get("is_owner", False):
        raise HTTPException(status_code=403, detail="Cannot delete owner user")
    
    # Don't allow deleting yourself
    current_user_data = await db.users.find_one({"username": current_user})
    if user["id"] == current_user_data["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete yourself")
    
    await db.users.delete_one({"id": user_id})
    
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, new_password: str = Form(...), current_user: str = Depends(get_current_user)):
    await require_permission(current_user, "users_edit")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": hash_password(new_password),
            "must_change_password": True
        }}
    )
    
    return {"message": "Password reset successfully"}

@api_router.post("/change-credentials")
async def change_credentials(
    old_password: str = Form(...),
    new_username: str = Form(...),
    new_password: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    user = await db.users.find_one({"username": current_user})
    if not user or not verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid old password")
    # prevent duplicate username
    if await db.users.find_one({"username": new_username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    await db.users.update_one(
        {"username": current_user},
        {"$set": {"username": new_username, "password_hash": hash_password(new_password), "must_change_password": False}}
    )
    return {"message": "Credentials updated successfully"}

# Page endpoints
@api_router.get("/page/{slug}")
async def get_page(slug: str, request: Request):
    await track_visit(request, f"/page/{slug}")
    if slug == "home":
        page = await db.pages.find_one({"is_homepage": True})
    else:
        page = await db.pages.find_one({"slug": slug})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return Page(**page)

@api_router.get("/pages", response_model=List[Page])
async def get_all_pages(current_user: str = Depends(get_current_user)):
    pages = await db.pages.find().to_list(length=None)
    return [Page(**page) for page in pages]

@api_router.post("/pages", response_model=Page)
async def create_page(page_data: PageCreate, current_user: str = Depends(get_current_user)):
    existing = await db.pages.find_one({"slug": page_data.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Page with this slug already exists")
    page = Page(title=page_data.title, slug=page_data.slug, content=page_data.content)
    await db.pages.insert_one(page.dict())
    return page

@api_router.put("/pages/{page_id}")
async def update_page(page_id: str, page_data: PageUpdate, current_user: str = Depends(get_current_user)):
    update_data = {
        "title": page_data.title,
        "content": page_data.content,
        "updated_at": datetime.now(timezone.utc)
    }
    result = await db.pages.update_one({"id": page_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page updated successfully"}

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, current_user: str = Depends(get_current_user)):
    page = await db.pages.find_one({"id": page_id})
    if page and page.get("is_homepage"):
        raise HTTPException(status_code=400, detail="Cannot delete homepage")
    result = await db.pages.delete_one({"id": page_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page deleted successfully"}

# Blog endpoints
@api_router.get("/blog", response_model=List[BlogPost])
async def get_blog_posts(
    request: Request,
    page: int = 1,
    limit: int = 10,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    published_only: bool = True
):
    await track_visit(request, "/blog")
    query = {}
    if published_only:
        query["published"] = True
    if tag:
        query["tags"] = tag
    if author:
        query["author"] = {"$regex": author, "$options": "i"}
    
    skip = (page - 1) * limit
    posts = await db.blog_posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    return [BlogPost(**post) for post in posts]

@api_router.post("/blog/search")
async def search_blog_posts(search_request: BlogSearchRequest):
    query = await build_blog_search_query(search_request)
    
    # Get total count
    total = await db.blog_posts.count_documents(query)
    
    # Get paginated results
    skip = (search_request.page - 1) * search_request.limit
    posts = await db.blog_posts.find(query).sort("created_at", -1).skip(skip).limit(search_request.limit).to_list(length=search_request.limit)
    
    # Process results with highlighting
    results = []
    for post in posts:
        blog_post = BlogPost(**post)
        if search_request.query:
            blog_post.title = highlight_search_terms(blog_post.title, search_request.query)
            blog_post.excerpt = highlight_search_terms(blog_post.excerpt or "", search_request.query)
        results.append(blog_post)
    
    return {
        "posts": results,
        "pagination": {
            "current_page": search_request.page,
            "total_pages": (total + search_request.limit - 1) // search_request.limit,
            "total_results": total,
            "per_page": search_request.limit
        }
    }

@api_router.get("/blog/tags")
async def get_blog_tags():
    """Get all unique tags from blog posts"""
    pipeline = [
        {"$match": {"published": True}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"tag": "$_id", "count": 1, "_id": 0}}
    ]
    tags = await db.blog_posts.aggregate(pipeline).to_list(length=None)
    return tags

@api_router.get("/blog/authors")
async def get_blog_authors():
    """Get all unique authors from blog posts"""
    authors = await db.blog_posts.distinct("author", {"published": True})
    return authors

@api_router.get("/blog/{slug}")
async def get_blog_post(slug: str, request: Request):
    await track_visit(request, f"/blog/{slug}")
    post = await db.blog_posts.find_one({"slug": slug})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return BlogPost(**post)

@api_router.post("/blog", response_model=BlogPost)
async def create_blog_post(post_data: BlogPostCreate, current_user: str = Depends(get_current_user)):
    existing = await db.blog_posts.find_one({"slug": post_data.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Blog post with this slug already exists")
    
    # Auto-generate excerpt if not provided
    excerpt = post_data.excerpt
    if not excerpt:
        settings = await db.settings.find_one() or {}
        excerpt_length = settings.get("auto_excerpt_length", 200)
        excerpt = extract_excerpt(post_data.content, excerpt_length)
    
    post = BlogPost(
        title=post_data.title,
        slug=post_data.slug,
        content=post_data.content,
        excerpt=excerpt,
        tags=post_data.tags,
        author=post_data.author,
        featured_image=post_data.featured_image,
        published=post_data.published
    )
    await db.blog_posts.insert_one(post.dict())
    return post

@api_router.put("/blog/{post_id}")
async def update_blog_post(post_id: str, post_data: BlogPostUpdate, current_user: str = Depends(get_current_user)):
    # Auto-generate excerpt if not provided
    excerpt = post_data.excerpt
    if not excerpt:
        settings = await db.settings.find_one() or {}
        excerpt_length = settings.get("auto_excerpt_length", 200)
        excerpt = extract_excerpt(post_data.content, excerpt_length)
    
    update_data = {
        "title": post_data.title,
        "content": post_data.content,
        "excerpt": excerpt,
        "tags": post_data.tags,
        "author": post_data.author,
        "featured_image": post_data.featured_image,
        "published": post_data.published,
        "updated_at": datetime.now(timezone.utc)
    }
    result = await db.blog_posts.update_one({"id": post_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {"message": "Blog post updated successfully"}

@api_router.delete("/blog/{post_id}")
async def delete_blog_post(post_id: str, current_user: str = Depends(get_current_user)):
    result = await db.blog_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {"message": "Blog post deleted successfully"}

# File upload endpoints
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    settings = await db.settings.find_one()
    max_size = settings["max_file_size"] if settings else 5368709120
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
    file_path = UPLOAD_DIR / unique_filename
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail="File too large")
        await f.write(content)
    return {"filename": unique_filename, "original_name": file.filename, "size": len(content)}

@api_router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Analytics endpoints
@api_router.get("/analytics")
async def get_analytics(
    current_user: str = Depends(get_current_user),
    search: Optional[str] = None,
    country: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    query = {}
    if search:
        query["$or"] = [
            {"ip_address": {"$regex": search, "$options": "i"}},
            {"user_agent": {"$regex": search, "$options": "i"}},
            {"page_url": {"$regex": search, "$options": "i"}},
            {"browser": {"$regex": search, "$options": "i"}},
            {"os": {"$regex": search, "$options": "i"}}
        ]
    if country and country != "all":
        query["country"] = country
    total_visits = await db.analytics.count_documents(query)
    unique_visitors = await db.analytics.distinct("ip_address", query)
    skip = (page - 1) * limit
    recent_visits_raw = await db.analytics.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
    recent_visits = [Analytics(**visit).dict() for visit in recent_visits_raw]
    pipeline = [{"$match": query}, {"$group": {"_id": "$page_url", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    top_pages = await db.analytics.aggregate(pipeline).to_list(length=10)
    country_pipeline = [{"$match": query}, {"$group": {"_id": "$country", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    top_countries = await db.analytics.aggregate(country_pipeline).to_list(length=10)
    browser_pipeline = [{"$match": query}, {"$group": {"_id": "$browser", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    top_browsers = await db.analytics.aggregate(browser_pipeline).to_list(length=10)
    return {
        "total_visits": total_visits,
        "unique_visitors": len(unique_visitors),
        "recent_visits": recent_visits,
        "top_pages": top_pages,
        "top_countries": top_countries,
        "top_browsers": top_browsers,
        "pagination": {"current_page": page, "total_pages": (total_visits + limit - 1) // limit, "total_results": total_visits}
    }

# Contact endpoints
@api_router.post("/contact")
async def submit_contact(contact_data: ContactForm, request: Request):
    client_ip = request.client.host
    settings = await db.settings.find_one() or {}
    cooldown = settings.get("contact_cooldown", 300)
    await check_rate_limit(client_ip, "contact", cooldown)
    contact = ContactMessage(
        name=contact_data.name,
        email=contact_data.email,
        message=contact_data.message,
        ip_address=client_ip
    )
    await db.contact_messages.insert_one(contact.dict())
    return {"message": "Contact message sent successfully"}

@api_router.get("/contact-messages")
async def get_contact_messages(current_user: str = Depends(get_current_user), page: int = 1, limit: int = 20, search: Optional[str] = None):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"message": {"$regex": search, "$options": "i"}}
        ]
    total = await db.contact_messages.count_documents(query)
    skip = (page - 1) * limit
    messages = await db.contact_messages.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    return {"messages": [ContactMessage(**msg) for msg in messages], "pagination": {"current_page": page, "total_pages": (total + limit - 1) // limit, "total_results": total}}

@api_router.delete("/contact-messages/{message_id}")
async def delete_contact_message(message_id: str, current_user: str = Depends(get_current_user)):
    result = await db.contact_messages.delete_one({"id": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Contact message deleted successfully"}

# Settings endpoints
@api_router.get("/settings")
async def get_settings(current_user: str = Depends(get_current_user)):
    settings = await db.settings.find_one()
    return Settings(**settings) if settings else Settings()

@api_router.put("/settings")
async def update_settings(
    # Basic Settings
    max_file_size: Optional[int] = Form(None),
    site_title: Optional[str] = Form(None),
    site_email: Optional[str] = Form(None),
    contact_cooldown: Optional[int] = Form(None),
    
    # Appearance
    background_type: Optional[str] = Form(None),
    background_value: Optional[str] = Form(None),
    background_image_url: Optional[str] = Form(None),
    
    # Theme Customization
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    accent_color: Optional[str] = Form(None),
    font_family: Optional[str] = Form(None),
    custom_css: Optional[str] = Form(None),
    
    # SEO Settings
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    google_analytics_id: Optional[str] = Form(None),
    google_search_console: Optional[str] = Form(None),
    robots_txt: Optional[str] = Form(None),
    
    # Social Media Links
    facebook_url: Optional[str] = Form(None),
    twitter_url: Optional[str] = Form(None),
    instagram_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    youtube_url: Optional[str] = Form(None),
    
    # Email Notification Settings
    smtp_server: Optional[str] = Form(None),
    smtp_port: Optional[int] = Form(None),
    smtp_username: Optional[str] = Form(None),
    smtp_password: Optional[str] = Form(None),
    smtp_use_tls: Optional[bool] = Form(None),
    notification_email: Optional[str] = Form(None),
    notify_on_contact: Optional[bool] = Form(None),
    notify_on_new_blog: Optional[bool] = Form(None),
    
    # Blog Settings
    posts_per_page: Optional[int] = Form(None),
    enable_comments: Optional[bool] = Form(None),
    auto_excerpt_length: Optional[int] = Form(None),
    default_author: Optional[str] = Form(None),
    
    current_user: str = Depends(get_current_user)
):
    update_data = {}
    
    # Only update fields that are provided
    if max_file_size is not None:
        update_data["max_file_size"] = max_file_size
    if site_title is not None:
        update_data["site_title"] = site_title
    if site_email is not None:
        update_data["site_email"] = site_email
    if contact_cooldown is not None:
        update_data["contact_cooldown"] = contact_cooldown
    if background_type is not None:
        update_data["background_type"] = background_type
    if background_value is not None:
        update_data["background_value"] = background_value
    if background_image_url is not None:
        update_data["background_image_url"] = background_image_url
    if primary_color is not None:
        update_data["primary_color"] = primary_color
    if secondary_color is not None:
        update_data["secondary_color"] = secondary_color
    if accent_color is not None:
        update_data["accent_color"] = accent_color
    if font_family is not None:
        update_data["font_family"] = font_family
    if custom_css is not None:
        update_data["custom_css"] = custom_css
    if meta_description is not None:
        update_data["meta_description"] = meta_description
    if meta_keywords is not None:
        update_data["meta_keywords"] = meta_keywords
    if google_analytics_id is not None:
        update_data["google_analytics_id"] = google_analytics_id
    if google_search_console is not None:
        update_data["google_search_console"] = google_search_console
    if robots_txt is not None:
        update_data["robots_txt"] = robots_txt
    if facebook_url is not None:
        update_data["facebook_url"] = facebook_url
    if twitter_url is not None:
        update_data["twitter_url"] = twitter_url
    if instagram_url is not None:
        update_data["instagram_url"] = instagram_url
    if linkedin_url is not None:
        update_data["linkedin_url"] = linkedin_url
    if github_url is not None:
        update_data["github_url"] = github_url
    if youtube_url is not None:
        update_data["youtube_url"] = youtube_url
    if smtp_server is not None:
        update_data["smtp_server"] = smtp_server
    if smtp_port is not None:
        update_data["smtp_port"] = smtp_port
    if smtp_username is not None:
        update_data["smtp_username"] = smtp_username
    if smtp_password is not None:
        update_data["smtp_password"] = smtp_password
    if smtp_use_tls is not None:
        update_data["smtp_use_tls"] = smtp_use_tls
    if notification_email is not None:
        update_data["notification_email"] = notification_email
    if notify_on_contact is not None:
        update_data["notify_on_contact"] = notify_on_contact
    if notify_on_new_blog is not None:
        update_data["notify_on_new_blog"] = notify_on_new_blog
    if posts_per_page is not None:
        update_data["posts_per_page"] = posts_per_page
    if enable_comments is not None:
        update_data["enable_comments"] = enable_comments
    if auto_excerpt_length is not None:
        update_data["auto_excerpt_length"] = auto_excerpt_length
    if default_author is not None:
        update_data["default_author"] = default_author
    
    await db.settings.update_one({}, {"$set": update_data}, upsert=True)
    return {"message": "Settings updated successfully"}

@api_router.get("/public-settings")
async def public_settings():
    s = await db.settings.find_one() or {}
    return {
        "site_title": s.get("site_title", Settings().site_title),
        "meta_description": s.get("meta_description", Settings().meta_description),
        "meta_keywords": s.get("meta_keywords", Settings().meta_keywords),
        "background_type": s.get("background_type", "default"),
        "background_value": s.get("background_value"),
        "background_image_url": s.get("background_image_url"),
        "primary_color": s.get("primary_color", Settings().primary_color),
        "secondary_color": s.get("secondary_color", Settings().secondary_color),
        "accent_color": s.get("accent_color", Settings().accent_color),
        "font_family": s.get("font_family", Settings().font_family),
        "custom_css": s.get("custom_css"),
        "google_analytics_id": s.get("google_analytics_id"),
        "facebook_url": s.get("facebook_url"),
        "twitter_url": s.get("twitter_url"),
        "instagram_url": s.get("instagram_url"),
        "linkedin_url": s.get("linkedin_url"),
        "github_url": s.get("github_url"),
        "youtube_url": s.get("youtube_url"),
        "posts_per_page": s.get("posts_per_page", Settings().posts_per_page),
        "enable_comments": s.get("enable_comments", Settings().enable_comments)
    }

@api_router.get("/robots.txt")
async def get_robots_txt():
    """Serve robots.txt dynamically from settings"""
    s = await db.settings.find_one() or {}
    robots_content = s.get("robots_txt", Settings().robots_txt)
    return {"content": robots_content}

@api_router.get("/sitemap.xml")
async def get_sitemap():
    """Generate dynamic sitemap"""
    base_url = "https://sectorfive.win"  # Should be configurable
    
    # Get all published blog posts
    posts = await db.blog_posts.find({"published": True}).sort("updated_at", -1).to_list(length=None)
    
    # Get all pages
    pages = await db.pages.find().to_list(length=None)
    
    urls = []
    
    # Add homepage
    urls.append({
        "loc": base_url,
        "lastmod": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "changefreq": "weekly",
        "priority": "1.0"
    })
    
    # Add blog posts
    for post in posts:
        urls.append({
            "loc": f"{base_url}/blog/{post['slug']}",
            "lastmod": post.get("updated_at", post.get("created_at")).strftime("%Y-%m-%d"),
            "changefreq": "monthly",
            "priority": "0.8"
        })
    
    # Add pages
    for page in pages:
        if not page.get("is_homepage"):
            urls.append({
                "loc": f"{base_url}/{page['slug']}",
                "lastmod": page.get("updated_at", page.get("created_at")).strftime("%Y-%m-%d"),
                "changefreq": "monthly",
                "priority": "0.6"
            })
    
    return {"urls": urls}

@app.on_event("startup")
async def startup_event():
    await initialize_data()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    try:
        # Check database connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)