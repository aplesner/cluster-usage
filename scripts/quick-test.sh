#!/bin/bash

# Quick test script - just test the code without running servers
# Usage: ./scripts/quick-test.sh

set -e

echo "=== Testing Backend ==="
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python app.py init
echo "✅ Backend test passed"
deactivate
cd ..

echo ""
echo "=== Testing Frontend ==="
cd frontend
npm install --prefer-offline --no-audit
CI=false npm run build
echo "✅ Frontend build passed"
cd ..

echo ""
echo "✅ All tests passed! Ready for deployment."