#!/bin/bash

# Docker helper script for IO Usage Dashboard
# Usage: ./docker-run.sh [command]

# Set the docker-compose file path
DOCKER_COMPOSE_FILE="docker/docker-compose.yml"

# Default command is 'help'
COMMAND=${1:-help}

case $COMMAND in
  start)
    echo "Starting containers..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    echo "Containers started. Web UI available at http://localhost"
    ;;
    
  stop)
    echo "Stopping containers..."
    docker-compose -f $DOCKER_COMPOSE_FILE down
    echo "Containers stopped."
    ;;
    
  restart)
    echo "Restarting containers..."
    docker-compose -f $DOCKER_COMPOSE_FILE down
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    echo "Containers restarted. Web UI available at http://localhost"
    ;;
    
  logs)
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose -f $DOCKER_COMPOSE_FILE logs -f
    ;;
    
  logs-backend)
    echo "Showing backend logs (Ctrl+C to exit)..."
    docker-compose -f $DOCKER_COMPOSE_FILE logs -f backend
    ;;
    
  logs-frontend)
    echo "Showing frontend logs (Ctrl+C to exit)..."
    docker-compose -f $DOCKER_COMPOSE_FILE logs -f frontend
    ;;
    
  rebuild)
    echo "Rebuilding containers..."
    docker-compose -f $DOCKER_COMPOSE_FILE up --build -d
    echo "Containers rebuilt and started. Web UI available at http://localhost"
    ;;
    
  process-logs)
    echo "Processing log files in data/logs/incoming..."
    CONTAINER_ID=$(docker-compose -f $DOCKER_COMPOSE_FILE ps -q backend)
    docker exec -it $CONTAINER_ID python /app/backend/app.py process_logs --archive
    echo "Log processing complete."
    ;;
    
  init-db)
    echo "Initializing database..."
    CONTAINER_ID=$(docker-compose -f $DOCKER_COMPOSE_FILE ps -q backend)
    docker exec -it $CONTAINER_ID python /app/backend/app.py init
    echo "Database initialization complete."
    ;;
    
  status)
    echo "Container status:"
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    ;;
    
  help|*)
    echo "IO Usage Dashboard Docker Helper"
    echo "--------------------------------"
    echo "Usage: ./docker-run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start containers"
    echo "  stop          Stop containers"
    echo "  restart       Restart containers"
    echo "  logs          Show logs from all containers"
    echo "  logs-backend  Show logs from backend container"
    echo "  logs-frontend Show logs from frontend container"
    echo "  rebuild       Rebuild and start containers"
    echo "  process-logs  Process log files in the incoming directory"
    echo "  init-db       Initialize the database"
    echo "  status        Show container status"
    echo "  help          Show this help message"
    ;;
esac
