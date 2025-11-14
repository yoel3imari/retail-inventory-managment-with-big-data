# Retail Inventory Management - Documentation Index

## 📚 Overview

This project provides comprehensive documentation for the Retail Inventory Management Big Data platform. Below is an index of all documentation files and their purposes.

## 📋 Core Documentation

### Main Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| **[README.md](README.md)** | Quick start guide and project overview | All users |
| **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** | Comprehensive technical documentation | Developers, Data Engineers |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Detailed setup and configuration guide | System Administrators, Developers |
| **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** | This file - documentation overview | All users |

## 🏗️ Architecture & Planning

### Architecture Documentation

| File | Purpose | Content |
|------|---------|---------|
| **[AGENT/architecure.md](AGENT/architecure.md)** | Detailed system architecture | Layer-by-layer architecture diagrams |
| **[planning/COMPREHENSIVE_PLAN.md](planning/COMPREHENSIVE_PLAN.md)** | 7-week implementation plan | Project timeline and milestones |
| **[planning/TECHNICAL_ARCHITECTURE.md](planning/TECHNICAL_ARCHITECTURE.md)** | Technical architecture details | System design and components |

## 🔧 Implementation Guides

### Database & Schema

| File | Purpose | Content |
|------|---------|---------|
| **[clickhouse/init/01-schema.sql](clickhouse/init/01-schema.sql)** | Core database schema | Fact and dimension tables |
| **[clickhouse/init/02-enhanced-schema.sql](clickhouse/init/02-enhanced-schema.sql)** | Enhanced schema | Streaming and analytics tables |
| **[clickhouse/init/03-spark-streaming-bridge.sql](clickhouse/init/03-spark-streaming-bridge.sql)** | Spark integration schema | Streaming bridge tables |
| **[docs/clickhouse_table_verification.md](docs/clickhouse_table_verification.md)** | Data verification guide | Table monitoring and validation |

### Spark Applications

| File | Purpose | Content |
|------|---------|---------|
| **[spark_jobs/README.md](spark_jobs/README.md)** | Spark jobs overview | Job descriptions and usage |
| **[spark_jobs/unified_streaming_bridge.py](spark_jobs/unified_streaming_bridge.py)** | Unified streaming processor | Multi-topic Kafka processing |
| **[spark_jobs/sales_streaming.py](spark_jobs/sales_streaming.py)** | Sales streaming job | Real-time sales analytics |
| **[spark_jobs/inventory_streaming.py](spark_jobs/inventory_streaming.py)** | Inventory streaming job | Stock monitoring and alerts |
| **[spark_jobs/ml_training.py](spark_jobs/ml_training.py)** | ML training job | Demand forecasting models |
| **[spark_jobs/batch_processing.py](spark_jobs/batch_processing.py)** | Batch processing job | Daily aggregations and reports |
| **[spark_jobs/submit_jobs.sh](spark_jobs/submit_jobs.sh)** | Job submission script | Automated job management |

## 🚀 Operations & Scripts

### Setup & Bootstrap

| File | Purpose | Content |
|------|---------|---------|
| **[docker-compose.yml](docker-compose.yml)** | Service orchestration | All container definitions |
| **[scripts/bootstrap.sh](scripts/bootstrap.sh)** | Automated setup | One-click service initialization |
| **[config/settings.py](config/settings.py)** | Configuration management | Centralized settings |

### Data Generation

| File | Purpose | Content |
|------|---------|---------|
| **[scripts/data_generator.py](scripts/data_generator.py)** | Real-time data generator | Fake retail data simulation |
| **[scripts/create_sample_data.py](scripts/create_sample_data.py)** | Sample data creation | Dimension table population |
| **[scripts/populate_sample_data.py](scripts/populate_sample_data.py)** | Data population | Sample data loading |

### Testing & Validation

| File | Purpose | Content |
|------|---------|---------|
| **[scripts/test_spark_clickhouse_bridge.py](scripts/test_spark_clickhouse_bridge.py)** | Pipeline testing | End-to-end data flow validation |
| **[scripts/check_clickhouse_tables.py](scripts/check_clickhouse_tables.py)** | Data verification | Table data quality checks |
| **[scripts/test_minio_integration.py](scripts/test_minio_integration.py)** | MinIO testing | Object storage validation |

## 📊 Workflow & Orchestration

### Airflow DAGs

| File | Purpose | Content |
|------|---------|---------|
| **[dags/retail_inventory_dag.py](dags/retail_inventory_dag.py)** | Main pipeline DAG | Hourly processing workflow |
| **[dags/data_quality_dag.py](dags/data_quality_dag.py)** | Data quality DAG | Monitoring and validation |

## 🔍 Quick Reference

### Service URLs & Ports

| Service | URL | Port | Credentials |
|---------|-----|------|-------------|
| **Kafka UI** | http://localhost:8080 | 8080 | None |
| **MinIO Console** | http://localhost:9001 | 9001 | minioadmin/minioadmin |
| **Spark Master UI** | http://localhost:8082 | 8082 | None |
| **ClickHouse HTTP** | http://localhost:8123 | 8123 | default/clickhouse |
| **Airflow** | http://localhost:8081 | 8081 | airflow/airflow |

### Common Commands

#### Quick Start
```bash
# One-click setup
./scripts/bootstrap.sh

# Manual setup
docker-compose up -d
docker exec data-generator python scripts/create_sample_data.py
docker exec spark-master ./submit_jobs.sh unified
```

#### Data Verification
```bash
# Check pipeline health
python scripts/test_spark_clickhouse_bridge.py

# Verify ClickHouse data
python scripts/check_clickhouse_tables.py

# Manual queries
docker exec clickhouse clickhouse-client --password clickhouse --database retail
```

#### Monitoring
```bash
# Check service logs
docker-compose logs -f <service-name>

# Check job status
docker exec spark-master ./submit_jobs.sh status

# Verify Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

## 🎯 Learning Path

### For Beginners
1. Start with **[README.md](README.md)** for quick setup
2. Use **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for detailed configuration
3. Explore **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** for technical understanding

### For Developers
1. Review **[AGENT/architecure.md](AGENT/architecure.md)** for system design
2. Study **[spark_jobs/README.md](spark_jobs/README.md)** for job implementation
3. Check **[config/settings.py](config/settings.py)** for configuration

### For Data Engineers
1. Examine **[clickhouse/init/](clickhouse/init/)** for database schema
2. Review **[dags/](dags/)** for workflow orchestration
3. Study **[scripts/](scripts/)** for automation and testing

## 📞 Support & Resources

### Troubleshooting
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Common issues and solutions
- **[docs/clickhouse_table_verification.md](docs/clickhouse_table_verification.md)** - Data quality monitoring
- Service logs via `docker-compose logs -f <service>`

### External Resources
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark Documentation](https://spark.apache.org/docs/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)

---

**Last Updated**: 2025-11-13  
**Project Version**: 1.0.0  
**Documentation Status**: ✅ Complete and Updated