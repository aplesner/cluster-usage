#!/bin/bash

# Deployment script for cluster-usage dashboard
# This script sets up the project on the university VM

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/var/www/cluster-usage-dashboard"
BACKUP_DIR="/var/backups/cluster-usage"
LOG_FILE="/var/log/cluster-usage-deploy.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to backup current data
backup_data() {
    if [ -d "$PROJECT_DIR/data" ]; then
        log "Backing up current data..."
        sudo mkdir -p "$BACKUP_DIR"
        sudo cp -r "$PROJECT_DIR/data" "$BACKUP_DIR/data-$(date +%Y%m%d-%H%M%S)"
        log "Data backup completed"
    fi
}

# Function to setup project directory
setup_project() {
    log "Setting up project directory..."
    
    # Create project directory if it doesn't exist
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR"
    
    # Clone repository if not exists, otherwise pull latest
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        log "Cloning repository..."
        git clone https://gitlab.ethz.ch/disco/social/cluster-usage-dashboard.git "$PROJECT_DIR"
    else
        log "Updating repository..."
        cd "$PROJECT_DIR"
        git fetch origin main
        git reset --hard origin/main
    fi
    
    cd "$PROJECT_DIR"
}

# Function to setup data directories
setup_data_dirs() {
    log "Setting up data directories..."
    mkdir -p data/logs/incoming
    mkdir -p data/logs/archive
    mkdir -p data/db
    
    # Set proper permissions
    chmod 755 data
    chmod 755 data/logs
    chmod 755 data/logs/incoming
    chmod 755 data/logs/archive
    chmod 755 data/db
}

# Function to setup Docker
setup_docker() {
    log "Setting up Docker..."
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml down || true
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Check if services are running
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log "Services are running successfully"
    else
        log "ERROR: Services failed to start"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# Function to setup systemd service for auto-restart
setup_systemd() {
    log "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/cluster-usage.service > /dev/null <<EOF
[Unit]
Description=Cluster Usage Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable cluster-usage.service
    log "Systemd service configured"
}

# Function to setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/cluster-usage > /dev/null <<EOF
$LOG_FILE {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}

$PROJECT_DIR/data/logs/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
    
    log "Log rotation configured"
}

# Main deployment function
main() {
    log "Starting deployment of cluster-usage dashboard..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log "ERROR: Do not run this script as root"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log "ERROR: Docker is not installed"
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log "ERROR: docker-compose is not installed"
        exit 1
    fi
    
    backup_data
    setup_project
    setup_data_dirs
    setup_docker
    setup_systemd
    setup_logrotate
    
    log "Deployment completed successfully!"
    log "Dashboard should be available at http://ee-tik-vm057.ethz.ch"
    
    # Show final status
    log "Service status:"
    docker-compose -f docker-compose.prod.yml ps
}

# Run main function
main "$@"
