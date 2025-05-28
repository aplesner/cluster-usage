#!/bin/bash

# Local deployment script for testing
# Usage: ./scripts/local-deploy.sh

set -e

# Configuration - update these with your values
VM_HOST="ee-tik-vm057.ethz.ch"
VM_USER="aplesner"  # Replace with your username
SSH_KEY="$HOME/.ssh/gitlab_ci_cluster_usage"  # Path to your SSH key

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    error "SSH key not found at $SSH_KEY"
    echo "Generate it with: ssh-keygen -t ed25519 -f $SSH_KEY"
    exit 1
fi

# Test SSH connection
log "Testing SSH connection..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$VM_USER@$VM_HOST" "echo 'Connection successful'"; then
    log "SSH connection successful"
else
    error "SSH connection failed"
    exit 1
fi

# Push current changes to git first
log "Pushing current changes to GitLab..."
git add .
git commit -m "Local deployment test - $(date)" || warn "Nothing to commit"
git push origin main

# Deploy to VM
log "Starting deployment to $VM_HOST..."

ssh -i "$SSH_KEY" "$VM_USER@$VM_HOST" << 'EOF'
set -e

echo "=== Deployment started ===" 
cd /var/www/cluster-usage-dashboard || exit 1
echo "Working directory: $(pwd)"

echo "=== Checking Docker status ===" 
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not accessible. Checking status..."
    sudo systemctl status docker || true
    echo "Starting Docker service..."
    sudo systemctl start docker
    sleep 5
    
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker still not accessible. Please check Docker installation."
        exit 1
    fi
fi
echo "✅ Docker is running"

echo "=== Pulling latest code ===" 
git fetch origin main
git reset --hard origin/main
echo "Code updated to: $(git rev-parse --short HEAD)"

echo "=== Stopping existing containers ===" 
docker-compose -f docker-compose.prod.yml down || true

echo "=== Cleaning up old containers and images ===" 
docker container prune -f || true
docker image prune -f || true

echo "=== Building and starting containers ===" 
docker-compose -f docker-compose.prod.yml up --build -d

echo "=== Waiting for containers to start ===" 
sleep 15

echo "=== Container status ===" 
docker-compose -f docker-compose.prod.yml ps

echo "=== Container logs (last 20 lines) ===" 
docker-compose -f docker-compose.prod.yml logs --tail=20

echo "=== Checking if services are responding ===" 
sleep 5

# Check backend
if curl -f -m 10 http://localhost:5000/api/stats > /dev/null 2>&1; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding"
    echo "Backend logs:"
    docker-compose -f docker-compose.prod.yml logs backend --tail=10
fi

# Check frontend
if curl -f -m 10 http://localhost/ > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend is not responding"
    echo "Frontend logs:"
    docker-compose -f docker-compose.prod.yml logs frontend --tail=10
fi

echo "=== Deployment completed ===" 
echo "Dashboard should be available at: http://ee-tik-vm057.ethz.ch"
EOF

log "Deployment completed! Check http://ee-tik-vm057.ethz.ch"