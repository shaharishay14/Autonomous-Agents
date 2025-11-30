#!/bin/bash

# Deploy to EC2 script for KGen21

set -e  # Exit on error

# Configuration
EC2_HOST="13.62.63.125"
EC2_USER="ubuntu"
PEM_FILE="$HOME/Downloads/kgen.pem"
PROJECT_NAME="KGen21"
REMOTE_DIR="/home/ubuntu/$PROJECT_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

echo "🚀 Deploying KGen21 to EC2..."
echo "   Host: $EC2_HOST"
echo "   User: $EC2_USER"
echo ""

# Check if PEM file exists
if [ ! -f "$PEM_FILE" ]; then
    print_error "PEM file not found at $PEM_FILE"
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    print_error "backend/.env file not found!"
    echo "Please create it from backend/.env.example and add your credentials"
    exit 1
fi

# Build frontend if needed
if [ ! -d "frontend/dist" ]; then
    print_warning "Frontend build not found. Building now..."
    cd frontend
    npm install
    npm run build:prod
    cd ..
    print_success "Frontend built"
fi

# Step 1: Create directory on EC2
print_info "Creating project directory on EC2..."
ssh -i "$PEM_FILE" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR"
print_success "Directory created"

# Step 2: Upload project files
print_info "Uploading project files to EC2..."
echo "This may take a few minutes..."

# Create a temporary tar archive (excluding unnecessary files)
tar -czf /tmp/kgen21-deploy.tar.gz \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=.venv \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude="*.pyc" \
    --exclude=.DS_Store \
    backend \
    frontend/dist \
    nginx \
    docker-compose.yml \
    deploy.sh

# Upload the archive
scp -i "$PEM_FILE" /tmp/kgen21-deploy.tar.gz "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"
print_success "Files uploaded"

# Extract on server
ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" "cd $REMOTE_DIR && tar -xzf kgen21-deploy.tar.gz && rm kgen21-deploy.tar.gz"
print_success "Files extracted"

# Clean up local temp file
rm /tmp/kgen21-deploy.tar.gz

# Step 3: Install Docker on EC2 if not installed
print_info "Checking Docker installation on EC2..."
if ! ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" "which docker" > /dev/null 2>&1; then
    print_warning "Docker not found. Installing Docker..."
    ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
        # Update packages
        sudo apt-get update

        # Install Docker dependencies
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release

        # Add Docker's official GPG key
        sudo mkdir -m 0755 -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Set up the repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Add user to docker group
        sudo usermod -aG docker $USER

        # Start Docker
        sudo systemctl start docker
        sudo systemctl enable docker
ENDSSH
    print_success "Docker installed"

    # Need to reconnect for group changes to take effect
    print_warning "Docker group updated. Reconnecting..."
    sleep 2
else
    print_success "Docker is already installed"
fi

# Step 4: Build and run Docker containers
print_info "Building and starting Docker containers..."
ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" << ENDSSH
    cd $REMOTE_DIR

    # Stop any existing containers
    sudo docker compose down 2>/dev/null || true

    # Build images
    echo "Building Docker images..."
    sudo docker compose build

    # Start containers
    echo "Starting containers..."
    sudo docker compose up -d

    # Wait for services to be ready
    sleep 10

    # Run migrations
    echo "Running database migrations..."
    sudo docker compose exec -T backend python manage.py migrate --noinput

    # Collect static files
    echo "Collecting static files..."
    sudo docker compose exec -T backend python manage.py collectstatic --noinput

    # Show status
    echo ""
    echo "Container status:"
    sudo docker compose ps
ENDSSH

print_success "Docker containers are running"

# Step 5: Health check
print_info "Performing health checks..."
sleep 5

if curl -f "http://$EC2_HOST/health" > /dev/null 2>&1; then
    print_success "Nginx is healthy"
else
    print_warning "Nginx health check failed (might need more time to start)"
fi

if curl -f "http://$EC2_HOST/api/" > /dev/null 2>&1; then
    print_success "Django API is responding"
else
    print_warning "Django API not responding yet (might need more time)"
fi

# Step 6: Display information
echo ""
echo "========================================="
echo ""
print_success "🎉 Deployment complete!"
echo ""
echo "Access your application at:"
echo "  Frontend: http://$EC2_HOST/"
echo "  API:      http://$EC2_HOST/api/"
echo "  Admin:    http://$EC2_HOST/admin/"
echo ""
echo "Useful commands (run on EC2):"
echo "  SSH to EC2:       ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
echo "  View logs:        sudo docker compose logs -f"
echo "  Restart:          sudo docker compose restart"
echo "  Stop:             sudo docker compose down"
echo "  Enter backend:    sudo docker compose exec backend bash"
echo ""
echo "========================================="

# Optional: Open logs
read -p "Do you want to view the logs now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh -i "$PEM_FILE" "$EC2_USER@$EC2_HOST" "cd $REMOTE_DIR && sudo docker compose logs --tail=50"
fi