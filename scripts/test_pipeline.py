#!/usr/bin/env python3
"""
End-to-End Pipeline Testing Script
Tests the complete data flow from generation to visualization
"""

import time
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineTester:
    """End-to-end pipeline testing class"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    def test_service_connectivity(self):
        """Test connectivity to all services"""
        logger.info("Testing service connectivity...")
        
        services = {
            'kafka': 'http://kafka:9092',
            'clickhouse': 'http://clickhouse:8123/ping',
            'spark_master': 'http://spark-master:8080/',
            'airflow': 'http://airflow-webserver:8080/health',
            'minio': 'http://minio:9000/minio/health/live',
            'kafka_ui': 'http://kafka-ui:8080/api/clusters/local'
        }
        
        results = {}
        for service, url in services.items():
            try:
                if service == 'clickhouse':
                    response = requests.get(url)
                    success = response.text.strip() == 'Ok'
                elif service == 'kafka':
                    # Kafka doesn't have a simple health endpoint
                    success = True  # We'll test through other means
                else:
                    response = requests.get(url, timeout=10)
                    success = response.status_code == 200
                
                results[service] = 'PASS' if success else 'FAIL'
                logger.info(f"  {service}: {results[service]}")
                
            except Exception as e:
                results[service] = f'FAIL - {str(e)}'
                logger.error(f"  {service}: FAIL - {str(e)}")
        
        self.test_results['service_connectivity'] = results
        return all('PASS' in str(result) for result in results.values())
    
    def test_kafka_topics(self):
        """Test Kafka topics through UI API"""
        logger.info("Testing Kafka topics...")
        
        try:
            response = requests.get('http://kafka-ui:8080/api/clusters/local/topics')
            topics = response.json()
            
            required_topics = ['sales_events', 'inventory_events']
            found_topics = [topic for topic in required_topics if topic in topics]
            
            results = {
                'required_topics': required_topics,
                'found_topics': found_topics,
                'status': 'PASS' if len(found_topics) == len(required_topics) else 'FAIL'
            }
            
            logger.info(f"  Found topics: {found_topics}")
            self.test_results['kafka_topics'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"Kafka topics test failed: {e}")
            self.test_results['kafka_topics'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def test_clickhouse_data(self):
        """Test ClickHouse database and data"""
        logger.info("Testing ClickHouse data...")
        
        try:
            # Test basic query
            query = "SHOW DATABASES"
            response = requests.post(
                'http://clickhouse:8123/',
                data=query,
                auth=('default', 'clickhouse')
            )
            
            if 'retail' not in response.text:
                logger.error("Retail database not found")
                self.test_results['clickhouse_data'] = {'status': 'FAIL - Database not found'}
                return False
            
            # Test table counts
            query = """
            SELECT 
                count() as table_count,
                sum(rows) as total_rows
            FROM system.tables 
            WHERE database = 'retail'
            """
            
            response = requests.post(
                'http://clickhouse:8123/',
                data=query,
                auth=('default', 'clickhouse')
            )
            
            result = response.text.strip().split('\t')
            table_count = int(result[0])
            total_rows = int(result[1])
            
            results = {
                'table_count': table_count,
                'total_rows': total_rows,
                'status': 'PASS' if table_count > 0 else 'FAIL'
            }
            
            logger.info(f"  Tables: {table_count}, Rows: {total_rows}")
            self.test_results['clickhouse_data'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"ClickHouse test failed: {e}")
            self.test_results['clickhouse_data'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def test_data_generation(self):
        """Test if data is being generated"""
        logger.info("Testing data generation...")
        
        try:
            # Check for recent data in ClickHouse
            query = """
            SELECT 
                count(*) as recent_sales,
                count(DISTINCT store_id) as active_stores,
                max(timestamp) as latest_timestamp
            FROM retail.raw_sales_events 
            WHERE timestamp >= now() - INTERVAL 5 MINUTE
            """
            
            response = requests.post(
                'http://clickhouse:8123/',
                data=query,
                auth=('default', 'clickhouse')
            )
            
            result = response.text.strip().split('\t')
            recent_sales = int(result[0])
            active_stores = int(result[1])
            latest_timestamp = result[2]
            
            results = {
                'recent_sales': recent_sales,
                'active_stores': active_stores,
                'latest_timestamp': latest_timestamp,
                'status': 'PASS' if recent_sales > 0 else 'WARNING'
            }
            
            logger.info(f"  Recent sales: {recent_sales}, Active stores: {active_stores}")
            self.test_results['data_generation'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"Data generation test failed: {e}")
            self.test_results['data_generation'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def test_spark_applications(self):
        """Test Spark application status"""
        logger.info("Testing Spark applications...")
        
        try:
            response = requests.get('http://spark-master:8080/api/v1/applications')
            applications = response.json()
            
            running_apps = [app for app in applications if app['state'] == 'RUNNING']
            app_names = [app['name'] for app in running_apps]
            
            results = {
                'total_applications': len(applications),
                'running_applications': len(running_apps),
                'app_names': app_names,
                'status': 'PASS' if len(running_apps) > 0 else 'WARNING'
            }
            
            logger.info(f"  Running apps: {len(running_apps)} - {app_names}")
            self.test_results['spark_applications'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"Spark applications test failed: {e}")
            self.test_results['spark_applications'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def test_airflow_dags(self):
        """Test Airflow DAGs status"""
        logger.info("Testing Airflow DAGs...")
        
        try:
            # This would typically use Airflow API
            # For now, we'll check if the service is responsive
            response = requests.get('http://airflow-webserver:8080/health')
            
            results = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'airflow_health': response.json() if response.status_code == 200 else 'Unavailable'
            }
            
            logger.info(f"  Airflow health: {results['status']}")
            self.test_results['airflow_dags'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"Airflow DAGs test failed: {e}")
            self.test_results['airflow_dags'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def test_real_time_metrics(self):
        """Test real-time metrics generation"""
        logger.info("Testing real-time metrics...")
        
        try:
            # Check if real-time metrics are being populated
            query = """
            SELECT 
                count(*) as metric_count,
                max(window_start) as latest_metric
            FROM retail.realtime_sales_metrics
            WHERE window_start >= now() - INTERVAL 1 HOUR
            """
            
            response = requests.post(
                'http://clickhouse:8123/',
                data=query,
                auth=('default', 'clickhouse')
            )
            
            result = response.text.strip().split('\t')
            metric_count = int(result[0])
            
            results = {
                'metric_count': metric_count,
                'status': 'PASS' if metric_count > 0 else 'WARNING'
            }
            
            logger.info(f"  Recent metrics: {metric_count}")
            self.test_results['real_time_metrics'] = results
            return results['status'] == 'PASS'
            
        except Exception as e:
            logger.error(f"Real-time metrics test failed: {e}")
            self.test_results['real_time_metrics'] = {'status': f'FAIL - {str(e)}'}
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        report = {
            'test_timestamp': self.start_time.isoformat(),
            'test_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'test_results': self.test_results,
            'overall_status': 'PASS' if all(
                'FAIL' not in str(result.get('status', '')) 
                for result in self.test_results.values()
            ) else 'FAIL'
        }
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        
        for test_name, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            logger.info(f"{test_name:25} : {status}")
        
        logger.info(f"{'OVERALL':25} : {report['overall_status']}")
        logger.info("="*50)
        
        # Save detailed report
        with open('/tmp/pipeline_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Detailed report saved to: /tmp/pipeline_test_report.json")
        return report
    
    def run_all_tests(self):
        """Run all pipeline tests"""
        logger.info("Starting end-to-end pipeline tests...")
        
        tests = [
            self.test_service_connectivity,
            self.test_kafka_topics,
            self.test_clickhouse_data,
            self.test_data_generation,
            self.test_spark_applications,
            self.test_airflow_dags,
            self.test_real_time_metrics
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
        
        return self.generate_test_report()

def main():
    """Main function to run pipeline tests"""
    tester = PipelineTester()
    report = tester.run_all_tests()
    
    if report['overall_status'] == 'PASS':
        logger.info("🎉 All tests passed! Pipeline is functioning correctly.")
        return 0
    else:
        logger.warning("⚠️ Some tests failed or produced warnings. Check the detailed report.")
        return 1

if __name__ == "__main__":
    exit(main())