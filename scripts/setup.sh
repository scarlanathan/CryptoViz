#!/bin/bash

# CRYPTO VIZ - Setup Script
# This script initializes the development environment

set -e

echo "🚀 Setting up CRYPTO VIZ Development Environment"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "Docker and Docker Compose are installed"
}

# Check if required files exist
check_files() {
    print_status "Checking required files..."

    if [ ! -f ".env.example" ]; then
        print_error ".env.example file not found"
        exit 1
    fi

    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml file not found"
        exit 1
    fi

    print_success "Required files found"
}

# Create .env file from example
setup_env() {
    print_status "Setting up environment variables..."

    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
        print_warning "Please edit .env file with your API keys and configuration"
    else
        print_warning ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p infrastructure/mongodb/init-scripts
    mkdir -p infrastructure/kafka/config
    mkdir -p shared/types
    mkdir -p shared/utils
    mkdir -p logs

    print_success "Directories created"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."

    print_status "Building data-collector service..."
    docker build -t crypto-viz/data-collector ./services/data-collector

    print_status "Building data-processor service..."
    docker build -t crypto-viz/data-processor ./services/data-processor

    print_status "Building api-backend service..."
    docker build -t crypto-viz/api-backend ./services/api-backend

    print_status "Building frontend service..."
    docker build -t crypto-viz/frontend ./services/frontend

    print_success "All Docker images built successfully"
}

# Start infrastructure services
start_infrastructure() {
    print_status "Starting infrastructure services..."

    docker-compose up -d zookeeper kafka mongodb redis

    print_status "Waiting for services to be ready..."
    sleep 30

    # Check if Kafka is ready
    print_status "Checking Kafka readiness..."
    timeout 60 bash -c 'until docker exec crypto-kafka kafka-topics --list --bootstrap-server localhost:9092; do sleep 2; done'

    print_success "Infrastructure services started"
}

# Initialize Kafka topics
init_kafka_topics() {
    print_status "Initializing Kafka topics..."

    docker-compose up kafka-init

    print_success "Kafka topics initialized"
}

# Start all services
start_services() {
    print_status "Starting all application services..."

    docker-compose up -d

    print_success "All services started"
}

# Show service status
show_status() {
    print_status "Service Status:"
    echo "==============="
    docker-compose ps

    echo ""
    print_status "Service URLs:"
    echo "============="
    echo "Frontend:         http://localhost:3000"
    echo "API Backend:      http://localhost:3002"
    echo "Data Collector:   http://localhost:8001"
    echo "Data Processor:   http://localhost:8002"
    echo "MongoDB:          mongodb://localhost:27017"
    echo "Redis:            redis://localhost:6379"
    echo "Kafka:            localhost:9092"
}

# Show logs
show_logs() {
    print_status "Recent logs:"
    echo "============"
    docker-compose logs --tail=50
}

# Main setup function
main() {
    print_status "Starting CRYPTO VIZ setup..."

    check_docker
    check_files
    setup_env
    create_directories

    # Ask user if they want to build images
    read -p "Do you want to build Docker images? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_images
    fi

    # Ask user if they want to start services
    read -p "Do you want to start all services? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_infrastructure
        init_kafka_topics
        start_services
        show_status

        echo ""
        print_success "🎉 CRYPTO VIZ setup completed successfully!"
        print_status "Access the dashboard at: http://localhost:3000"

        # Ask if user wants to see logs
        read -p "Do you want to see recent logs? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            show_logs
        fi
    fi

    echo ""
    print_status "Setup completed. Run 'docker-compose logs -f' to follow logs."
}

# Run main function
main "$@"