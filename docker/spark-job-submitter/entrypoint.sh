#!/bin/bash

# Automated Spark Job Submitter Entrypoint
# This script waits for all dependencies to be ready and then submits Spark jobs

set -e

echo "🚀 Spark Job Submitter - Starting up..."
echo "=========================================="

# Configuration
SPARK_MASTER="spark://spark-master:7077"
KAFKA_BOOTSTRAP="kafka:9092"
CLICKHOUSE_HOST="clickhouse"
CLICKHOUSE_PORT="8123"
MAX_WAIT_SECONDS=300
WAIT_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local description="$3"
    
    log "Waiting for $description to be ready..."
    
    local counter=0
    while [ $counter -lt $MAX_WAIT_SECONDS ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            log_success "$description is ready!"
            return 0
        fi
        log_warning "Still waiting for $description... ($((counter + WAIT_INTERVAL))s/$MAX_WAIT_SECONDS)"
        sleep $WAIT_INTERVAL
        counter=$((counter + WAIT_INTERVAL))
    done
    
    log_error "Timeout waiting for $description after $MAX_WAIT_SECONDS seconds"
    return 1
}

# Check if Spark master is ready
check_spark_master() {
    curl -s http://spark-master:8080/ >/dev/null 2>&1
}

# Check if Spark worker is connected
check_spark_worker() {
    local response=$(curl -s http://spark-master:8080/ | grep -o "Alive Workers.*[0-9]" | grep -o "[0-9]")
    [ "$response" -gt 0 ] 2>/dev/null
}

# Check if Kafka is ready
check_kafka() {
    nc -z kafka 9092
}

# Check if ClickHouse is ready
check_clickhouse() {
    curl -s http://clickhouse:8123/ping >/dev/null 2>&1
}

# Check if Kafka topics exist
check_kafka_topics() {
    docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 | grep -q "retail-sales-transactions" && \
    docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 | grep -q "retail-inventory-updates"
}

# Create checkpoint directories
create_checkpoint_dirs() {
    log "Creating checkpoint directories..."
    mkdir -p /tmp/checkpoint/sales_streaming
    mkdir -p /tmp/checkpoint/inventory_streaming
    mkdir -p /tmp/checkpoint/unified_bridge
    mkdir -p /tmp/checkpoint/ml_training
    log_success "Checkpoint directories created"
}

# Submit unified streaming bridge job
submit_unified_bridge() {
    log "Submitting Unified Streaming Bridge job..."
    
    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --deploy-mode client \
        --name "UnifiedStreamingBridge" \
        --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.clickhouse:clickhouse-jdbc:0.4.6" \
        --conf "spark.sql.adaptive.enabled=true" \
        --conf "spark.sql.adaptive.coalescePartitions.enabled=true" \
        --conf "spark.streaming.backpressure.enabled=true" \
        --conf "spark.streaming.kafka.maxRatePerPartition=75" \
        --conf "spark.driver.memory=2g" \
        --conf "spark.executor.memory=2g" \
        --conf "spark.driver.cores=2" \
        --conf "spark.executor.cores=2" \
        /opt/spark/jobs/unified_streaming_bridge.py &
    
    local pid=$!
    log "Unified Streaming Bridge job submitted with PID: $pid"
    return 0
}

# Monitor job status
monitor_jobs() {
    log "Starting job monitoring..."
    
    while true; do
        echo "=== Spark Job Status ==="
        curl -s http://spark-master:8080/api/v1/applications 2>/dev/null | \
            grep -o '"name":"[^"]*","state":"[^"]*"' | \
            sed 's/"name":"\([^"]*\)","state":"\([^"]*\)"/\1: \2/g' || \
            echo "No running applications"
        
        echo "=== Worker Status ==="
        curl -s http://spark-master:8080/ | grep -E "Alive Workers|Cores in use|Memory in use" | \
            sed 's/<[^>]*>//g' | sed 's/^[ \t]*//'
        
        echo "======================="
        sleep 30
    done
}

# Main execution
main() {
    log "Starting automated Spark job submission..."
    
    # Wait for all dependencies
    wait_for_service "spark-master" "check_spark_master" "Spark Master"
    wait_for_service "spark-worker" "check_spark_worker" "Spark Worker"
    wait_for_service "kafka" "check_kafka" "Kafka"
    wait_for_service "clickhouse" "check_clickhouse" "ClickHouse"
    wait_for_service "kafka-topics" "check_kafka_topics" "Kafka Topics"
    
    log_success "All dependencies are ready!"
    
    # Create checkpoint directories
    create_checkpoint_dirs
    
    # Submit jobs
    log "Submitting Spark streaming jobs..."
    submit_unified_bridge
    
    log_success "Spark jobs submitted successfully!"
    log "Streaming jobs are now running and will process data continuously"
    
    # Start monitoring
    monitor_jobs
}

# Handle signals for graceful shutdown
trap 'log "Received shutdown signal, stopping..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"