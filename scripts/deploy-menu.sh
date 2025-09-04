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

# Logo and header
show_header() {
    clear
    echo -e "${BLUE}=================================="
    echo -e "   Personal Website Manager"
    echo -e "   Docker Deployment System"
    echo -e "==================================${NC}"
    echo ""
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed!${NC}"
        echo "Would you like to install Docker? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            install_docker
        else
            echo -e "${RED}Docker is required for deployment. Exiting.${NC}"
            exit 1
        fi
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed!${NC}"
        echo "Installing Docker Compose..."
        install_docker_compose
    fi
}

# Install Docker (Ubuntu/Debian)
install_docker() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    
    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Update package index
    sudo apt-get update
    
    # Install dependencies
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository  
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Docker installed successfully!${NC}"
    echo -e "${YELLOW}Please log out and log back in for group changes to take effect.${NC}"
    echo "Press any key to continue..."
    read -n 1
}

# Install Docker Compose
install_docker_compose() {
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
}

# Deploy the application
deploy_app() {
    echo -e "${YELLOW}Deploying Personal Website...${NC}"
    cd "$ROOT_DIR"
    
    # Build and start containers
    docker-compose down --remove-orphans 2>/dev/null || true
    docker-compose build --no-cache
    docker-compose up -d
    
    echo -e "${GREEN}Deployment completed!${NC}"
    echo ""
    echo -e "${BLUE}Your website is now available at:${NC}"
    echo -e "${GREEN}  Frontend: http://localhost:8080${NC}"
    echo -e "${GREEN}  Backend API: http://localhost:8001${NC}"
    echo -e "${GREEN}  MongoDB: localhost:27017${NC}"
    echo ""
    echo -e "${YELLOW}Default admin credentials:${NC}"
    echo -e "  Username: admin"
    echo -e "  Password: admin"
    echo -e "  ${RED}(You will be asked to change these on first login)${NC}"
    echo ""
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Check service status
    if curl -f http://localhost:8001/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running${NC}"
    else
        echo -e "${RED}✗ Backend may not be ready yet${NC}"
    fi
    
    if curl -f http://localhost:8080 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
    else
        echo -e "${RED}✗ Frontend may not be ready yet${NC}"
    fi
}

# Stop and remove all containers
stop_app() {
    echo -e "${YELLOW}Stopping Personal Website...${NC}"
    cd "$ROOT_DIR"
    docker-compose down --remove-orphans
    echo -e "${GREEN}Application stopped successfully!${NC}"
}

# Complete cleanup (removes containers, images, and volumes)
cleanup_app() {
    echo -e "${RED}WARNING: This will remove all data including uploaded files and database!${NC}"
    echo "Are you sure you want to proceed? Type 'DELETE' to confirm:"
    read -r confirmation
    
    if [[ "$confirmation" == "DELETE" ]]; then
        echo -e "${YELLOW}Performing complete cleanup...${NC}"
        cd "$ROOT_DIR"
        
        # Stop containers
        docker-compose down --remove-orphans
        
        # Remove images
        docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
        
        # Remove dangling images
        docker image prune -f
        
        echo -e "${GREEN}Complete cleanup finished!${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled.${NC}"
    fi
}

# Show logs
show_logs() {
    echo -e "${YELLOW}Select service to view logs:${NC}"
    echo "1. All services"
    echo "2. Frontend"
    echo "3. Backend" 
    echo "4. MongoDB"
    echo "5. Back to main menu"
    echo ""
    read -p "Enter your choice [1-5]: " choice
    
    cd "$ROOT_DIR"
    case $choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f frontend ;;
        3) docker-compose logs -f backend ;;
        4) docker-compose logs -f mongo ;;
        5) return ;;
        *) echo -e "${RED}Invalid option${NC}"; sleep 2 ;;
    esac
}

# Backup data
backup_data() {
    echo -e "${YELLOW}Creating backup...${NC}"
    
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="$ROOT_DIR/backups/backup_$BACKUP_DATE"
    mkdir -p "$BACKUP_DIR"
    
    cd "$ROOT_DIR"
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${RED}Containers are not running. Please start the application first.${NC}"
        return 1
    fi
    
    # Backup MongoDB
    echo -e "${YELLOW}Backing up database...${NC}"
    docker-compose exec -T mongo mongodump --db sectorfive_db --archive > "$BACKUP_DIR/database.archive"
    
    # Backup uploaded files
    echo -e "${YELLOW}Backing up uploaded files...${NC}"
    cp -r backend/uploads "$BACKUP_DIR/" 2>/dev/null || echo "No uploads directory found"
    
    # Create backup info
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
Sectorfive Website Backup
Created: $(date)
Database: sectorfive_db
Files: backend/uploads/
EOF
    
    echo -e "${GREEN}Backup created successfully at: $BACKUP_DIR${NC}"
    echo "Press any key to continue..."
    read -n 1
}

# Restore data
restore_data() {
    echo -e "${YELLOW}Available backups:${NC}"
    
    if [ -d "$ROOT_DIR/backups" ]; then
        ls -la "$ROOT_DIR/backups/"
        echo ""
        echo "Enter backup directory name (e.g., backup_20240101_120000):"
        read -r backup_name
        
        BACKUP_PATH="$ROOT_DIR/backups/$backup_name"
        
        if [ -d "$BACKUP_PATH" ]; then
            echo -e "${RED}WARNING: This will overwrite existing data!${NC}"
            echo "Are you sure? (y/n)"
            read -r confirm
            
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                cd "$ROOT_DIR"
                
                # Restore database
                if [ -f "$BACKUP_PATH/database.archive" ]; then
                    echo -e "${YELLOW}Restoring database...${NC}"
                    docker-compose exec -T mongo mongorestore --db sectorfive_db --archive < "$BACKUP_PATH/database.archive"
                fi
                
                # Restore files
                if [ -d "$BACKUP_PATH/uploads" ]; then
                    echo -e "${YELLOW}Restoring uploaded files...${NC}"
                    rm -rf backend/uploads 2>/dev/null || true
                    cp -r "$BACKUP_PATH/uploads" backend/
                fi
                
                echo -e "${GREEN}Restore completed successfully!${NC}"
            else
                echo -e "${YELLOW}Restore cancelled.${NC}"
            fi
        else
            echo -e "${RED}Backup directory not found!${NC}"
        fi
    else
        echo -e "${RED}No backups found!${NC}"
    fi
    
    echo "Press any key to continue..."
    read -n 1
}

# Update application
update_app() {
    echo -e "${YELLOW}Updating Sectorfive Website...${NC}"
    cd "$ROOT_DIR"
    
    # Pull latest changes if in git repo
    if [ -d ".git" ]; then
        echo -e "${YELLOW}Pulling latest code...${NC}"
        git pull
    fi
    
    # Rebuild and restart
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    echo -e "${GREEN}Update completed!${NC}"
    echo "Press any key to continue..."
    read -n 1
}

# Main menu
show_menu() {
    show_header
    echo -e "${GREEN}What would you like to do?${NC}"
    echo ""
    echo "  1. Install Docker & Dependencies"
    echo "  2. Deploy/Start Website"
    echo "  3. Stop Website"
    echo "  4. View Logs"
    echo "  5. Backup Data"
    echo "  6. Restore Data"
    echo "  7. Update Application"
    echo "  8. Complete Cleanup (DANGER)"
    echo "  9. Exit"
    echo ""
    read -p "Enter your choice [1-9]: " choice
    
    case $choice in
        1) check_docker; install_docker ;;
        2) check_docker; deploy_app ;;
        3) stop_app ;;
        4) show_logs ;;
        5) backup_data ;;
        6) restore_data ;;
        7) update_app ;;
        8) cleanup_app ;;
        9) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option. Please try again.${NC}"; sleep 2 ;;
    esac
}

# Main loop
main() {
    while true; do
        show_menu
        echo ""
        echo "Press any key to continue..."
        read -n 1
    done
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}" 
   exit 1
fi

# Start the application
main