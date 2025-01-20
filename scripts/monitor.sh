#!/bin/bash

# Crypto Anomaly Detection Engine System (CADES)
#
# Monitoring Script
# This script provides system monitoring and health checking
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

print_warning() {
    echo -e "\033[1;33m>> Warning: $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m>> Error: $1\033[0m"
}

print_success() {
    echo -e "\033[1;32m>> Success: $1\033[0m"
}

# Check system resources
check_system_resources() {
    print_message "Checking system resources..."

    # CPU Usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
    if [ "$cpu_usage" -gt 80 ]; then
        print_warning "High CPU usage: ${cpu_usage}%"
    fi

    # Memory Usage
    memory_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | cut -d. -f1)
    if [ "$memory_usage" -gt 80 ]; then
        print_warning "High memory usage: ${memory_usage}%"
    fi

    # Disk Usage
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | cut -d% -f1)
    if [ "$disk_usage" -gt 80 ]; then
        print_warning "High disk usage: ${disk_usage}%"
    fi
}

# Check Docker containers
check_containers() {
    print_message "Checking Docker containers..."

    # List all containers
    containers=$(docker ps -a --format "{{.Names}}")

    for container in $containers; do
        status=$(docker inspect -f '{{.State.Status}}' "$container")
        if [ "$status" != "running" ]; then
            print_error "Container $container is not running (Status: $status)"
        else
            print_success "Container $container is running"
        fi
    done
}

# Check API endpoints
check_api_endpoints() {
    print_message "Checking API endpoints..."

    endpoints=(
        "health"
        "metrics"
        "status"
    )

    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/${endpoint}")
        if [ "$response" == "200" ]; then
            print_success "Endpoint /${endpoint} is healthy"
        else
            print_error "Endpoint /${endpoint} returned status ${response}"
        fi
    done
}

# Check logs for errors
check_logs() {
    print_message "Checking logs for errors..."

    error_count=$(grep -i "error" logs/cade.log | wc -l)
    if [ "$error_count" -gt 0 ]; then
        print_warning "Found ${error_count} errors in logs"
        grep -i "error" logs/cade.log | tail -n 5
    else
        print_success "No errors found in logs"
    fi
}

# Monitor database
check_database() {
    print_message "Checking database status..."

    if ! pg_isready -h localhost -p 5432; then
        print_error "Database is not responding"
    else
        print_success "Database is healthy"
        
        # Check connection count
        connections=$(psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT count(*) FROM pg_stat_activity;")
        if [ "$connections" -gt 80 ]; then
            print_warning "High number of database connections: ${connections}"
        fi
    fi
}

# Check Redis
check_redis() {
    print_message "Checking Redis status..."

    if ! redis-cli ping >/dev/null 2>&1; then
        print_error "Redis is not responding"
    else
        print_success "Redis is healthy"
        
        # Check memory usage
        used_memory=$(redis-cli info memory | grep "used_memory_human:" | cut -d: -f2)
        print_message "Redis memory usage: ${used_memory}"
    fi
}

# Main monitoring loop
monitor() {
    while true; do
        print_message "Starting monitoring cycle at $(date)"
        
        check_system_resources
        check_containers
        check_api_endpoints
        check_logs
        check_database
        check_redis
        
        print_message "Monitoring cycle completed at $(date)"
        print_message "Waiting for next cycle..."
        
        sleep "${MONITOR_INTERVAL:-300}"  # Default to 5 minutes if not set
    done
}

# Parse command line arguments
case "$1" in
    "start")
        monitor
        ;;
    "check")
        check_system_resources
        check_containers
        check_api_endpoints
        check_logs
        check_database
        check_redis
        ;;
    "logs")
        tail -f logs/cade.log
        ;;
    *)
        echo "Usage: $0 {start|check|logs}"
        exit 1
        ;;
esac