#!/bin/bash

# This is a simple build script for the OpenReferral Fullstack application.

echo "Starting build process..."
echo "--------------------------------"

# --- Backend Build ---
echo "[Backend] Building Docker image for the backend..."
# The Docker image will be tagged as 'openserver_fullstack_backend'
# This command assumes Docker is available in the environment.
docker build -t openserver_fullstack_backend ./backend

if [ $? -eq 0 ]; then
    echo "[Backend] Docker image 'openserver_fullstack_backend' built successfully."
else
    echo "[Backend] Docker image build FAILED."
    exit 1
fi
echo "--------------------------------"

# --- Frontend Preparation ---
# For the current simple frontend (static HTML, CSS, JS), no complex build step is needed.
# Assets are directly usable from the /frontend directory.
echo "[Frontend] Frontend assets are static and located in the /frontend directory."
echo "[Frontend] For deployment, these files would typically be served by a web server (e.g., Nginx, Caddy, or FastAPI static files)."
echo "--------------------------------"

# --- Packaging for Deployment (Conceptual) ---
# This section describes how one might package the application for deployment.
# Actual implementation would depend on the deployment target.
echo "[Deployment] Conceptual packaging steps:"
echo "  1. Create a 'dist' or 'deploy' directory."
echo "     mkdir -p dist"
echo "  2. Copy essential files for running the application:"
echo "     cp docker-compose.yml ./dist/"
echo "     cp -R backend ./dist/  (or just the built Docker image reference)"
echo "     cp -R frontend ./dist/"
echo "     cp .env ./dist/ (ensure sensitive data is handled appropriately)"
echo "  3. The 'dist' directory would then be deployed to the server."
echo "     (Note: For Docker-centric deployments, pushing the image to a registry and using docker-compose on the server is common)."
echo "--------------------------------"

echo "Build script finished."
echo "To run the application locally (after Docker image build): docker-compose up"
echo "Ensure the .env file is configured if not using docker-compose defaults for DATABASE_URL directly in app/database.py for non-Docker runs."
