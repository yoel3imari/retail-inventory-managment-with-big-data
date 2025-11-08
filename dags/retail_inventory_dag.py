"""
Airflow DAG for Retail Inventory Management
Orchestrates the complete data pipeline including:
- Data generation and streaming
- Real-time processing
- ML model training
- Batch processing and reporting
"""

from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'retail_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'retail_inventory_pipeline',
    default_args=default_args,
    description='Complete retail inventory management pipeline',
    schedule_interval=timedelta(hours=1),  # Run hourly
    catchup=False,
    tags=['retail', 'inventory', 'bigdata'],
)

# Task definitions

# Start of pipeline
start_pipeline = DummyOperator(
    task_id='start_pipeline',
    dag=dag,
)

# Check infrastructure health
check_infrastructure = BashOperator(
    task_id='check_infrastructure',
    bash_command="""
    echo "Checking infrastructure health..."
    curl -f http://kafka:9092 || exit 1
    curl -f http://clickhouse:8123/ping || exit 1
    curl -f http://spark-master:8080/ || exit 1
    echo "All services are healthy"
    """,
    dag=dag,
)

# Start data generator (if not already running)
start_data_generator = BashOperator(
    task_id='start_data_generator',
    bash_command="""
    echo "Starting data generator..."
    docker-compose up -d data-generator
    sleep 10
    echo "Data generator started"
    """,
    dag=dag,
)

# Submit Spark streaming jobs
submit_sales_streaming = SparkSubmitOperator(
    task_id='submit_sales_streaming',
    application='/opt/airflow/dags/spark_jobs/sales_streaming.py',
    name='retail_sales_streaming',
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.sql.adaptive.enabled': 'true',
        'spark.streaming.backpressure.enabled': 'true',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '1g',
    },
    dag=dag,
)

submit_inventory_streaming = SparkSubmitOperator(
    task_id='submit_inventory_streaming',
    application='/opt/airflow/dags/spark_jobs/inventory_streaming.py',
    name='retail_inventory_streaming',
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.sql.adaptive.enabled': 'true',
        'spark.streaming.backpressure.enabled': 'true',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '1g',
    },
    dag=dag,
)

# Daily ML training (runs once per day)
train_ml_models = SparkSubmitOperator(
    task_id='train_ml_models',
    application='/opt/airflow/dags/spark_jobs/ml_training.py',
    name='retail_ml_training',
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.sql.adaptive.enabled': 'true',
        'spark.driver.memory': '2g',
        'spark.executor.memory': '2g',
    },
    dag=dag,
)

# Batch processing (runs every 6 hours)
run_batch_processing = SparkSubmitOperator(
    task_id='run_batch_processing',
    application='/opt/airflow/dags/spark_jobs/batch_processing.py',
    name='retail_batch_processing',
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.sql.adaptive.enabled': 'true',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '1g',
    },
    dag=dag,
)

# Data quality checks
run_data_quality_checks = BashOperator(
    task_id='run_data_quality_checks',
    bash_command="""
    echo "Running data quality checks..."
    # Check if ClickHouse has data
    curl -s -u default:clickhouse -X POST -d "
    SELECT 
        COUNT(*) as total_sales,
        COUNT(DISTINCT store_id) as active_stores,
        COUNT(DISTINCT product_id) as active_products
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    " http://clickhouse:8123/
    echo "Data quality checks completed"
    """,
    dag=dag,
)

# Generate business report
generate_business_report = BashOperator(
    task_id='generate_business_report',
    bash_command="""
    echo "Generating business report..."
    # Generate report using ClickHouse queries
    curl -s -u default:clickhouse -X POST -d "
    SELECT 
        toStartOfHour(now()) as report_time,
        COUNT(*) as hourly_transactions,
        SUM(total_amount) as hourly_revenue,
        COUNT(DISTINCT customer_id) as unique_customers,
        AVG(total_amount) as avg_transaction_value
    FROM retail.raw_sales_events 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    " http://clickhouse:8123/ > /tmp/hourly_report.json
    echo "Business report generated"
    """,
    dag=dag,
)

# Monitor pipeline health
monitor_pipeline_health = BashOperator(
    task_id='monitor_pipeline_health',
    bash_command="""
    echo "Monitoring pipeline health..."
    # Check Kafka topics
    curl -s http://kafka-ui:8080/api/clusters/local/topics | grep -q sales_events && echo "Kafka topics OK" || echo "Kafka topics issue"
    
    # Check Spark applications
    curl -s http://spark-master:8080/api/v1/applications | grep -q RUNNING && echo "Spark apps OK" || echo "Spark apps issue"
    
    # Check ClickHouse tables
    curl -s -u default:clickhouse -X POST -d "
    SELECT count() FROM system.tables WHERE database = 'retail'
    " http://clickhouse:8123/ | grep -q [0-9] && echo "ClickHouse OK" || echo "ClickHouse issue"
    
    echo "Pipeline health monitoring completed"
    """,
    dag=dag,
)

# End of pipeline
end_pipeline = DummyOperator(
    task_id='end_pipeline',
    dag=dag,
)

# Define task dependencies
start_pipeline >> check_infrastructure

# Parallel streaming tasks
check_infrastructure >> [submit_sales_streaming, submit_inventory_streaming]

# ML training runs independently (once per day)
check_infrastructure >> train_ml_models

# Batch processing depends on streaming data
[submit_sales_streaming, submit_inventory_streaming] >> run_batch_processing

# Data quality and reporting
run_batch_processing >> run_data_quality_checks
run_data_quality_checks >> generate_business_report

# Final monitoring
[generate_business_report, train_ml_models] >> monitor_pipeline_health
monitor_pipeline_health >> end_pipeline

# Additional DAG for daily operations
daily_dag = DAG(
    'retail_daily_operations',
    default_args=default_args,
    description='Daily retail operations and reporting',
    schedule_interval=timedelta(days=1),  # Run daily
    catchup=False,
    tags=['retail', 'daily', 'reporting'],
)

# Daily tasks
daily_start = DummyOperator(
    task_id='daily_start',
    dag=daily_dag,
)

# Generate comprehensive daily report
generate_daily_report = SparkSubmitOperator(
    task_id='generate_daily_report',
    application='/opt/airflow/dags/spark_jobs/batch_processing.py',
    name='retail_daily_report',
    conn_id='spark_default',
    verbose=True,
    dag=daily_dag,
)

# Archive old data
archive_old_data = BashOperator(
    task_id='archive_old_data',
    bash_command="""
    echo "Archiving old data..."
    # Archive data older than 30 days to cold storage
    curl -s -u default:clickhouse -X POST -d "
    ALTER TABLE retail.raw_sales_events 
    DROP PARTITION WHERE timestamp < today() - INTERVAL 30 DAY
    " http://clickhouse:8123/
    echo "Old data archived"
    """,
    dag=daily_dag,
)

# Update ML models
update_ml_models = SparkSubmitOperator(
    task_id='update_ml_models',
    application='/opt/airflow/dags/spark_jobs/ml_training.py',
    name='retail_ml_update',
    conn_id='spark_default',
    verbose=True,
    dag=daily_dag,
)

daily_end = DummyOperator(
    task_id='daily_end',
    dag=daily_dag,
)

# Daily DAG dependencies
daily_start >> generate_daily_report
generate_daily_report >> [archive_old_data, update_ml_models]
[archive_old_data, update_ml_models] >> daily_end

if __name__ == "__main__":
    dag.cli()