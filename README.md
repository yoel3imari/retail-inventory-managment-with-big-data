# 🏪 Retail Inventory Big Data Analysis Project

An educational project demonstrating real-world big data architecture for retail inventory management using Kafka, ClickHouse, and MinIO.

## 📋 Project Overview

This project simulates a retail chain's data infrastructure, processing real-time inventory updates, sales transactions, and stock movements to provide actionable insights.

### Learning Objectives
- **Stream Processing**: Real-time data ingestion with Kafka
- **Analytics Database**: OLAP queries with ClickHouse
- **Data Lake**: Object storage with MinIO
- **ETL Pipelines**: Data transformation and loading
- **Big Data Architecture**: Lambda/Kappa architecture patterns

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Retail    │      │    Kafka    │      │ ClickHouse  │
│   Stores    │─────▶│  (Streams)  │─────▶│ (Analytics) │
│   (Events)  │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
                            │                     │
                            │                     │
                            ▼                     ▼
                     ┌─────────────┐      ┌─────────────┐
                     │    MinIO    │      │   Jupyter   │
                     │ (Data Lake) │      │  (Analysis) │
                     └─────────────┘      └─────────────┘
```

### Data Flow
1. **Data Generation**: Python script generates realistic retail events
2. **Streaming**: Kafka topics handle real-time data streams
3. **Storage**: MinIO stores raw data and backups
4. **Analytics**: ClickHouse processes queries for insights
5. **Visualization**: Jupyter notebooks for analysis

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- At least 8GB RAM available
- 10GB free disk space

### One-Click Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd retail-inventory-managment-with-big-data
```

2. **Start all services and initialize**:
```bash
# Start services and run automated bootstrap
./scripts/bootstrap.sh
```

3. **Verify services are running**:
```bash
docker-compose ps
```

### Manual Setup (Alternative)

1. **Start services**:
```bash
docker-compose up -d
```

2. **Wait for services to be ready** (30-60 seconds):
```bash
docker-compose ps
```

3. **Initialize data and infrastructure**:
```bash
# Create sample dimension data
docker exec data-generator python scripts/create_sample_data.py

# Start data generation
docker exec data-generator python scripts/data_generator.py --duration 60 --rate 10
```

4. **Submit Spark streaming jobs**:
```bash
# Submit unified streaming bridge (recommended)
docker exec spark-master ./submit_jobs.sh unified

# Or submit individual jobs
docker exec spark-master ./submit_jobs.sh sales
docker exec spark-master ./submit_jobs.sh inventory
```

## 📊 Using the System

### 1. Access Web Interfaces

| Service | URL | Port | Credentials | Purpose |
|---------|-----|------|-------------|---------|
| **MinIO Console** | http://localhost:9001 | 9001 | minioadmin/minioadmin | Object storage management |
| **Kafka UI** | http://localhost:8080 | 8080 | None | Monitor Kafka topics and messages |
| **Spark Master UI** | http://localhost:8082 | 8082 | None | Monitor Spark applications |
| **ClickHouse HTTP** | http://localhost:8123 | 8123 | default/clickhouse | Database HTTP interface |
| **Airflow** | http://localhost:8081 | 8081 | airflow/airflow | Workflow orchestration |

### 2. Verify Kafka Topics (Automatically Created)

The bootstrap script automatically creates the following Kafka topics:

- `retail-sales-transactions` - Sales events and transactions
- `retail-inventory-updates` - Inventory level changes
- `retail-restock-alerts` - Low stock and restock notifications
- `retail-price-changes` - Pricing updates
- `retail-customer-events` - Customer behavior events

**Check existing topics**:
```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### 3. Generate Sample Data

```bash
# Generate dimension data (stores, products, categories)
docker exec data-generator python scripts/create_sample_data.py

# Start real-time data generation
docker exec data-generator python scripts/data_generator.py --duration 60 --rate 10
```

**Data Generation Options**:
- `--duration 60`: Run for 60 minutes
- `--rate 10`: Generate 10 events per minute
- `--stores 10`: Override number of stores
- `--products 100`: Override number of products

### 4. Consume Kafka Messages

```bash
# Watch sales transactions
docker exec -it kafka kafka-console-consumer \
  --topic retail-sales-transactions \
  --bootstrap-server localhost:9092 \
  --from-beginning --max-messages 5

# Watch inventory updates
docker exec -it kafka kafka-console-consumer \
  --topic retail-inventory-updates \
  --bootstrap-server localhost:9092 \
  --from-beginning --max-messages 5
```

### 5. Query ClickHouse

```bash
# Enter ClickHouse client
docker exec -it clickhouse clickhouse-client --password clickhouse

# Run queries
USE retail;

-- Check tables
SHOW TABLES;

-- View real-time sales metrics
SELECT * FROM spark_sales_metrics LIMIT 10;

-- View inventory metrics and alerts
SELECT * FROM spark_inventory_metrics WHERE stock_status != 'IN_STOCK' LIMIT 10;

-- Top selling products (from fact tables)
SELECT
    p.product_name,
    COUNT(s.sale_id) as transaction_count,
    SUM(s.total_amount) as total_revenue
FROM fact_sales s
JOIN dim_product p ON s.product_key = p.product_key
WHERE s.transaction_time >= today()
GROUP BY p.product_name
ORDER BY total_revenue DESC
LIMIT 10;

-- Sales by hour (from streaming metrics)
SELECT
    window_start,
    store_id,
    total_revenue,
    transaction_count
FROM spark_sales_metrics
ORDER BY window_start DESC
LIMIT 10;
```

## 📚 Learning Exercises

### Exercise 1: Real-time Dashboard
Create a query that shows current inventory status across all stores.

### Exercise 2: Sales Analytics
Calculate daily sales trends, best-performing categories, and revenue forecasts.

### Exercise 3: Stock Optimization
Identify slow-moving products and recommend reorder quantities.

### Exercise 4: ETL Pipeline
Build a pipeline to load data from Kafka → ClickHouse → MinIO (backup).

### Exercise 5: Anomaly Detection
Detect unusual sales patterns or inventory discrepancies.

## 🔍 Sample Queries

### Real-time Sales Analytics
```sql
-- Current hour sales performance
SELECT
    store_id,
    SUM(total_revenue) as hourly_revenue,
    SUM(transaction_count) as hourly_transactions,
    AVG(avg_unit_price) as avg_price
FROM spark_sales_metrics
WHERE window_start >= now() - INTERVAL 1 HOUR
GROUP BY store_id
ORDER BY hourly_revenue DESC;
```

### Inventory Status Dashboard
```sql
-- Current inventory status across stores
SELECT
    store_id,
    COUNT(*) as products,
    SUM(CASE WHEN stock_status = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) as out_of_stock,
    SUM(CASE WHEN stock_status = 'LOW_STOCK' THEN 1 ELSE 0 END) as low_stock,
    AVG(stock_percentage) as avg_stock_level
FROM spark_inventory_metrics
WHERE window_start >= now() - INTERVAL 1 HOUR
GROUP BY store_id
ORDER BY out_of_stock DESC;
```

### Product Performance Analysis
```sql
-- Top performing products with inventory status
SELECT
    p.product_name,
    p.category,
    sm.total_revenue,
    sm.transaction_count,
    im.latest_stock,
    im.stock_status
FROM spark_sales_metrics sm
JOIN spark_inventory_metrics im ON sm.store_id = im.store_id AND sm.product_id = im.product_id
JOIN dim_product p ON sm.product_id = p.sku
WHERE sm.window_start >= now() - INTERVAL 1 DAY
ORDER BY sm.total_revenue DESC
LIMIT 20;
```

## 🛠️ Advanced Features

### Connect to MinIO from Python
```python
from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Create bucket
client.make_bucket("retail-data")

# Upload file
client.fput_object("retail-data", "sales.csv", "/path/to/sales.csv")
```

### Unified Streaming Bridge
The project includes a unified Spark streaming bridge that processes both sales and inventory events:

```bash
# Submit the unified streaming bridge
docker exec spark-master ./submit_jobs.sh unified

# This processes:
# - retail-sales-transactions → spark_sales_metrics
# - retail-inventory-updates → spark_inventory_metrics
# - Generates unified alerts → streaming_alerts
```

### Pipeline Testing
Test the complete data pipeline:

```bash
# Run comprehensive pipeline test
python scripts/test_spark_clickhouse_bridge.py

# Check ClickHouse table data
python scripts/check_clickhouse_tables.py
```

## 📦 Data Volumes

The system generates approximately:
- **Sales**: 120 transactions/minute
- **Inventory Updates**: 60 updates/minute
- **Stock Movements**: 20 movements/minute

This creates realistic data volumes for learning big data concepts.

## 🔧 Troubleshooting

### Kafka not accepting connections
```bash
docker-compose restart kafka
docker-compose logs -f kafka
```

### ClickHouse queries slow
```bash
# Check table sizes
docker exec -it clickhouse clickhouse-client --password clickhouse \
  -q "SELECT table, formatReadableSize(sum(bytes)) as size FROM system.parts GROUP BY table"
```

### Out of memory
Reduce the data generation rate or allocate more RAM to Docker.

## 📖 Additional Resources

- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)

## 🎓 Next Steps

1. Implement data visualization with Grafana
2. Add Apache Spark for batch processing
3. Set up dbt for data transformations
4. Create real-time alerts with Apache Flink
5. Deploy on cloud (AWS, Azure, GCP)

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove all data volumes (CAUTION: deletes all data)
docker-compose down -v
```

---

**Happy Learning! 🚀**