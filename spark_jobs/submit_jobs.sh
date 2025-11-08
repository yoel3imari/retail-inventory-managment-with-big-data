#!/bin/bash

# Spark Job Submission Script
# This script submits Spark jobs to the cluster

set -e

# Configuration
SPARK_MASTER="spark://spark-master:7077"
JARS_PATH="/opt/spark/jars"
JOBS_PATH="/opt/spark/jobs"
CHECKPOINT_PATH="/tmp/checkpoint"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Spark master is available
check_spark_master() {
    log "Checking Spark master availability..."
    if nc -z spark-master 7077 2>/dev/null; then
        log_success "Spark master is available"
        return 0
    else
        log_error "Spark master is not available"
        return 1
    fi
}

# Submit sales streaming job
submit_sales_streaming() {
    log "Submitting Sales Streaming job..."
    
    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --deploy-mode client \
        --name "RetailSalesStreaming" \
        --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.clickhouse:clickhouse-jdbc:0.4.6" \
        --conf "spark.sql.adaptive.enabled=true" \
        --conf "spark.sql.adaptive.coalescePartitions.enabled=true" \
        --conf "spark.streaming.backpressure.enabled=true" \
        --conf "spark.streaming.kafka.maxRatePerPartition=100" \
        --conf "spark.driver.memory=1g" \
        --conf "spark.executor.memory=1g" \
        --conf "spark.driver.cores=1" \
        --conf "spark.executor.cores=1" \
        $JOBS_PATH/sales_streaming.py
    
    if [ $? -eq 0 ]; then
        log_success "Sales Streaming job submitted successfully"
    else
        log_error "Failed to submit Sales Streaming job"
        exit 1
    fi
}

# Submit inventory streaming job
submit_inventory_streaming() {
    log "Submitting Inventory Streaming job..."
    
    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --deploy-mode client \
        --name "RetailInventoryStreaming" \
        --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.clickhouse:clickhouse-jdbc:0.4.6" \
        --conf "spark.sql.adaptive.enabled=true" \
        --conf "spark.sql.adaptive.coalescePartitions.enabled=true" \
        --conf "spark.streaming.backpressure.enabled=true" \
        --conf "spark.streaming.kafka.maxRatePerPartition=50" \
        --conf "spark.driver.memory=1g" \
        --conf "spark.executor.memory=1g" \
        --conf "spark.driver.cores=1" \
        --conf "spark.executor.cores=1" \
        $JOBS_PATH/inventory_streaming.py
    
    if [ $? -eq 0 ]; then
        log_success "Inventory Streaming job submitted successfully"
    else
        log_error "Failed to submit Inventory Streaming job"
        exit 1
    fi
}

# Submit ML training job
submit_ml_training() {
    log "Submitting ML Training job..."
    
    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --deploy-mode client \
        --name "RetailMLTraining" \
        --packages "com.clickhouse:clickhouse-jdbc:0.4.6" \
        --conf "spark.sql.adaptive.enabled=true" \
        --conf "spark.sql.adaptive.coalescePartitions.enabled=true" \
        --conf "spark.driver.memory=2g" \
        --conf "spark.executor.memory=2g" \
        --conf "spark.driver.cores=2" \
        --conf "spark.executor.cores=2" \
        --conf "spark.sql.adaptive.advisoryPartitionSizeInBytes=64m" \
        $JOBS_PATH/ml_training.py
    
    if [ $? -eq 0 ]; then
        log_success "ML Training job submitted successfully"
    else
        log_error "Failed to submit ML Training job"
        exit 1
    fi
}

# Submit batch processing job
submit_batch_processing() {
    log "Submitting Batch Processing job..."
    
    /opt/spark/bin/spark-submit \
        --master $SPARK_MASTER \
        --deploy-mode client \
        --name "RetailBatchProcessing" \
        --packages "com.clickhouse:clickhouse-jdbc:0.4.6" \
        --conf "spark.sql.adaptive.enabled=true" \
        --conf "spark.driver.memory=1g" \
        --conf "spark.executor.memory=1g" \
        --conf "spark.sql.adaptive.advisoryPartitionSizeInBytes=128m" \
        $JOBS_PATH/batch_processing.py
    
    if [ $? -eq 0 ]; then
        log_success "Batch Processing job submitted successfully"
    else
        log_error "Failed to submit Batch Processing job"
        exit 1
    fi
}

# Create checkpoint directories
create_checkpoint_dirs() {
    log "Creating checkpoint directories..."
    mkdir -p $CHECKPOINT_PATH/sales_streaming
    mkdir -p $CHECKPOINT_PATH/inventory_streaming
    mkdir -p $CHECKPOINT_PATH/ml_training
    log_success "Checkpoint directories created"
}

# Show job status
show_job_status() {
    log "Checking Spark job status..."
    
    # Get running applications
    curl -s http://spark-master:8080/api/v1/applications | jq -r '.[] | "\(.id)\t\(.name)\t\(.state)"' 2>/dev/null || echo "Unable to fetch job status"
}

# Clean up checkpoint data
clean_checkpoints() {
    log "Cleaning up checkpoint data..."
    rm -rf $CHECKPOINT_PATH/*
    log_success "Checkpoint data cleaned"
}

# Show usage
usage() {
    echo "Usage: $0 {sales|inventory|ml|batch|all|status|clean|help}"
    echo ""
    echo "Commands:"
    echo "  sales      - Submit sales streaming job"
    echo "  inventory  - Submit inventory streaming job"
    echo "  ml         - Submit ML training job"
    echo "  batch      - Submit batch processing job"
    echo "  all        - Submit all streaming jobs"
    echo "  status     - Show job status"
    echo "  clean      - Clean checkpoint data"
    echo "  help       - Show this help message"
    echo ""
}

# Main execution
case "$1" in
    sales)
        check_spark_master
        create_checkpoint_dirs
        submit_sales_streaming
        ;;
    inventory)
        check_spark_master
        create_checkpoint_dirs
        submit_inventory_streaming
        ;;
    ml)
        check_spark_master
        submit_ml_training
        ;;
    batch)
        check_spark_master
        submit_batch_processing
        ;;
    all)
        check_spark_master
        create_checkpoint_dirs
        log "Submitting all streaming jobs..."
        submit_sales_streaming &
        submit_inventory_streaming &
        wait
        log_success "All streaming jobs submitted"
        ;;
    status)
        show_job_status
        ;;
    clean)
        clean_checkpoints
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Invalid command: $1"
        usage
        exit 1
        ;;
esac