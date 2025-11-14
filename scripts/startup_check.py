#!/usr/bin/env python3
"""
Startup Check Script for Retail Inventory Pipeline
Ensures all services are ready before starting the data pipeline
"""

import time
import logging
import requests
import json
from kafka import KafkaProducer, KafkaConsumer
from clickhouse_driver import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PipelineStartupChecker:
    def __init__(self):
        self.max_retries = 30
        self.retry_delay = 10  # seconds
        
    def wait_for_kafka(self):
        """Wait for Kafka to be ready"""
        logger.info("Waiting for Kafka to be ready...")
        for i in range(self.max_retries):
            try:
                producer = KafkaProducer(
                    bootstrap_servers=['kafka:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                producer.close()
                logger.info("✅ Kafka is ready!")
                return True
            except Exception as e:
                logger.info(f"⏳ Kafka not ready yet (attempt {i+1}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay)
        
        logger.error("❌ Kafka failed to become ready")
        return False
    
    def wait_for_clickhouse(self):
        """Wait for ClickHouse to be ready"""
        logger.info("Waiting for ClickHouse to be ready...")
        for i in range(self.max_retries):
            try:
                client = Client(
                    host='clickhouse',
                    port=8123,
                    user='default',
                    password='clickhouse'
                )
                client.execute('SELECT 1')
                logger.info("✅ ClickHouse is ready!")
                return True
            except Exception as e:
                logger.info(f"⏳ ClickHouse not ready yet (attempt {i+1}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay)
        
        logger.error("❌ ClickHouse failed to become ready")
        return False
    
    def wait_for_spark(self):
        """Wait for Spark master to be ready"""
        logger.info("Waiting for Spark master to be ready...")
        for i in range(self.max_retries):
            try:
                response = requests.get('http://spark-master:8080', timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Spark master is ready!")
                    return True
            except Exception as e:
                logger.info(f"⏳ Spark master not ready yet (attempt {i+1}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay)
        
        logger.error("❌ Spark master failed to become ready")
        return False
    
    def create_kafka_topics(self):
        """Ensure Kafka topics exist"""
        logger.info("Creating Kafka topics if they don't exist...")
        topics = ['retail-sales-transactions', 'retail-inventory-updates']
        
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='startup-checker'
            )
            
            # Kafka will auto-create topics if configured
            existing_topics = consumer.topics()
            for topic in topics:
                if topic not in existing_topics:
                    logger.info(f"Topic '{topic}' will be auto-created when first used")
                else:
                    logger.info(f"✅ Topic '{topic}' exists")
            
            consumer.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check Kafka topics: {e}")
            return False
    
    def check_clickhouse_tables(self):
        """Verify ClickHouse tables exist"""
        logger.info("Checking ClickHouse tables...")
        try:
            client = Client(
                host='clickhouse',
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
            logger.error(f"❌ Failed to check ClickHouse tables: {e}")
            return False
    
    def run_all_checks(self):
        """Run all startup checks"""
        logger.info("🚀 Starting pipeline startup checks...")
        
        checks = [
            ("Kafka", self.wait_for_kafka),
            ("ClickHouse", self.wait_for_clickhouse),
            ("Kafka Topics", self.create_kafka_topics),
            ("ClickHouse Tables", self.check_clickhouse_tables),
            ("Spark Master", self.wait_for_spark)
        ]
        
        results = []
        for check_name, check_func in checks:
            logger.info(f"Running {check_name} check...")
            try:
                result = check_func()
                results.append((check_name, result))
                if not result:
                    logger.error(f"❌ {check_name} check failed")
                    break
            except Exception as e:
                logger.error(f"❌ {check_name} check failed with exception: {e}")
                results.append((check_name, False))
                break
        
        # Summary
        logger.info("\n📊 Startup Check Results:")
        logger.info("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for check_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{check_name}: {status}")
        
        logger.info("=" * 50)
        logger.info(f"Overall: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("🎉 All startup checks passed! Pipeline is ready to run.")
            return True
        else:
            logger.error("⚠️ Some startup checks failed. Pipeline may not work correctly.")
            return False

def main():
    """Main entry point"""
    checker = PipelineStartupChecker()
    success = checker.run_all_checks()
    
    if success:
        logger.info("Startup completed successfully!")
        return 0
    else:
        logger.error("Startup failed!")
        return 1

if __name__ == "__main__":
    exit(main())