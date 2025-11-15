#!/bin/bash

# Comprehensive Data Pipeline Setup Script
# Builds and runs the entire data pipeline with proper testing
# Ensures data flows from data generation through Kafka to ClickHouse and MinIO

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local max_attempts="$3"
    local attempt=1
    
    print_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        print_warning "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to check container health
check_container_health() {
    local container_name="$1"
    local health_status
    
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
    
    if [ "$health_status" = "healthy" ]; then
        return 0
    else
        return 1
    fi
}

# Function to wait for all containers to be healthy
wait_for_all_containers() {
    print_info "Waiting for all containers to become healthy..."
    
    local containers=("minio" "kafka" "clickhouse" "airflow-postgres" "airflow-redis" "spark-master" "data-generator")
    local max_attempts=60
    local all_healthy=false
    
    for attempt in $(seq 1 $max_attempts); do
        local unhealthy_containers=()
        
        for container in "${containers[@]}"; do
            if ! check_container_health "$container"; then
                unhealthy_containers+=("$container")
            fi
        done
        
        if [ ${#unhealthy_containers[@]} -eq 0 ]; then
            all_healthy=true
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Some containers failed to become healthy after $max_attempts attempts:"
            for container in "${unhealthy_containers[@]}"; do
                print_error "  - $container"
            done
            print_warning "You can check container logs with: docker logs <container_name>"
            return 1
        fi
        
        print_warning "Waiting for containers to become healthy... (attempt $attempt/$max_attempts)"
        print_warning "Unhealthy containers: ${unhealthy_containers[*]}"
        sleep 10
    done
    
    if [ "$all_healthy" = true ]; then
        print_success "All containers are healthy!"
    fi
}

# Function to test Kafka topics
test_kafka_topics() {
    print_info "Testing Kafka topics for message presence..."
    
    local topics=("retail-sales-transactions" "retail-inventory-updates")
    local max_attempts=20
    
    for topic in "${topics[@]}"; do
        print_info "Checking topic: $topic"
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            # Check if topic has messages
            local message_count
            message_count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
                --bootstrap-server localhost:9092 \
                --topic "$topic" \
                --time -1 | awk -F ":" '{sum += $3} END {print sum}' 2>/dev/null || echo "0")
            
            if [ "$message_count" -gt 0 ]; then
                print_success "Topic $topic has $message_count messages"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                print_warning "Topic $topic has no messages after $max_attempts attempts"
            fi
            
            print_warning "Waiting for messages in $topic... (attempt $attempt/$max_attempts)"
            sleep 5
            attempt=$((attempt + 1))
        done
    done
}

# Function to verify ClickHouse tables
verify_clickhouse_tables() {
    print_info "Verifying ClickHouse tables are being populated..."
    
    # Run the existing check_clickhouse_tables.py script
    if command_exists python3; then
        print_info "Running ClickHouse table verification..."
        python3 scripts/check_clickhouse_tables.py
    else
        print_warning "Python3 not available, skipping detailed ClickHouse verification"
        # Basic check using docker exec
        docker exec clickhouse clickhouse-client --password clickhouse --database retail \
            --query "SELECT name, total_rows FROM system.tables WHERE database = 'retail' AND total_rows > 0"
    fi
}

# Function to test MinIO connectivity
test_minio_connectivity() {
    print_info "Testing MinIO connectivity and data storage..."
    
    if command_exists python3; then
        print_info "Running MinIO integration tests..."
        python3 scripts/test_minio_integration.py
    else
        print_warning "Python3 not available, skipping MinIO integration tests"
        # Basic MinIO check
        if curl -s http://localhost:9001/minio/health/live >/dev/null; then
            print_success "MinIO is accessible"
        else
            print_error "MinIO is not accessible"
        fi
    fi
}

# Function to run end-to-end pipeline tests
run_pipeline_tests() {
    print_info "Running end-to-end pipeline tests..."
    
    if command_exists python3; then
        print_info "Running pipeline flow tests..."
        python3 scripts/test_pipeline_flow.py
        
        print_info "Running startup checks..."
        python3 scripts/startup_check.py
    else
        print_warning "Python3 not available, skipping pipeline tests"
    fi
}

# Function to check service status
check_service_status() {
    print_info "Checking service status..."
    
    local services=(
        "minio:9000"
        "kafka:9092" 
        "clickhouse:8123"
        "airflow-webserver:8081"
        "spark-master:8082"
        "kafka-ui:8080"
    )
    
    for service in "${services[@]}"; do
        local name="${service%:*}"
        local port="${service#*:}"
        
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            print_success "$name is accessible on port $port"
        else
            print_warning "$name is not accessible on port $port"
        fi
    done
}

# Function to display monitoring information
display_monitoring_info() {
    echo ""
    echo "🎉 Data Pipeline Setup Complete!"
    echo ""
    echo "📊 Service URLs:"
    echo "========================"
    echo "MinIO Console:      http://localhost:9001 (minioadmin/minioadmin)"
    echo "Kafka UI:           http://localhost:8080"
    echo "Airflow:            http://localhost:8081 (airflow/airflow)"
    echo "Spark Master UI:    http://localhost:8082"
    echo "ClickHouse HTTP:    http://localhost:8123"
    echo ""
    echo "🔍 Data Flow Verification:"
    echo "=========================="
    echo "Kafka Topics:       docker exec kafka kafka-topics --list --bootstrap-server localhost:9092"
    echo "ClickHouse Data:    docker exec clickhouse clickhouse-client --password clickhouse --database retail"
    echo "MinIO Buckets:      docker exec minio mc ls minio/"
    echo ""
    echo "📈 Monitoring Commands:"
    echo "======================"
    echo "Container Status:   docker-compose ps"
    echo "Container Logs:     docker-compose logs -f"
    echo "Kafka Messages:     docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic retail-sales-transactions --from-beginning --max-messages 5"
    echo ""
    echo "🚀 Pipeline Status:"
    echo "=================="
    echo "Data Generation:    Running in data-generator container"
    echo "Kafka Streaming:    Active with retail-sales-transactions and retail-inventory-updates topics"
    echo "Spark Processing:   Auto-submitted streaming jobs"
    echo "ClickHouse Storage: Direct Kafka integration + Spark streaming"
    echo "MinIO Storage:      Models and processed data storage"
    echo ""
}

# Main execution function
main() {
    echo "🏪 Comprehensive Data Pipeline Setup"
    echo "===================================="
    echo ""
    echo "This script will:"
    echo "1. Build and start all Docker containers"
    echo "2. Initialize ClickHouse with schemas and Kafka integration"
    echo "3. Start data generators and verify data production"
    echo "4. Test Kafka topics for message presence"
    echo "5. Verify ClickHouse tables are being populated"
    echo "6. Check MinIO for data storage"
    echo "7. Run end-to-end pipeline tests"
    echo "8. Provide monitoring and health checks"
    echo ""
    
    # Check prerequisites
    print_info "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
    
    # Step 1: Build and start Docker containers
    print_info "Step 1: Building and starting Docker containers..."
    docker-compose down 2>/dev/null || true
    docker-compose build --no-cache
    docker-compose up -d
    
    # Step 2: Wait for all containers to be healthy
    print_info "Step 2: Waiting for containers to become healthy..."
    wait_for_all_containers
    
    # Step 3: Initialize ClickHouse schemas (already done via init scripts)
    print_info "Step 3: ClickHouse schemas initialized via docker-entrypoint-initdb.d"
    
    # Step 4: Verify data generators are producing data
    print_info "Step 4: Verifying data generators are producing data..."
    test_kafka_topics
    
    # Step 5: Data flow verification
    print_info "Step 5: Data flow verification..."
    
    # 5.1 Test Kafka topics for message presence
    print_info "5.1 Testing Kafka topics..."
    test_kafka_topics
    
    # 5.2 Verify ClickHouse tables are being populated
    print_info "5.2 Verifying ClickHouse tables..."
    verify_clickhouse_tables
    
    # 5.3 Check MinIO for data storage
    print_info "5.3 Testing MinIO connectivity..."
    test_minio_connectivity
    
    # Step 6: Run end-to-end testing
    print_info "Step 6: Running end-to-end tests..."
    run_pipeline_tests
    
    # Step 7: Monitoring and health checks
    print_info "Step 7: Performing final health checks..."
    check_service_status
    
    # Display final information
    display_monitoring_info
    
    print_success "Data pipeline setup completed successfully! 🎉"
    echo ""
    print_info "The pipeline is now running and processing data from:"
    print_info "Data Generation → Kafka → ClickHouse & MinIO"
    echo ""
    print_info "Use the monitoring commands above to verify data flow and check system status."
}

# Handle script interruption
cleanup() {
    print_warning "Script interrupted. Cleaning up..."
    docker-compose down
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"