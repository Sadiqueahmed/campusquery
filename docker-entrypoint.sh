#!/bin/sh
set -e

# Seed database if not present
if [ ! -f "/app/backend/student_data.db" ]; then
    echo "Initializing student database..."
    cd /app/backend && python seed.py
fi

cd /app/backend
echo "Starting CampusQuery server on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
