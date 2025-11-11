#!/usr/bin/env python3
"""
Test Script for Spark Streaming Bridge between Kafka and ClickHouse

This script tests the complete data pipeline:
1. Kafka topics and connectivity
2. Data generation and publishing
3. Spark streaming job execution
4. ClickHouse data ingestion
5. Data validation and quality checks
"""

import json
import time
import uuid
import logging
import requests
from datetime import datetime, timedelta
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PipelineTester:
    """Comprehensive test for Kafka-Spark-ClickHouse pipeline"""
    
    def __init__(self):
        self.kafka_bootstrap_servers = "localhost:9092"
        self.clickhouse_url = "http://localhost:8123"
        self.clickhouse_db = "retail"
        
        # Test configuration
        self.test_events_count = 100
        self.test_timeout = 300  # 5 minutes
        
    def check_kafka_connectivity(self):
        """Check Kafka connectivity and topics"""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.kafka_bootstrap_servers,
                client_id='pipeline_tester'
            )
            
            topics = admin_client.list_topics()
            required_topics = ['sales_events', 'inventory_events']
            
            logger.info(f"Available Kafka topics: {topics}")
            
            for topic in required_topics:
                if topic not in topics:
                    logger.warning(f"Required topic '{topic}' not found. Creating...")
                    topic_list = [NewTopic(name=topic, num_partitions=1, replication_factor=1)]
                    admin_client.create_topics(new_topics=topic_list, validate_only=False)
                    logger.info(f"Created topic: {topic}")
                else:
                    logger.info(f"Topic '{topic}' exists")
            
            admin_client.close()
            return True
            
        except Exception as e:
            logger.error(f"Kafka connectivity check failed: {e}")
            return False
    
    def check_clickhouse_connectivity(self):
        """Check ClickHouse connectivity and database"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.clickhouse_url}/ping", timeout=10)
            if response.status_code != 200:
                logger.error("ClickHouse ping failed")
                return False
            
            # Check if retail database exists
            query = "SHOW DATABASES"
            response = requests.post(
                f"{self.clickhouse_url}/",
                data=query,
                params={'database': 'default'},
                timeout=10
            )
            
            if response.status_code == 200:
                databases = [line.strip() for line in response.text.strip().split('\n')]
                if 'retail' in databases:
                    logger.info("Retail database exists in ClickHouse")
                    return True
                else:
                    logger.error("Retail database not found in ClickHouse")
                    return False
            else:
                logger.error(f"ClickHouse query failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"ClickHouse connectivity check failed: {e}")
            return False
    
    def generate_test_events(self):
        """Generate test events for both sales and inventory"""
        producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        test_events = []
        
        # Generate sales events
        for i in range(self.test_events_count // 2):
            sales_event = {
                "sale_id": f"test_sale_{uuid.uuid4()}",
                "store_id": f"store_{i % 5 + 1}",
                "product_id": f"product_{i % 10 + 1}",
                "customer_id": f"customer_{i % 50 + 1}",
                "quantity": (i % 3) + 1,
                "unit_price": round(10 + (i % 90), 2),
                "total_amount": round(((i % 3) + 1) * (10 + (i % 90)), 2),
                "sale_timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "payment_method": ["credit_card", "debit_card", "cash"][i % 3],
                "promotion_id": f"promo_{i % 5}" if i % 4 == 0 else None
            }
            
            producer.send('sales_events', value=sales_event)
            test_events.append(('sales_events', sales_event))
            logger.debug(f"Sent sales event: {sales_event['sale_id']}")
        
        # Generate inventory events
        for i in range(self.test_events_count // 2):
            inventory_event = {
                "inventory_id": f"test_inv_{uuid.uuid4()}",
                "store_id": f"store_{i % 5 + 1}",
                "product_id": f"product_{i % 10 + 1}",
                "current_stock": 100 - (i % 50),
                "minimum_stock": 10,
                "maximum_stock": 200,
                "reorder_point": 20,
                "last_restock_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "next_restock_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "update_timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
            }
            
            producer.send('inventory_events', value=inventory_event)
            test_events.append(('inventory_events', inventory_event))
            logger.debug(f"Sent inventory event: {inventory_event['inventory_id']}")
        
        producer.flush()
        producer.close()
        
        logger.info(f"Generated {len(test_events)} test events")
        return test_events
    
    def verify_clickhouse_data(self, max_wait_seconds=60):
        """Verify data was written to ClickHouse tables"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check spark_sales_metrics table
                sales_metrics_query = "SELECT COUNT(*) as count FROM spark_sales_metrics"
                response = requests.post(
                    f"{self.clickhouse_url}/",
                    data=sales_metrics_query,
                    params={'database': self.clickhouse_db},
                    timeout=10
                )
                
                if response.status_code == 200:
                    sales_count = int(response.text.strip())
                    logger.info(f"Found {sales_count} records in spark_sales_metrics")
                    
                    if sales_count > 0:
                        # Check spark_inventory_metrics table
                        inventory_query = "SELECT COUNT(*) as count FROM spark_inventory_metrics"
                        response = requests.post(
                            f"{self.clickhouse_url}/",
                            data=inventory_query,
                            params={'database': self.clickhouse_db},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            inventory_count = int(response.text.strip())
                            logger.info(f"Found {inventory_count} records in spark_inventory_metrics")
                            
                            if inventory_count > 0:
                                # Check streaming_events_raw table
                                raw_query = "SELECT COUNT(*) as count FROM streaming_events_raw"
                                response = requests.post(
                                    f"{self.clickhouse_url}/",
                                    data=raw_query,
                                    params={'database': self.clickhouse_db},
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    raw_count = int(response.text.strip())
                                    logger.info(f"Found {raw_count} records in streaming_events_raw")
                                    
                                    return {
                                        'sales_metrics': sales_count,
                                        'inventory_metrics': inventory_count,
                                        'raw_events': raw_count
                                    }
                
                logger.info("Waiting for data to appear in ClickHouse...")
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking ClickHouse data: {e}")
                time.sleep(10)
        
        logger.error("Timeout waiting for data in ClickHouse")
        return None
    
    def run_data_quality_checks(self):
        """Run data quality checks on the ingested data"""
        try:
            checks_passed = 0
            total_checks = 0
            
            # Check 1: Verify no null store_ids in sales metrics
            query = "SELECT COUNT(*) FROM spark_sales_metrics WHERE store_id = '' OR store_id IS NULL"
            response = requests.post(
                f"{self.clickhouse_url}/",
                data=query,
                params={'database': self.clickhouse_db},
                timeout=10
            )
            
            if response.status_code == 200:
                null_count = int(response.text.strip())
                total_checks += 1
                if null_count == 0:
                    checks_passed += 1
                    logger.info("✓ Data quality check passed: No null store_ids in sales metrics")
                else:
                    logger.warning(f"✗ Data quality check failed: Found {null_count} null store_ids in sales metrics")
            
            # Check 2: Verify positive quantities in sales metrics
            query = "SELECT COUNT(*) FROM spark_sales_metrics WHERE total_quantity < 0"
            response = requests.post(
                f"{self.clickhouse_url}/",
                data=query,
                params={'database': self.clickhouse_db},
                timeout=10
            )
            
            if response.status_code == 200:
                negative_count = int(response.text.strip())
                total_checks += 1
                if negative_count == 0:
                    checks_passed += 1
                    logger.info("✓ Data quality check passed: No negative quantities in sales metrics")
                else:
                    logger.warning(f"✗ Data quality check failed: Found {negative_count} negative quantities in sales metrics")
            
            # Check 3: Verify valid stock status in inventory metrics
            query = "SELECT COUNT(*) FROM spark_inventory_metrics WHERE stock_status NOT IN ('IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK')"
            response = requests.post(
                f"{self.clickhouse_url}/",
                data=query,
                params={'database': self.clickhouse_db},
                timeout=10
            )
            
            if response.status_code == 200:
                invalid_status_count = int(response.text.strip())
                total_checks += 1
                if invalid_status_count == 0:
                    checks_passed += 1
                    logger.info("✓ Data quality check passed: All stock status values are valid")
                else:
                    logger.warning(f"✗ Data quality check failed: Found {invalid_status_count} invalid stock status values")
            
            # Check 4: Verify timestamp consistency
            query = """
            SELECT COUNT(*) FROM spark_sales_metrics 
            WHERE window_start > window_end OR window_start > now() + INTERVAL 1 DAY
            """
            response = requests.post(
                f"{self.clickhouse_url}/",
                data=query,
                params={'database': self.clickhouse_db},
                timeout=10
            )
            
            if response.status_code == 200:
                timestamp_issues = int(response.text.strip())
                total_checks += 1
                if timestamp_issues == 0:
                    checks_passed += 1
                    logger.info("✓ Data quality check passed: Timestamp consistency is maintained")
                else:
                    logger.warning(f"✗ Data quality check failed: Found {timestamp_issues} timestamp inconsistencies")
            
            logger.info(f"Data quality checks: {checks_passed}/{total_checks} passed")
            return checks_passed == total_checks
            
        except Exception as e:
            logger.error(f"Data quality checks failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive pipeline test"""
        logger.info("Starting comprehensive Kafka-Spark-ClickHouse pipeline test")
        
        # Step 1: Check connectivity
        logger.info("Step 1: Checking service connectivity...")
        if not self.check_kafka_connectivity():
            logger.error("Kafka connectivity test failed")
            return False
        
        if not self.check_clickhouse_connectivity():
            logger.error("ClickHouse connectivity test failed")
            return False
        
        logger.info("✓ Service connectivity tests passed")
        
        # Step 2: Generate test events
        logger.info("Step 2: Generating test events...")
        test_events = self.generate_test_events()
        logger.info(f"✓ Generated {len(test_events)} test events")
        
        # Step 3: Wait and verify data in ClickHouse
        logger.info("Step 3: Waiting for Spark streaming to process events...")
        logger.info("NOTE: Spark streaming jobs must be running for this step to succeed")
        
        clickhouse_data = self.verify_clickhouse_data(max_wait_seconds=120)
        if not clickhouse_data:
            logger.error("Data verification failed - no data found in ClickHouse")
            return False
        
        logger.info("✓ Data successfully processed and stored in ClickHouse")
        logger.info(f"  - Sales metrics: {clickhouse_data['sales_metrics']} records")
        logger.info(f"  - Inventory metrics: {clickhouse_data['inventory_metrics']} records")
        logger.info(f"  - Raw events: {clickhouse_data['raw_events']} records")
        
        # Step 4: Run data quality checks
        logger.info("Step 4: Running data quality checks...")
        quality_ok = self.run_data_quality_checks()
        
        if quality_ok:
            logger.info("✓ All data quality checks passed")
        else:
            logger.warning("Some data quality checks failed - review warnings above")
        
        # Step 5: Generate test report
        logger.info("Step 5: Generating test report...")
        
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "test_events_generated": len(test_events),
            "clickhouse_data_found": clickhouse_data,
            "data_quality_passed": quality_ok,
            "overall_status": "PASSED" if (clickhouse_data and quality_ok) else "PARTIAL" if clickhouse_data else "FAILED"
        }
        
        # Save report to file
        with open("pipeline_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("✓ Test report saved to pipeline_test_report.json")
        logger.info(f"Overall test result: {report['overall_status']}")
        
        return report['overall_status'] == "PASSED"

def main():
    """Main test execution"""
    tester = PipelineTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()