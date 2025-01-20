#!/bin/bash

# Crypto Anomaly Detection Engine System (CADES)
#
# Setup Script
# This script prepares the environment for CADES deployment
#
# Author: CADES
# Team License: Proprietary

# Exit on any error
set -e

# Print colorful messages
print_message() {
    echo -e "\033[1;34m>> $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m>> Error: $1\033[0m"
}

print_success() {
    echo -e "\033[1;32m>> Success: $1\033[0m"
}

# Check for required tools
print_message "Checking required tools..."

command -v docker >/dev/null 2>&1 || { 
    print_error "Docker is required but not installed. Visit https://docs.docker.com/get-docker/"
    exit 1
}

command -v docker-compose >/dev/null 2>&1 || {
    print_error "Docker Compose is required but not installed. Visit https://docs.docker.com/compose/install/"
    exit 1
}

command -v python3 >/dev/null 2>&1 || {
    print_error "Python 3 is required but not installed."
    exit 1
}

# Create necessary directories
print_message "Creating directory structure..."

directories=(
    "data/postgres"
    "data/redis"
    "data/prometheus"
    "data/grafana"
    "logs"
    "config/ssl"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    chmod 755 "$dir"
done

# Generate SSL certificates for development
if [ ! -f "config/ssl/dev.crt" ]; then
    print_message "Generating development SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout config/ssl/dev.key \
        -out config/ssl/dev.crt \
        -subj "/C=US/ST=State/L=City/O=CADE/CN=localhost"
fi

# Set up Python virtual environment
print_message "Setting up Python virtual environment..."

python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_message "Installing Python dependencies..."

pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
print_message "Initializing database..."

if [ -f ".env" ]; then
    source .env
else
    print_message "Creating .env file with default values..."
    cat > .env << EOF
POSTGRES_USER=cade
POSTGRES_PASSWORD=cade
POSTGRES_DB=cade
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_APP=src/api/app.py
EOF
fi

# Pull required Docker images
print_message "Pulling required Docker images..."

docker-compose pull

# Build local images
print_message "Building local Docker images..."

docker-compose build

# Create Docker networks if they don't exist
print_message "Setting up Docker networks..."

docker network create cade-network 2>/dev/null || true

# Initialize Git hooks
print_message "Setting up Git hooks..."

if [ -d ".git" ]; then
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
python3 -m black .
python3 -m flake8 .
python3 -m pytest tests/
EOF
    chmod +x .git/hooks/pre-commit
fi

# Final setup steps
print_message "Running final setup steps..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Set correct permissions
chmod -R 755 scripts/
chmod +x scripts/*.sh

print_success "Setup completed successfully!"
print_message "You can now start the application with: docker-compose up"