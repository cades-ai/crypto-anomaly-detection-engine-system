#!/bin/bash

# Crypto Anomaly Detection Engine System (CADES)
#
# Deployment Script
# This script handles the deployment process for CADES
#
# Author: CADES
# Team License: Proprietary

# Exit on any error
set -e

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

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

# Check deployment environment
if [ -z "$DEPLOYMENT_ENV" ]; then
    print_error "DEPLOYMENT_ENV not set. Use 'staging' or 'production'"
    exit 1
fi

# Verify AWS credentials
print_message "Verifying AWS credentials..."
if ! aws sts get-caller-identity &>/dev/null; then
    print_error "AWS credentials not configured properly"
    exit 1
fi

# Update EKS kubeconfig
print_message "Updating kubeconfig for EKS cluster..."
aws eks update-kubeconfig --name "cade-${DEPLOYMENT_ENV}-cluster" --region ${AWS_REGION}

# Check if kubectl is properly configured
if ! kubectl get nodes &>/dev/null; then
    print_error "kubectl not properly configured"
    exit 1
fi

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    print_message "Waiting for deployment ${deployment} to be ready..."
    kubectl rollout status deployment/${deployment} -n ${namespace} --timeout=300s
}

# Deploy to environment
deploy() {
    local env=$1
    print_message "Starting deployment to ${env} environment..."

    # Update Docker images
    print_message "Building and pushing Docker images..."
    docker-compose -f docker-compose.${env}.yml build
    docker-compose -f docker-compose.${env}.yml push

    # Apply Kubernetes configurations
    print_message "Applying Kubernetes configurations..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace cade-${env} --dry-run=client -o yaml | kubectl apply -f -

    # Apply secrets
    kubectl apply -f k8s/${env}/secrets.yml -n cade-${env}

    # Apply configurations
    kubectl apply -f k8s/${env}/configmap.yml -n cade-${env}

    # Deploy database migrations
    print_message "Running database migrations..."
    kubectl apply -f k8s/${env}/jobs/migrations.yml -n cade-${env}
    kubectl wait --for=condition=complete job/db-migrations -n cade-${env} --timeout=300s

    # Deploy main components
    components=(
        "api"
        "worker"
        "redis"
        "prometheus"
        "grafana"
    )

    for component in "${components[@]}"; do
        print_message "Deploying ${component}..."
        kubectl apply -f k8s/${env}/${component}.yml -n cade-${env}
        wait_for_deployment ${component} cade-${env}
    done

    # Verify deployment
    print_message "Verifying deployment..."
    kubectl get pods -n cade-${env}

    # Run smoke tests
    print_message "Running smoke tests..."
    python -m pytest tests/smoke/

    print_success "Deployment to ${env} completed successfully!"
}

# Start deployment process
case $DEPLOYMENT_ENV in
    "staging")
        deploy "staging"
        ;;
    "production")
        # Additional safety checks for production
        print_message "Production deployment selected. Performing additional checks..."
        
        # Check if staging deployment is healthy
        if ! curl -s https://staging.cades.io/health | grep -q "ok"; then
            print_error "Staging environment health check failed"
            exit 1
        fi

        # Verify all tests pass
        print_message "Running full test suite..."
        if ! python -m pytest tests/; then
            print_error "Test suite failed"
            exit 1
        fi

        # Prompt for confirmation
        read -p "Are you sure you want to deploy to production? (yes/no) " answer
        if [ "$answer" != "yes" ]; then
            print_message "Deployment cancelled"
            exit 0
        fi

        deploy "production"
        ;;
    *)
        print_error "Invalid environment: ${DEPLOYMENT_ENV}"
        exit 1
        ;;
esac