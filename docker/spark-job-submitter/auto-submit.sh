#!/bin/bash

# Simple Spark Job Auto-Submitter
# This script waits for dependencies and submits Spark jobs automatically

set -e

echo "🚀 Auto-submitting Spark jobs..."
echo "=================================="

# Wait for Spark worker to be connected
wait_for_worker() {
    echo "Waiting for Spark worker to connect..."
    while true; do
        workers=$(curl -s http://localhost:8080/ | grep -o "Alive Workers.*[0-9]" | grep -o "[0-9]" || echo "0")
        if [ "$workers" -gt 0 ]; then
            echo "✅ Spark worker connected!"
            break
        fi
        echo "⏳ Waiting for worker... ($workers workers)"
        sleep 5
    done
}

# Wait for Kafka to be ready
wait_for_kafka() {
    echo "Waiting for Kafka to be ready..."
    while ! nc -z kafka 9092; do
        echo "⏳ Waiting for Kafka..."
        sleep 5
    done
    echo "✅ Kafka is ready!"
}

# Wait for ClickHouse to be ready
wait_for_clickhouse() {
    echo "Waiting for ClickHouse to be ready..."
    while ! curl -s http://clickhouse:8123/ping >/dev/null; do
        echo "⏳ Waiting for ClickHouse..."
        sleep 5
    done
    echo "✅ ClickHouse is ready!"
}

# Submit unified streaming bridge job
submit_unified_bridge() {
    echo "📤 Submitting Unified Streaming Bridge job..."
    
    /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
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
    
    echo "✅ Unified Streaming Bridge job submitted!"
}

# Main execution
main() {
    echo "Starting automatic Spark job submission..."
    
    # Wait for dependencies
    wait_for_worker
    wait_for_kafka
    wait_for_clickhouse
    
    # Create checkpoint directories
    mkdir -p /tmp/checkpoint/unified_bridge
    
    # Submit jobs
    submit_unified_bridge
    
    echo "🎉 Spark jobs submitted successfully!"
    echo "Streaming jobs are now running and processing data continuously"
    
    # Keep the script running to monitor jobs
    while true; do
        echo "=== Job Status ==="
        curl -s http://localhost:8080/api/v1/applications 2>/dev/null | \
            grep -o '"name":"[^"]*","state":"[^"]*"' | \
            sed 's/"name":"\([^"]*\)","state":"\([^"]*\)"/\1: \2/g' || \
            echo "No running applications"
        echo "=================="
        sleep 30
    done
}

# Run main function
main "$@"