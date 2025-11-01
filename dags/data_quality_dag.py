"""
Data Quality Monitoring DAG for Retail Inventory Management
Monitors data quality, detects anomalies, and ensures pipeline health
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data_quality_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'data_quality_monitoring',
    default_args=default_args,
    description='Data quality monitoring and anomaly detection',
    schedule_interval=timedelta(minutes=30),  # Run every 30 minutes
    catchup=False,
    tags=['data-quality', 'monitoring', 'retail'],
)

def check_data_freshness():
    """Check if data is being generated and processed in real-time"""
    import requests
    
    # Check ClickHouse for recent data
    query = """
    SELECT 
        COUNT(*) as recent_sales,
        COUNT(DISTINCT store_id) as active_stores,
        MAX(timestamp) as latest_timestamp,
        now() - MAX(timestamp) as data_lag_seconds
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    """
    
    try:
        response = requests.post(
            'http://clickhouse:8123/',
            data=query,
            auth=('default', 'clickhouse')
        )
        result = response.text.strip().split('\t')
        
        recent_sales = int(result[0])
        data_lag = int(result[3])
        
        print(f"Recent sales: {recent_sales}")
        print(f"Data lag: {data_lag} seconds")
        
        if recent_sales == 0:
            raise Exception("No recent sales data detected")
            
        if data_lag > 300:  # 5 minutes lag
            raise Exception(f"Data lag too high: {data_lag} seconds")
            
        print("Data freshness check passed")
        
    except Exception as e:
        print(f"Data freshness check failed: {e}")
        raise

def check_data_completeness():
    """Check for missing data and data gaps"""
    import requests
    
    query = """
    SELECT 
        store_id,
        COUNT(*) as record_count,
        MIN(timestamp) as first_record,
        MAX(timestamp) as last_record
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    GROUP BY store_id
    HAVING record_count = 0
    """
    
    try:
        response = requests.post(
            'http://clickhouse:8123/',
            data=query,
            auth=('default', 'clickhouse')
        )
        
        missing_stores = response.text.strip().split('\n')
        
        if len(missing_stores) > 1:  # Header + data
            raise Exception(f"Missing data from stores: {missing_stores[1:]}")
            
        print("Data completeness check passed")
        
    except Exception as e:
        print(f"Data completeness check failed: {e}")
        raise

def check_data_consistency():
    """Check data consistency and business rules"""
    import requests
    
    # Check for negative quantities or prices
    query = """
    SELECT 
        COUNT(*) as invalid_records
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    AND (quantity <= 0 OR unit_price <= 0 OR total_amount <= 0)
    """
    
    try:
        response = requests.post(
            'http://clickhouse:8123/',
            data=query,
            auth=('default', 'clickhouse')
        )
        
        invalid_count = int(response.text.strip())
        
        if invalid_count > 0:
            raise Exception(f"Found {invalid_count} invalid records")
            
        print("Data consistency check passed")
        
    except Exception as e:
        print(f"Data consistency check failed: {e}")
        raise

def check_kafka_health():
    """Check Kafka cluster health and topic status"""
    import requests
    
    try:
        # Check Kafka UI API for cluster health
        response = requests.get('http://kafka-ui:8080/api/clusters/local')
        cluster_info = response.json()
        
        if cluster_info['status'] != 'HEALTHY':
            raise Exception(f"Kafka cluster status: {cluster_info['status']}")
            
        # Check topic status
        response = requests.get('http://kafka-ui:8080/api/clusters/local/topics')
        topics = response.json()
        
        required_topics = ['sales_events', 'inventory_events']
        missing_topics = [topic for topic in required_topics if topic not in topics]
        
        if missing_topics:
            raise Exception(f"Missing topics: {missing_topics}")
            
        print("Kafka health check passed")
        
    except Exception as e:
        print(f"Kafka health check failed: {e}")
        raise

def check_clickhouse_health():
    """Check ClickHouse database health and performance"""
    import requests
    
    try:
        # Check basic connectivity
        response = requests.get('http://clickhouse:8123/ping')
        if response.text != 'Ok\n':
            raise Exception("ClickHouse ping failed")
            
        # Check table counts
        query = """
        SELECT 
            database,
            count() as table_count,
            sum(bytes) as total_bytes,
            sum(rows) as total_rows
        FROM system.tables 
        WHERE database = 'retail'
        GROUP BY database
        """
        
        response = requests.post(
            'http://clickhouse:8123/',
            data=query,
            auth=('default', 'clickhouse')
        )
        
        result = response.text.strip().split('\t')
        table_count = int(result[1])
        
        if table_count == 0:
            raise Exception("No tables found in retail database")
            
        print("ClickHouse health check passed")
        
    except Exception as e:
        print(f"ClickHouse health check failed: {e}")
        raise

def generate_quality_report():
    """Generate data quality report"""
    import requests
    import json
    
    query = """
    SELECT 
        toStartOfHour(now()) as report_time,
        COUNT(*) as total_records,
        COUNT(DISTINCT store_id) as store_count,
        COUNT(DISTINCT product_id) as product_count,
        COUNT(DISTINCT customer_id) as customer_count,
        AVG(quantity) as avg_quantity,
        AVG(unit_price) as avg_unit_price,
        SUM(total_amount) as total_revenue,
        MIN(timestamp) as earliest_record,
        MAX(timestamp) as latest_record
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    """
    
    try:
        response = requests.post(
            'http://clickhouse:8123/',
            data=query,
            auth=('default', 'clickhouse')
        )
        
        result = response.text.strip().split('\t')
        
        quality_report = {
            'report_timestamp': datetime.now().isoformat(),
            'total_records': int(result[1]),
            'store_count': int(result[2]),
            'product_count': int(result[3]),
            'customer_count': int(result[4]),
            'avg_quantity': float(result[5]),
            'avg_unit_price': float(result[6]),
            'total_revenue': float(result[7]),
            'data_freshness_seconds': (datetime.now() - datetime.fromisoformat(result[9].replace(' ', 'T'))).total_seconds()
        }
        
        print("Data Quality Report:")
        for key, value in quality_report.items():
            print(f"  {key}: {value}")
            
        # Save report to file (in production, this would go to a database)
        with open('/tmp/data_quality_report.json', 'w') as f:
            json.dump(quality_report, f, indent=2)
            
    except Exception as e:
        print(f"Failed to generate quality report: {e}")
        raise

# Task definitions
start_monitoring = DummyOperator(
    task_id='start_monitoring',
    dag=dag,
)

check_data_freshness_task = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    dag=dag,
)

check_data_completeness_task = PythonOperator(
    task_id='check_data_completeness',
    python_callable=check_data_completeness,
    dag=dag,
)

check_data_consistency_task = PythonOperator(
    task_id='check_data_consistency',
    python_callable=check_data_consistency,
    dag=dag,
)

check_kafka_health_task = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag,
)

check_clickhouse_health_task = PythonOperator(
    task_id='check_clickhouse_health',
    python_callable=check_clickhouse_health,
    dag=dag,
)

generate_quality_report_task = PythonOperator(
    task_id='generate_quality_report',
    python_callable=generate_quality_report,
    dag=dag,
)

end_monitoring = DummyOperator(
    task_id='end_monitoring',
    dag=dag,
)

# Task dependencies
start_monitoring >> [
    check_data_freshness_task,
    check_data_completeness_task, 
    check_data_consistency_task,
    check_kafka_health_task,
    check_clickhouse_health_task
]

[
    check_data_freshness_task,
    check_data_completeness_task,
    check_data_consistency_task,
    check_kafka_health_task,
    check_clickhouse_health_task
] >> generate_quality_report_task

generate_quality_report_task >> end_monitoring

if __name__ == "__main__":
    dag.cli()