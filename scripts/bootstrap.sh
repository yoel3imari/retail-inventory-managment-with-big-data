#!/bin/bash

# Retail Inventory Management - Bootstrap Script
# This script initializes all services and creates necessary configurations

set -e

echo "🏪 Retail Inventory Management - Bootstrap Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install it and try again."
        exit 1
    fi
    print_status "Docker Compose is available"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p models/trained
    mkdir -p models/registry
    mkdir -p models/pipelines
    
    # Create log files
    touch logs/retail_inventory.log
    touch logs/kafka.log
    touch logs/spark.log
    touch logs/airflow.log
    
    print_status "Directories created successfully"
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    cat > .env << EOF
# Retail Inventory Management Environment Variables

# Application
DEBUG=true
APP_NAME=retail-inventory-management
APP_VERSION=1.0.0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CLIENT_ID=retail-inventory

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# ClickHouse
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=clickhouse
CLICKHOUSE_DATABASE=retail

# Spark
SPARK_MASTER=spark://spark-master:7077

# Data Generation
STORE_COUNT=10
PRODUCT_COUNT=1000

# ML Configuration
ML_MODEL_VERSION=v1
FORECAST_HORIZON_DAYS=7

# Monitoring
PROMETHEUS_PORT=8000
EOF

    print_status "Environment file created"
}

# Create MinIO buckets
create_minio_buckets() {
    print_status "Creating MinIO buckets..."
    
    # Wait for MinIO to be ready (using health check)
    local max_attempts=30
    local attempt=1
    
    until curl -s http://localhost:9001/minio/health/live > /dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "MinIO failed to become ready after $max_attempts attempts"
            exit 1
        fi
        print_warning "Waiting for MinIO to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    # Additional wait to ensure MinIO is fully initialized
    sleep 10
    
    # Create buckets using MinIO client inside the container
    docker exec minio mc mb --ignore-existing minio/retail-raw-data
    docker exec minio mc mb --ignore-existing minio/retail-processed-data
    docker exec minio mc mb --ignore-existing minio/retail-models
    docker exec minio mc mb --ignore-existing minio/retail-features
    
    print_status "MinIO buckets created"
}

# Create Kafka topics
create_kafka_topics() {
    print_status "Creating Kafka topics..."
    
    # Wait for Kafka to be ready (using health check)
    local max_attempts=30
    local attempt=1
    
    until docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "Kafka failed to become ready after $max_attempts attempts"
            exit 1
        fi
        print_warning "Waiting for Kafka to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    # Additional wait to ensure Kafka is fully initialized
    sleep 10
    
    # Create topics
    docker exec kafka kafka-topics --create \
        --topic retail-sales-transactions \
        --bootstrap-server localhost:9092 \
        --partitions 3 --replication-factor 1
    
    docker exec kafka kafka-topics --create \
        --topic retail-inventory-updates \
        --bootstrap-server localhost:9092 \
        --partitions 3 --replication-factor 1
    
    docker exec kafka kafka-topics --create \
        --topic retail-restock-alerts \
        --bootstrap-server localhost:9092 \
        --partitions 1 --replication-factor 1
    
    docker exec kafka kafka-topics --create \
        --topic retail-price-changes \
        --bootstrap-server localhost:9092 \
        --partitions 2 --replication-factor 1
    
    docker exec kafka kafka-topics --create \
        --topic retail-customer-events \
        --bootstrap-server localhost:9092 \
        --partitions 2 --replication-factor 1
    
    print_status "Kafka topics created"
}

# Wait for ClickHouse to be ready and verify schema
verify_clickhouse_schema() {
    print_status "Verifying ClickHouse schema..."
    
    # Wait for ClickHouse to be ready (using health check)
    local max_attempts=30
    local attempt=1
    
    until curl -s http://localhost:8123/ping > /dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "ClickHouse failed to become ready after $max_attempts attempts"
            exit 1
        fi
        print_warning "Waiting for ClickHouse to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    # Wait for initialization script to complete
    print_status "Waiting for ClickHouse initialization to complete..."
    sleep 20
    
    # Verify tables were created
    if docker exec clickhouse clickhouse-client --password clickhouse --query "SHOW TABLES FROM retail" | grep -q "fact_sales"; then
        print_status "ClickHouse schema verified successfully"
    else
        print_error "ClickHouse schema creation failed"
        print_warning "Retrying schema verification..."
        sleep 10
        # Try one more time
        if docker exec clickhouse clickhouse-client --password clickhouse --query "SHOW TABLES FROM retail" | grep -q "fact_sales"; then
            print_status "ClickHouse schema verified successfully on retry"
        else
            print_error "ClickHouse schema creation failed after retry"
            exit 1
        fi
    fi
}

# Wait for Airflow to be ready
wait_for_airflow() {
    print_status "Waiting for Airflow to be ready..."
    
    local max_attempts=60
    local attempt=1
    
    until curl -s http://localhost:8081/health > /dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "Airflow failed to become ready after $max_attempts attempts"
            print_warning "Check Airflow logs with: docker logs airflow-webserver"
            exit 1
        fi
        print_warning "Waiting for Airflow to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    print_status "Airflow is ready"
}

# Wait for Spark to be ready
wait_for_spark() {
    print_status "Waiting for Spark to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    until curl -s http://localhost:8082/ > /dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "Spark failed to become ready after $max_attempts attempts"
            exit 1
        fi
        print_warning "Waiting for Spark to be ready... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_status "Spark is ready"
}

# Check if service is healthy
check_service_health() {
    local service_name="$1"
    local health_status
    
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$service_name" 2>/dev/null || echo "unknown")
    
    if [ "$health_status" = "healthy" ]; then
        return 0
    else
        return 1
    fi
}

# Wait for all services to be healthy
wait_for_all_services() {
    print_status "Waiting for all services to become healthy..."
    
    local services=("minio" "kafka" "clickhouse" "airflow-postgres" "airflow-redis" "spark-master")
    local max_attempts=60
    local all_healthy=false
    
    for attempt in $(seq 1 $max_attempts); do
        local unhealthy_services=()
        
        for service in "${services[@]}"; do
            if ! check_service_health "$service"; then
                unhealthy_services+=("$service")
            fi
        done
        
        if [ ${#unhealthy_services[@]} -eq 0 ]; then
            all_healthy=true
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Some services failed to become healthy after $max_attempts attempts:"
            for service in "${unhealthy_services[@]}"; do
                print_error "  - $service"
            done
            print_warning "You can check service logs with: docker logs <service_name>"
            exit 1
        fi
        
        print_warning "Waiting for services to become healthy... (attempt $attempt/$max_attempts)"
        print_warning "Unhealthy services: ${unhealthy_services[*]}"
        sleep 10
    done
    
    if [ "$all_healthy" = true ]; then
        print_status "All core services are healthy!"
    fi
}

# Generate initial sample data
generate_sample_data() {
    print_status "Generating initial sample data..."
    
    # Wait for data-generator to be healthy
    local max_attempts=30
    local attempt=1
    
    until check_service_health "data-generator"; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "Data generator failed to become healthy after $max_attempts attempts"
            exit 1
        fi
        print_warning "Waiting for data generator to be healthy... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    # Create sample dimension data
    docker exec data-generator python scripts/create_sample_data.py \
        --stores 10 \
        --products 100 \
        --categories 5
    
    print_status "Sample data generated"
}

# Print service information
print_service_info() {
    echo ""
    echo "🎉 Bootstrap completed successfully!"
    echo ""
    echo "📊 Services Information:"
    echo "========================"
    echo "MinIO Console:      http://localhost:9001 (minioadmin/minioadmin)"
    echo "Kafka UI:           http://localhost:8080"
    echo "Airflow:            http://localhost:8081 (airflow/airflow)"
    echo "Spark Master UI:    http://localhost:8082"
    echo "ClickHouse HTTP:    http://localhost:8123"
    echo ""
    echo "📁 Data Locations:"
    echo "=================="
    echo "Logs:               ./logs/"
    echo "DAGs:               ./dags/"
    echo "Models:             ./models/"
    echo "Config:             ./config/"
    echo ""
    echo "🚀 Next Steps:"
    echo "=============="
    echo "1. Generate more data: docker exec data-generator python scripts/data_generator.py"
    echo "2. Check Kafka topics: docker exec kafka kafka-topics --list --bootstrap-server localhost:9092"
    echo "3. Run sample queries: docker exec clickhouse clickhouse-client --password clickhouse --database retail"
    echo "4. Monitor pipelines: http://localhost:8081"
    echo ""
}

# Main execution
main() {
    print_status "Starting bootstrap process..."
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    
    # Create directories and config
    create_directories
    create_env_file
    
    print_status "Starting services with Docker Compose..."
    docker-compose up -d
    
    # Wait for all core services to be healthy
    wait_for_all_services
    
    # Wait for services and initialize
    create_minio_buckets
    create_kafka_topics
    verify_clickhouse_schema
    wait_for_airflow
    wait_for_spark
    
    # Generate initial data
    generate_sample_data
    
    # Print final information
    print_service_info
    
    print_status "Bootstrap completed successfully! 🎉"
}

# Run main function
main "$@"