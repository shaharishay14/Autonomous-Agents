#!/bin/bash

# Deployment script for KGen21 with Docker

set -e  # Exit on error

echo "🚀 Starting deployment process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    print_error "backend/.env file not found!"
    echo "Please create it from backend/.env.example and add your credentials"
    exit 1
fi
print_success "Environment file found"

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    print_warning "Frontend build not found. Building now..."
    cd frontend
    npm install
    npm run build:prod
    cd ..
    print_success "Frontend built successfully"
else
    print_success "Frontend build found"
fi

# Build Docker images
echo ""
echo "📦 Building Docker images..."
docker compose build
print_success "Docker images built"

# Stop any existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker compose down
print_success "Existing containers stopped"

# Start new containers
echo ""
echo "🚀 Starting containers..."
docker compose up -d
print_success "Containers started"

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check container status
echo ""
echo "📊 Container status:"
docker compose ps

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
docker compose exec backend python manage.py migrate --noinput
print_success "Database migrations completed"

# Collect static files
echo ""
echo "📁 Collecting static files..."
docker compose exec backend python manage.py collectstatic --noinput
print_success "Static files collected"

# Show logs
echo ""
echo "📝 Recent logs:"
docker compose logs --tail=20

# Health check
echo ""
echo "🏥 Health check:"
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Nginx is healthy"
else
    print_error "Nginx health check failed"
fi

if curl -f http://localhost/api/ > /dev/null 2>&1; then
    print_success "Django API is responding"
else
    print_error "Django API is not responding"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access your application at:"
echo "  Frontend: http://localhost/"
echo "  API:      http://localhost/api/"
echo "  Admin:    http://localhost/admin/"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop containers:  docker compose down"
echo "  Restart:          docker compose restart"
echo "  Enter backend:    docker compose exec backend bash"