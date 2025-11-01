# Retail Inventory Management with Big Data - Setup Guide

## Overview

This project implements a complete big data pipeline for retail inventory management using modern technologies including Kafka, Spark, ClickHouse, Airflow, and Power BI.

## Prerequisites

### System Requirements
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free disk space
- **CPU**: 4+ cores recommended

### Software Requirements
- Git
- Python 3.8+ (for local development)
- Web browser for accessing UIs

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd retail-inventory-managment-with-big-data
```

### 2. Start the Infrastructure
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Initialize the Database
```bash
# Initialize ClickHouse database
docker exec -it clickhouse bash
cd /docker-entrypoint-initdb.d
./init-database.sh init
```

### 4. Start Data Generation
```bash
# The data generator should start automatically
# Check if it's running
docker-compose logs data-generator
```

### 5. Submit Spark Jobs
```bash
# Submit streaming jobs
docker exec -it spark-master bash
cd /opt/spark/jobs
./submit_jobs.sh all
```

## Service URLs

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| Kafka UI | http://localhost:8080 | 8080 | Kafka management interface |
| Airflow | http://localhost:8081 | 8081 | Workflow orchestration |
| Spark Master | http://localhost:8082 | 8082 | Spark cluster management |
| MinIO Console | http://localhost:9001 | 9001 | Object storage management |
| ClickHouse | http://localhost:8123 | 8123 | Database HTTP interface |

## Detailed Setup Instructions

### Infrastructure Setup

#### 1. Docker Compose Configuration
The `docker-compose.yml` file defines all services:
- **Kafka**: Message streaming platform
- **MinIO**: S3-compatible object storage
- **ClickHouse**: OLAP database for analytics
- **Apache Airflow**: Workflow orchestration
- **Apache Spark**: Distributed processing
- **Data Generator**: Fake data producer

#### 2. Network Configuration
All services are connected to the `dev-network` for internal communication.

#### 3. Volume Mounts
- Data persistence for databases
- Spark job directories
- Airflow DAGs and logs

### Database Setup

#### ClickHouse Initialization
```bash
# Manual initialization
docker exec -it clickhouse clickhouse-client --user default --password clickhouse

# Create database and tables
CREATE DATABASE IF NOT EXISTS retail;
USE retail;

# Execute schema files
SOURCE /docker-entrypoint-initdb.d/01-schema.sql;
SOURCE /docker-entrypoint-initdb.d/02-enhanced-schema.sql;
```

#### Verify Database
```sql
-- Check tables
SHOW TABLES FROM retail;

-- Check sample data
SELECT * FROM retail.dim_product LIMIT 5;
```

### Data Pipeline Setup

#### 1. Start Data Generation
The data generator automatically creates:
- Sales events
- Inventory updates
- Customer activities

```bash
# Monitor data generation
docker-compose logs -f data-generator
```

#### 2. Verify Kafka Topics
```bash
# Check Kafka topics through UI
# Visit http://localhost:8080
# Or use command line
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

Expected topics:
- `sales_events`
- `inventory_events`

#### 3. Submit Spark Jobs
```bash
# Access Spark master
docker exec -it spark-master bash

# Submit individual jobs
./submit_jobs.sh sales
./submit_jobs.sh inventory
./submit_jobs.sh ml
./submit_jobs.sh batch

# Or submit all
./submit_jobs.sh all
```

### Airflow Setup

#### 1. Access Airflow UI
- URL: http://localhost:8081
- Username: `airflow`
- Password: `airflow`

#### 2. Enable DAGs
- Navigate to DAGs page
- Enable `retail_inventory_pipeline`
- Enable `data_quality_monitoring`
- Enable `retail_daily_operations`

#### 3. Configure Connections
- **Spark**: `spark_default` (auto-configured)
- **ClickHouse**: Manual configuration if needed

## Monitoring and Troubleshooting

### Service Health Checks

#### Check All Services
```bash
docker-compose ps
```

#### Check Individual Service Logs
```bash
docker-compose logs <service-name>
# Examples:
docker-compose logs kafka
docker-compose logs spark-master
docker-compose logs data-generator
```

### Data Flow Verification

#### 1. Check Kafka Messages
```bash
# Consume messages from sales topic
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sales_events \
  --from-beginning
```

#### 2. Check ClickHouse Data
```sql
-- Check recent sales
SELECT count(*) FROM retail.raw_sales_events 
WHERE timestamp >= now() - INTERVAL 1 HOUR;

-- Check real-time metrics
SELECT * FROM retail.realtime_dashboard LIMIT 10;
```

#### 3. Check Spark Applications
- Visit Spark UI: http://localhost:8082
- Check running applications
- Monitor executor status

### Common Issues and Solutions

#### 1. Services Not Starting
**Problem**: Docker containers fail to start
**Solution**:
```bash
# Check available resources
docker system df
docker system prune

# Restart services
docker-compose down
docker-compose up -d
```

#### 2. Database Connection Issues
**Problem**: ClickHouse not accessible
**Solution**:
```bash
# Check if ClickHouse is running
docker exec -it clickhouse curl http://localhost:8123/ping

# Restart ClickHouse
docker-compose restart clickhouse
```

#### 3. Spark Job Failures
**Problem**: Spark jobs fail to submit
**Solution**:
```bash
# Check Spark master
curl http://spark-master:8080/

# Check worker connectivity
docker-compose logs spark-worker

# Increase memory if needed
# Edit docker-compose.yml spark-worker environment
```

#### 4. Data Not Flowing
**Problem**: No data in Kafka or ClickHouse
**Solution**:
```bash
# Check data generator
docker-compose logs data-generator

# Check Kafka topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Manually trigger data generation
docker exec -it data-generator python /app/scripts/data_generator.py
```

## Performance Tuning

### Memory Configuration
Edit `docker-compose.yml` for resource allocation:
```yaml
spark-worker:
  environment:
    SPARK_WORKER_MEMORY: 2G
    SPARK_WORKER_CORES: 2
```

### Kafka Configuration
```yaml
kafka:
  environment:
    KAFKA_HEAP_OPTS: "-Xmx1G -Xms1G"
```

### ClickHouse Configuration
```yaml
clickhouse:
  ulimits:
    nofile:
      soft: 262144
      hard: 262144
```

## Development and Customization

### Adding New Data Sources
1. Update data generator in `scripts/data_generator.py`
2. Create new Kafka topic if needed
3. Add Spark streaming job in `spark_jobs/`
4. Update ClickHouse schema
5. Create Airflow DAG for orchestration

### Modifying ML Models
1. Edit `spark_jobs/ml_training.py`
2. Update feature engineering
3. Modify model parameters
4. Test with sample data

### Customizing Dashboards
1. Connect Power BI to ClickHouse
2. Import data model from `powerbi/retail_dashboard.pbix`
3. Modify visuals and measures
4. Publish updated dashboard

## Security Considerations

### Production Deployment
- Change default passwords
- Enable SSL/TLS for services
- Configure firewall rules
- Set up monitoring and alerting
- Implement backup strategies

### Data Privacy
- Anonymize customer data
- Implement access controls
- Encrypt sensitive data
- Regular security audits

## Maintenance

### Regular Tasks
- Monitor disk usage
- Check service logs
- Update software versions
- Backup important data
- Review performance metrics

### Backup Procedures
```bash
# Backup ClickHouse data
docker exec -it clickhouse clickhouse-backup create

# Backup configuration files
tar -czf config-backup.tar.gz docker-compose.yml config/ scripts/
```

## Support and Resources

### Documentation
- Architecture: `AGENT/architecture.md`
- Spark Jobs: `spark_jobs/README.md`
- Database Schema: `clickhouse/init/`

### Monitoring Tools
- **Kafka UI**: Topic monitoring and management
- **Spark UI**: Application monitoring
- **Airflow UI**: Workflow monitoring
- **MinIO Console**: Storage management

### Troubleshooting Resources
- Service logs via `docker-compose logs`
- ClickHouse query logs
- Spark application logs
- Airflow task logs

## Next Steps

After successful setup:
1. **Explore the UIs**: Familiarize with each service's interface
2. **Run Sample Queries**: Test ClickHouse with provided views
3. **Monitor Data Flow**: Observe real-time processing
4. **Customize for Your Use Case**: Modify data models and processing logic
5. **Scale for Production**: Adjust configurations for larger workloads

For additional help, refer to the individual service documentation or check the project's issue tracker.