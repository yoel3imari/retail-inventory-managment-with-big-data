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

### Setup

1. **Create project structure**:

2. **Save the Docker Compose file** as `docker-compose.yml`

3. **Save the ClickHouse schema** as `clickhouse/init/01-schema.sql`

4. **Save the data generator script** as `scripts/generate_data.py`

5. **Start all services**:
```bash
docker-compose up -d
```

6. **Wait for services to be ready** (30-60 seconds):
```bash
docker-compose ps
```

## 📊 Using the System

### 1. Access Web Interfaces

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka UI**: http://localhost:8080
- **Jupyter Notebook**: http://localhost:8888 (token: retail123)
- **ClickHouse HTTP**: http://localhost:8123

### 2. Create Kafka Topics

```bash
docker exec -it kafka kafka-topics --create \
  --topic retail-sales \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1

docker exec -it kafka kafka-topics --create \
  --topic retail-inventory-updates \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1

docker exec -it kafka kafka-topics --create \
  --topic retail-stock-movements \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1
```

### 3. Generate Sample Data

```bash
# Enter the data generator container
docker exec -it data-generator bash

# Run the generator
cd /app
python generate_data.py
```

Select option `4` to generate all types of events.

### 4. Consume Kafka Messages

```bash
# Watch sales transactions
docker exec -it kafka kafka-console-consumer \
  --topic retail-sales \
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

-- View low stock alerts
SELECT * FROM low_stock_alerts LIMIT 10;

-- Top selling products
SELECT 
    product_name,
    total_units_sold,
    total_revenue,
    profit_margin_pct
FROM product_performance
LIMIT 10;

-- Sales by hour
SELECT 
    toHour(date_hour) as hour,
    sum(total_revenue) as revenue
FROM hourly_sales_metrics
WHERE date_hour >= today()
GROUP BY hour
ORDER BY hour;
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

### Inventory Turnover Rate
```sql
SELECT 
    p.category,
    COUNT(DISTINCT p.product_id) as products,
    SUM(s.quantity_sold) as units_sold,
    AVG(i.quantity_on_hand) as avg_inventory,
    (SUM(s.quantity_sold) / AVG(i.quantity_on_hand)) * 30 as turnover_days
FROM retail.products p
JOIN retail.sales s ON p.product_id = s.product_id
JOIN retail.inventory i ON p.product_id = i.product_id
WHERE s.transaction_time >= now() - INTERVAL 30 DAY
GROUP BY p.category;
```

### Store Performance Comparison
```sql
SELECT 
    store_id,
    COUNT(DISTINCT transaction_id) as transactions,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_transaction,
    SUM(quantity_sold) as units_sold
FROM retail.sales
WHERE transaction_time >= today() - INTERVAL 7 DAY
GROUP BY store_id
ORDER BY revenue DESC;
```

### Stock Movement Analysis
```sql
SELECT 
    movement_type,
    COUNT(*) as movement_count,
    SUM(quantity) as total_quantity,
    AVG(quantity) as avg_quantity
FROM retail.stock_movements
WHERE movement_time >= now() - INTERVAL 7 DAY
GROUP BY movement_type
ORDER BY movement_count DESC;
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

### Stream Data from Kafka to ClickHouse
Use Kafka Engine in ClickHouse for direct consumption:

```sql
CREATE TABLE retail.sales_queue
(
    transaction_id String,
    product_id String,
    -- other fields...
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:19092',
    kafka_topic_list = 'retail-sales',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow';
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