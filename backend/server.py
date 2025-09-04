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
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    must_change_password: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    max_file_size: int = 5368709120  # 5GB in bytes
    site_title: str = "Sectorfive Personal Website"
    site_email: str = "admin@sectorfive.win"
    contact_cooldown: int = 300  # 5 minutes in seconds
    # Appearance
    background_type: str = "default"  # default | color | gradient | image
    background_value: Optional[str] = None
    background_image_url: Optional[str] = None

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
    # Ensure an 'admin' user exists, regardless of old default user
    admin_user = await db.users.find_one({"username": "admin"})
    if not admin_user:
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("admin"),
            must_change_password=True
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
    return {
        "username": user["username"],
        "email": user.get("email"),
        "must_change_password": user.get("must_change_password", False),
        "created_at": user.get("created_at")
    }

@api_router.post("/change-password")
async def change_password(old_password: str = Form(...), new_password: str = Form(...), current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"username": current_user})
    if not user or not verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid old password")
    await db.users.update_one(
        {"username": current_user},
        {"$set": {"password_hash": hash_password(new_password), "must_change_password": False}}
    )
    return {"message": "Password updated successfully"}

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
async def get_blog_posts(request: Request):
    await track_visit(request, "/blog")
    posts = await db.blog_posts.find().sort("created_at", -1).to_list(length=None)
    return [BlogPost(**post) for post in posts]

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
    post = BlogPost(title=post_data.title, slug=post_data.slug, content=post_data.content)
    await db.blog_posts.insert_one(post.dict())
    return post

@api_router.put("/blog/{post_id}")
async def update_blog_post(post_id: str, post_data: BlogPostUpdate, current_user: str = Depends(get_current_user)):
    update_data = {
        "title": post_data.title,
        "content": post_data.content,
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
    max_file_size: int = Form(...),
    site_title: str = Form(...),
    site_email: str = Form(...),
    contact_cooldown: int = Form(...),
    background_type: Optional[str] = Form(None),
    background_value: Optional[str] = Form(None),
    background_image_url: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user)
):
    update_data = {
        "max_file_size": max_file_size,
        "site_title": site_title,
        "site_email": site_email,
        "contact_cooldown": contact_cooldown
    }
    if background_type is not None:
        update_data["background_type"] = background_type
    if background_value is not None:
        update_data["background_value"] = background_value
    if background_image_url is not None:
        update_data["background_image_url"] = background_image_url
    await db.settings.update_one({}, {"$set": update_data}, upsert=True)
    return {"message": "Settings updated successfully"}

@api_router.get("/public-settings")
async def public_settings():
    s = await db.settings.find_one() or {}
    return {
        "site_title": s.get("site_title", Settings().site_title),
        "background_type": s.get("background_type", "default"),
        "background_value": s.get("background_value"),
        "background_image_url": s.get("background_image_url"),
    }

@app.on_event("startup")
async def startup_event():
    await initialize_data()

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