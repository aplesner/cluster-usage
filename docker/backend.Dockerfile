FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt /app/backend/

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Create necessary directories
RUN mkdir -p /app/data/logs/incoming /app/data/logs/archive /app/data/db

# Add script to initialize DB if it doesn't exist and start server
RUN echo '#!/bin/bash\n\
if [ ! -f "/app/data/db/io_usage.db" ]; then\n\
  echo "Initializing database..."\n\
  python /app/backend/app.py init\n\
fi\n\
\n\
python /app/backend/app.py run\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the working directory to the backend directory
WORKDIR /app/backend

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["/app/start.sh"]

