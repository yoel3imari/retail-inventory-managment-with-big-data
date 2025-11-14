#!/usr/bin/env python3
"""
Test script to verify the complete pipeline flow from data-generator to ClickHouse
"""

import json
import time
import requests
import logging
from kafka import KafkaProducer
from clickhouse_driver import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_kafka_connection():
    """Test Kafka connectivity and topic creation"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Test message
        test_message = {
            "transaction_id": "test_001",
            "store_id": "STORE101",
            "product_id": "SKU10001",
            "quantity": 1,
            "unit_price": 10.0,
            "total_amount": 10.0,
            "timestamp": "2024-01-01T12:00:00",
            "customer_id": "CUST9999",
            "payment_method": "test"
        }
        
        producer.send('retail-sales-transactions', test_message)
        producer.flush()
        producer.close()
        
        logger.info("✅ Kafka connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Kafka connection test failed: {e}")
        return False

def test_clickhouse_connection():
    """Test ClickHouse connectivity"""
    try:
        client = Client(
            host='localhost',
            port=8123,
            user='default',
            password='clickhouse',
            database='retail'
        )
        
        # Test query
        result = client.execute('SELECT 1 as test_value')
        logger.info(f"✅ ClickHouse connection test passed: {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ ClickHouse connection test failed: {e}")
        return False

def test_clickhouse_tables():
    """Verify that ClickHouse tables exist"""
    try:
        client = Client(
            host='localhost',
            port=8123,
            user='default',
            password='clickhouse',
            database='retail'
        )
        
        tables_to_check = [
            'spark_sales_metrics',
            'spark_inventory_metrics', 
            'spark_streaming_alerts',
            'streaming_events_raw',
            'spark_job_monitoring'
        ]
        
        for table in tables_to_check:
            result = client.execute(f"EXISTS {table}")
            if result[0][0] == 1:
                logger.info(f"✅ Table {table} exists")
            else:
                logger.error(f"❌ Table {table} does not exist")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"❌ ClickHouse tables test failed: {e}")
        return False

def test_spark_ui():
    """Test Spark UI accessibility"""
    try:
        response = requests.get('http://localhost:8082', timeout=10)
        if response.status_code == 200:
            logger.info("✅ Spark UI is accessible")
            return True
        else:
            logger.error(f"❌ Spark UI returned status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Spark UI test failed: {e}")
        return False

def test_kafka_ui():
    """Test Kafka UI accessibility"""
    try:
        response = requests.get('http://localhost:8080', timeout=10)
        if response.status_code == 200:
            logger.info("✅ Kafka UI is accessible")
            return True
        else:
            logger.error(f"❌ Kafka UI returned status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Kafka UI test failed: {e}")
        return False

def main():
    """Run all pipeline tests"""
    logger.info("🚀 Starting pipeline flow tests...")
    
    tests = [
        ("Kafka Connection", test_kafka_connection),
        ("ClickHouse Connection", test_clickhouse_connection),
        ("ClickHouse Tables", test_clickhouse_tables),
        ("Spark UI", test_spark_ui),
        ("Kafka UI", test_kafka_ui)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Small delay between tests
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    logger.info("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 40)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All pipeline tests passed! The data flow should work correctly.")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()