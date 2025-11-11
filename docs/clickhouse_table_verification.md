# ClickHouse Table Verification Guide

This guide provides multiple methods to verify if ClickHouse tables are not empty in your retail inventory management system.

## Quick Verification Methods

### Method 1: Direct SQL Queries via HTTP

```bash
# Check all tables row counts
curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20table%2C%20sum(rows)%20as%20total_rows%20FROM%20system.parts%20WHERE%20database%20%3D%20'retail'%20AND%20active%20GROUP%20BY%20table%20ORDER%20BY%20total_rows%20DESC"

# Check specific table
curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20count(*)%20FROM%20retail.fact_sales"

# Check tables with zero rows
curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20table%2C%20sum(rows)%20as%20total_rows%20FROM%20system.parts%20WHERE%20database%20%3D%20'retail'%20AND%20active%20GROUP%20BY%20table%20HAVING%20total_rows%20%3D%200"
```

### Method 2: Using ClickHouse Client

```bash
# Connect to ClickHouse container
docker exec -it clickhouse clickhouse-client --user default --password clickhouse

# Then run these queries:
USE retail;

-- Check all tables row counts
SELECT 
    table,
    sum(rows) as total_rows,
    formatReadableSize(sum(bytes)) as size
FROM system.parts 
WHERE database = 'retail' AND active
GROUP BY table
ORDER BY total_rows DESC;

-- Check specific table
SELECT count(*) FROM fact_sales;

-- Check empty tables
SELECT 
    table,
    sum(rows) as total_rows
FROM system.parts 
WHERE database = 'retail' AND active
GROUP BY table
HAVING total_rows = 0;
```

### Method 3: Python Script

We've created a comprehensive Python script that provides multiple verification methods:

```bash
python scripts/check_clickhouse_tables.py
```

## Advanced Verification Queries

### Check Data Freshness
```sql
-- Latest data in each table
SELECT 
    table,
    max(modification_time) as last_modified
FROM system.parts 
WHERE database = 'retail' AND active
GROUP BY table
ORDER BY last_modified DESC;
```

### Check Partition Information
```sql
-- Partition details for fact tables
SELECT 
    table,
    partition,
    sum(rows) as rows,
    min(min_date) as min_date,
    max(max_date) as max_date
FROM system.parts 
WHERE database = 'retail' 
  AND table LIKE 'fact_%'
  AND active
GROUP BY table, partition
ORDER BY table, partition;
```

### Check Data Quality Metrics
```sql
-- Data quality checks for key tables
SELECT 
    'fact_sales' as table_name,
    count(*) as total_rows,
    count(DISTINCT sale_id) as unique_sales,
    min(transaction_time) as earliest_sale,
    max(transaction_time) as latest_sale,
    avg(revenue) as avg_revenue
FROM retail.fact_sales

UNION ALL

SELECT 
    'fact_inventory' as table_name,
    count(*) as total_rows,
    count(DISTINCT inventory_id) as unique_inventory,
    min(last_updated) as earliest_update,
    max(last_updated) as latest_update,
    avg(quantity_on_hand) as avg_stock
FROM retail.fact_inventory;
```

## Automated Monitoring

### Create a Monitoring View
```sql
-- Create a monitoring view in ClickHouse
CREATE VIEW IF NOT EXISTS retail.table_monitoring AS
SELECT 
    database,
    table,
    sum(rows) as total_rows,
    formatReadableSize(sum(bytes)) as table_size,
    count() as partitions,
    max(modification_time) as last_updated,
    if(total_rows > 0, 'HAS_DATA', 'EMPTY') as status
FROM system.parts 
WHERE database = 'retail' AND active
GROUP BY database, table
ORDER BY total_rows DESC;
```

### Query the Monitoring View
```sql
SELECT * FROM retail.table_monitoring;
```

## Common Issues and Solutions

### Issue: Tables Exist But Are Empty
**Solution**: Check if data generation is running:
```bash
# Check data generator container
docker ps | grep data-generator

# Check logs
docker logs data-generator

# Manually trigger data generation
docker exec data-generator python scripts/data_generator.py
```

### Issue: Kafka Events Not Processing
**Solution**: Verify Kafka and Spark streaming:
```bash
# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check Spark jobs
curl -s http://localhost:8082 | grep -i "running"
```

### Issue: ClickHouse Connection Problems
**Solution**: Test connectivity:
```bash
# Test basic connectivity
curl -s "http://default:clickhouse@localhost:8123/ping"

# Check container health
docker ps | grep clickhouse

# Check logs
docker logs clickhouse
```

## Scheduled Monitoring

### Using Airflow DAG
Add this to your existing data quality DAG to schedule regular table checks:

```python
# Add this task to dags/data_quality_dag.py
check_table_health = BashOperator(
    task_id='check_table_health',
    bash_command='python /opt/airflow/dags/scripts/check_clickhouse_tables.py',
    dag=dag
)
```

### Cron Job Alternative
```bash
# Add to crontab for hourly checks
0 * * * * /path/to/python /Users/yusef/M3/big-data/scripts/check_clickhouse_tables.py >> /var/log/clickhouse_monitoring.log
```

## Alerting

Set up alerts for critical tables being empty:

```python
# In your monitoring script, add alert logic
CRITICAL_TABLES = ['fact_sales', 'fact_inventory', 'dim_product', 'dim_store']

for table in CRITICAL_TABLES:
    row_count = verifier.check_table_row_count(table)
    if row_count == 0:
        print(f"🚨 ALERT: Critical table {table} is empty!")
        # Add email/Slack notification here
```

This comprehensive approach ensures you can effectively monitor and verify your ClickHouse table data at any time.