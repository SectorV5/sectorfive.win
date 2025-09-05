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

# Helper function to use correct docker compose command
docker_compose_cmd() {
    if docker compose version &> /dev/null 2>&1; then
        docker compose "$@"
    elif command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        echo -e "${RED}Error: Neither 'docker compose' nor 'docker-compose' is available!${NC}"
        exit 1
    fi
}

# Function to hash password using Python's bcrypt
hash_password() {
    local password="$1"
    python3 -c "
import bcrypt
import sys
password = sys.argv[1]
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
" "$password"
}

# Function to change admin credentials
change_credentials() {
    echo -e "${BLUE}=== Admin Credentials Manager ===${NC}"
    echo ""
    
    # Check if containers are running
    cd "$ROOT_DIR"
    if ! docker_compose_cmd ps | grep -q "Up"; then
        echo -e "${RED}Error: Docker containers are not running!${NC}"
        echo "Please start the application first with:"
        echo "  ./scripts/deploy-menu.sh"
        echo "  Choose option 2: Deploy/Start Website"
        exit 1
    fi
    
    echo -e "${YELLOW}Current admin user information:${NC}"
    # Get current admin info
    docker_compose_cmd exec -T mongo mongosh personal_website_db --eval "
        db.users.findOne({username: 'admin'}, {username: 1, email: 1, must_change_password: 1})
    " --quiet || {
        echo -e "${RED}Error: Could not connect to database${NC}"
        exit 1
    }
    echo ""
    
    # Get new username
    echo -e "${GREEN}Enter new admin username:${NC}"
    read -r new_username
    if [ -z "$new_username" ]; then
        echo -e "${RED}Username cannot be empty${NC}"
        exit 1
    fi
    
    # Get new password
    echo -e "${GREEN}Enter new admin password:${NC}"
    read -s new_password
    echo ""
    if [ -z "$new_password" ]; then
        echo -e "${RED}Password cannot be empty${NC}"
        exit 1
    fi
    
    # Confirm password
    echo -e "${GREEN}Confirm new admin password:${NC}"
    read -s confirm_password
    echo ""
    if [ "$new_password" != "$confirm_password" ]; then
        echo -e "${RED}Passwords do not match${NC}"
        exit 1
    fi
    
    # Get new email
    echo -e "${GREEN}Enter new admin email:${NC}"
    read -r new_email
    if [ -z "$new_email" ]; then
        echo -e "${RED}Email cannot be empty${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}You are about to change admin credentials to:${NC}"
    echo "  Username: $new_username"
    echo "  Email: $new_email"
    echo "  Password: [hidden]"
    echo ""
    read -p "Are you sure? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
    fi
    
    # Hash the password
    echo -e "${YELLOW}Hashing password...${NC}"
    hashed_password=$(hash_password "$new_password")
    
    # Update the database
    echo -e "${YELLOW}Updating database...${NC}"
    docker_compose_cmd exec -T mongo mongosh personal_website_db --eval "
        db.users.updateOne(
            {username: 'admin'}, 
            {\$set: {
                username: '$new_username',
                email: '$new_email', 
                password_hash: '$hashed_password',
                must_change_password: false,
                updated_at: new Date()
            }}
        )
    " --quiet || {
        echo -e "${RED}Error: Failed to update credentials${NC}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✅ Admin credentials updated successfully!${NC}"
    echo ""
    echo -e "${YELLOW}New login details:${NC}"
    echo "  Username: $new_username"
    echo "  Email: $new_email"
    echo ""
    echo -e "${BLUE}You can now login to the admin panel with your new credentials.${NC}"
}

# Function to reset to default credentials
reset_to_default() {
    echo -e "${BLUE}=== Reset to Default Credentials ===${NC}"
    echo ""
    echo -e "${RED}WARNING: This will reset admin credentials to:${NC}"
    echo "  Username: admin"
    echo "  Password: admin"
    echo "  Email: admin@example.com"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
    fi
    
    # Check if containers are running
    cd "$ROOT_DIR"
    if ! docker_compose_cmd ps | grep -q "Up"; then
        echo -e "${RED}Error: Docker containers are not running!${NC}"
        echo "Please start the application first."
        exit 1
    fi
    
    # Hash default password
    echo -e "${YELLOW}Preparing default credentials...${NC}"
    default_hash=$(hash_password "admin")
    
    # Update the database
    echo -e "${YELLOW}Resetting database...${NC}"
    docker_compose_cmd exec -T mongo mongosh personal_website_db --eval "
        db.users.updateOne(
            {}, 
            {\$set: {
                username: 'admin',
                email: 'admin@example.com',
                password_hash: '$default_hash',
                must_change_password: true,
                updated_at: new Date()
            }},
            {upsert: true}
        )
    " --quiet || {
        echo -e "${RED}Error: Failed to reset credentials${NC}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✅ Credentials reset to default successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Default login details:${NC}"
    echo "  Username: admin"
    echo "  Password: admin"
    echo "  Email: admin@example.com"
    echo ""
    echo -e "${BLUE}You will be required to change these on first login.${NC}"
}

# Function to show current admin info
show_info() {
    echo -e "${BLUE}=== Current Admin Information ===${NC}"
    echo ""
    
    # Check if containers are running
    cd "$ROOT_DIR"
    if ! docker_compose_cmd ps | grep -q "Up"; then
        echo -e "${RED}Error: Docker containers are not running!${NC}"
        echo "Please start the application first."
        exit 1
    fi
    
    # Get admin info
    echo -e "${YELLOW}Admin user details:${NC}"
    docker_compose_cmd exec -T mongo mongosh personal_website_db --eval "
        const user = db.users.findOne({}, {password_hash: 0});
        if (user) {
            print('Username: ' + user.username);
            print('Email: ' + user.email);
            print('Must change password: ' + user.must_change_password);
            print('Created: ' + user.created_at);
            print('Updated: ' + (user.updated_at || 'Never'));
            print('Role: ' + (user.role || 'admin'));
        } else {
            print('No admin user found');
        }
    " --quiet || {
        echo -e "${RED}Error: Could not connect to database${NC}"
        exit 1
    }
}

# Main menu
show_menu() {
    clear
    echo -e "${BLUE}=================================="
    echo -e "   Admin Credentials Manager"
    echo -e "   Personal Website Template"
    echo -e "==================================${NC}"
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "  1. Change admin credentials"
    echo "  2. Reset to default (admin/admin)"
    echo "  3. Show current admin info"
    echo "  4. Exit"
    echo ""
}

# Main script
main() {
    # Check dependencies
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        exit 1
    fi
    
    if ! python3 -c "import bcrypt" &> /dev/null; then
        echo -e "${RED}Error: Python bcrypt library is required${NC}"
        echo "Install it with: pip3 install bcrypt"
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "Enter your choice [1-4]: " choice
        case $choice in
            1)
                change_credentials
                echo ""
                read -p "Press any key to continue..." -n 1 -r
                ;;
            2)
                reset_to_default
                echo ""
                read -p "Press any key to continue..." -n 1 -r
                ;;
            3)
                show_info
                echo ""
                read -p "Press any key to continue..." -n 1 -r
                ;;
            4)
                echo -e "${YELLOW}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Run main function
main