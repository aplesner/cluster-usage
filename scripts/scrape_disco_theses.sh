#!/bin/bash
# Script to scrape DISCO theses from the website

ROOT_DIR="/var/www/cluster-usage-dashboard"
cd $ROOT_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "$ROOT_DIR/backend/venv" ]; then
    echo "Creating virtual environment..."
    cd "$ROOT_DIR/backend" && python -m venv venv
    source "$ROOT_DIR/backend/venv/bin/activate"
    pip install -r "$ROOT_DIR/backend/requirements.txt"
else
    echo "Activating existing virtual environment..."
    source "$ROOT_DIR/backend/venv/bin/activate"
fi

python "$ROOT_DIR/backend/app.py" scrape_disco_website

deactivate
echo "Scraping completed."
