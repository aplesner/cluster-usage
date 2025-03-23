#!/bin/bash

# Setup script for IO Usage Dashboard
# This script will:
# 1. Create the required directory structure
# 2. Set up the backend virtual environment
# 3. Initialize the database
# 4. Install frontend dependencies

# Root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$ROOT_DIR/data/logs/incoming"
mkdir -p "$ROOT_DIR/data/logs/archive"
mkdir -p "$ROOT_DIR/data/db"

# Create empty __init__.py files to make Python package imports work
echo "Creating Python package structure..."
touch "$ROOT_DIR/backend/__init__.py"
touch "$ROOT_DIR/backend/api/__init__.py"
touch "$ROOT_DIR/backend/database/__init__.py"
touch "$ROOT_DIR/backend/parsers/__init__.py"
touch "$ROOT_DIR/backend/utils/__init__.py"

# Set up backend
echo "Setting up backend..."
cd "$ROOT_DIR/backend"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Initialize database
cd "$ROOT_DIR"
python3 "$ROOT_DIR/backend/app.py" init

deactivate

# Set up frontend
echo "Setting up frontend..."
cd "$ROOT_DIR/frontend"

# Install npm dependencies if package.json exists
if [ -f "package.json" ]; then
    npm install
else
    echo "Warning: package.json not found in frontend directory"
fi

echo "Setup completed successfully!"
echo ""
echo "To start the backend server:"
echo "  cd $ROOT_DIR/backend"
echo "  source venv/bin/activate"
echo "  python app.py run"
echo ""
echo "To start the frontend development server:"
echo "  cd $ROOT_DIR/frontend"
echo "  npm start"