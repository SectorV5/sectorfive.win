#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

echo -e "${BLUE}Personal Website Template - Production Deployment${NC}"
echo "=================================================="
echo ""

# Check if .env.prod exists
if [ ! -f "$ROOT_DIR/.env.prod" ]; then
    echo -e "${RED}ERROR: .env.prod file not found!${NC}"
    echo "Please create .env.prod from .env.prod.example with your production settings."
    echo ""
    echo "Steps:"
    echo "1. cp .env.prod.example .env.prod"
    echo "2. Edit .env.prod with your domain and secure JWT secret"
    echo "3. Run this script again"
    exit 1
fi

# Load production environment variables
set -a
source "$ROOT_DIR/.env.prod"
set +a

# Validate required environment variables
if [ -z "${JWT_SECRET:-}" ]; then
    echo -e "${RED}ERROR: JWT_SECRET not set in .env.prod${NC}"
    exit 1
fi

if [ -z "${CORS_ORIGINS:-}" ]; then
    echo -e "${RED}ERROR: CORS_ORIGINS not set in .env.prod${NC}"
    exit 1
fi

echo -e "${YELLOW}Production Configuration:${NC}"
echo "  Domain: ${BASE_URL:-https://yourdomain.com}"
echo "  CORS Origins: ${CORS_ORIGINS}"
echo "  Backend URL: ${REACT_APP_BACKEND_URL}"
echo ""

# Confirm deployment
echo -e "${YELLOW}This will deploy the website in PRODUCTION mode.${NC}"
echo -e "${RED}Make sure you have:${NC}"
echo "  ✓ Configured Nginx reverse proxy"
echo "  ✓ Set up SSL certificates"
echo "  ✓ Configured firewall"
echo "  ✓ Set strong JWT_SECRET"
echo ""
read -p "Continue with production deployment? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

cd "$ROOT_DIR"

echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

echo -e "${YELLOW}Building production images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

echo -e "${YELLOW}Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 15

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"
if curl -f http://localhost:8001/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

if curl -f http://localhost:8080 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}✗ Frontend health check failed${NC}"
fi

echo ""
echo -e "${GREEN}Production deployment completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure Nginx reverse proxy to forward traffic to localhost:8080"
echo "2. Set up SSL certificates (Let's Encrypt recommended)"
echo "3. Configure firewall to allow only HTTP/HTTPS traffic"
echo "4. Test the website at your domain"
echo "5. Change default admin credentials (admin/admin)"
echo "6. Set up automated backups"
echo ""
echo -e "${YELLOW}Monitor logs with:${NC}"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo -e "${YELLOW}Stop services with:${NC}"
echo "  docker-compose -f docker-compose.prod.yml down"