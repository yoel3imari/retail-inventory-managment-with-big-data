# Retail Inventory Management with Big Data - Project Documentation

## Project Overview

This academic project demonstrates a complete big data pipeline for retail inventory management, showcasing modern data engineering practices including real-time streaming, distributed processing, machine learning, and business intelligence.

### Key Features
- **Real-time Data Processing**: Kafka + Spark Streaming for live data
- **Machine Learning**: Demand forecasting and stock optimization
- **Data Warehousing**: ClickHouse for analytical queries
- **Workflow Orchestration**: Airflow for pipeline management
- **Business Intelligence**: Power BI dashboards for insights
- **Containerized Deployment**: Docker Compose for easy setup

## Architecture

### High-Level Architecture
```
Data Sources → Kafka → Spark Streaming → ClickHouse → Power BI
     ↓              ↓           ↓           ↓
Data Generator  Real-time   ML Training  Airflow DAGs
               Processing   Batch Jobs
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Streaming** | Apache Kafka | Real-time event streaming |
| **Processing** | Apache Spark | Distributed data processing |
| **Storage** | ClickHouse | OLAP database for analytics |
| **Orchestration** | Apache Airflow | Workflow management |
| **Object Storage** | MinIO | S3-compatible storage |
| **Visualization** | Power BI | Business intelligence |
| **Containerization** | Docker | Service deployment |

## Data Flow

### 1. Data Generation
- **Source**: [`scripts/data_generator.py`](scripts/data_generator.py) - Realistic retail data simulator
- **Output**: JSON events published to Kafka topics
- **Topics**: `retail-sales-transactions`, `retail-inventory-updates`, `retail-restock-alerts`
- **Features**: Peak hour patterns, weekend multipliers, seasonal variations

### 2. Real-time Processing
- **Technology**: Spark Structured Streaming with unified bridge
- **Applications**:
  - [`spark_jobs/unified_streaming_bridge.py`](spark_jobs/unified_streaming_bridge.py) - Multi-topic processing
  - [`spark_jobs/sales_streaming.py`](spark_jobs/sales_streaming.py) - Sales-specific processing
  - [`spark_jobs/inventory_streaming.py`](spark_jobs/inventory_streaming.py) - Inventory monitoring
- **Processing**: 5-minute windows, real-time metrics, anomaly detection
- **Output**: ClickHouse tables with real-time metrics and alerts

### 3. Batch Processing & ML
- **Technology**: Spark Batch Jobs with MLlib
- **Applications**:
  - [`spark_jobs/ml_training.py`](spark_jobs/ml_training.py) - Demand forecasting models
  - [`spark_jobs/batch_processing.py`](spark_jobs/batch_processing.py) - Daily aggregations
- **Processing**: Feature engineering, model training, business reports
- **Output**: Trained models, performance metrics, business insights

### 4. Data Storage & Analytics
- **Technology**: ClickHouse OLAP database
- **Schema**: Enhanced star schema with real-time views
- **Tables**: `fact_sales`, `fact_inventory`, `spark_sales_metrics`, `spark_inventory_metrics`
- **Features**: Columnar storage, real-time inserts, materialized views

### 5. Visualization & Monitoring
- **Technology**: Power BI with ClickHouse integration
- **Data Source**: ClickHouse via ODBC/JDBC
- **Features**: Interactive dashboards, real-time updates, automated alerts
- **Monitoring**: [`docs/clickhouse_table_verification.md`](docs/clickhouse_table_verification.md) - Data quality checks

## Implementation Details

### Infrastructure (`docker-compose.yml`)

#### Service Configuration
- **Kafka**: KRaft mode (no Zookeeper), internal/external listeners
- **Spark**: Master-worker architecture, resource allocation
- **ClickHouse**: Optimized for analytics, partitioned tables
- **Airflow**: LocalExecutor, PostgreSQL backend
- **MinIO**: S3-compatible API, web console

#### Network Configuration
- Internal `dev-network` for service communication
- Port mapping for external access
- Health checks for service monitoring

### Data Generation (`scripts/`)

#### Components
- `data_generator.py`: Main data generation script
- `create_sample_data.py`: Dimension table population
- Kafka producers for event streaming

#### Data Models
- **Sales Events**: Transactions, customers, products
- **Inventory Events**: Stock levels, updates, alerts
- **Dimension Data**: Products, stores, categories

### Spark Applications (`spark_jobs/`)

#### Streaming Applications
1. **Unified Streaming Bridge** ([`unified_streaming_bridge.py`](spark_jobs/unified_streaming_bridge.py))
   - Multi-topic Kafka consumption (sales + inventory)
   - Real-time metrics aggregation
   - Unified alert detection
   - ClickHouse integration for both raw and processed data

2. **Sales Streaming** ([`sales_streaming.py`](spark_jobs/sales_streaming.py))
   - Real-time sales metrics with ClickHouse output
   - Anomaly detection for high-value transactions
   - 5-minute windowed aggregations with 1-minute slides

3. **Inventory Streaming** ([`inventory_streaming.py`](spark_jobs/inventory_streaming.py))
   - Stock level monitoring with real-time alerts
   - Turnover calculations and stock status classification
   - 10-minute windows with 2-minute slides

#### Batch Applications
4. **ML Training** ([`ml_training.py`](spark_jobs/ml_training.py))
   - Demand forecasting (Random Forest + Gradient Boosted Trees)
   - Stock optimization models
   - Model evaluation with RMSE metrics
   - Model saving to MinIO storage

5. **Batch Processing** ([`batch_processing.py`](spark_jobs/batch_processing.py))
   - Daily KPI calculations and business reports
   - Performance rankings and trend analysis
   - ClickHouse materialized view updates

#### Job Management
- [`submit_jobs.sh`](spark_jobs/submit_jobs.sh): Automated job submission with unified bridge support
- Configuration management via [`config/settings.py`](config/settings.py)
- Checkpoint handling with automatic directory creation
- Job monitoring and status tracking

### Database Schema (`clickhouse/init/`)

#### Core Tables
- **Fact Tables**: `fact_sales`, `fact_inventory`, `fact_ml_predictions`
- **Dimension Tables**: `dim_date`, `dim_product`, `dim_store`, `dim_category`, `dim_brand`
- **Raw Events**: `raw_sales_events`, `raw_inventory_events`

#### Spark Streaming Tables
- **Real-time Metrics**: `spark_sales_metrics`, `spark_inventory_metrics`
- **Streaming Alerts**: `streaming_alerts`
- **Raw Events**: `streaming_events_raw`
- **Job Monitoring**: `spark_job_monitoring`

#### Enhanced Views
- **Real-time Dashboard**: Aggregated metrics for Power BI
- **Active Alerts**: Current stock and sales anomalies
- **ML Model Performance**: Prediction accuracy and feature importance
- **Inventory Turnover Analysis**: Stock movement patterns
- **Customer Behavior Analysis**: Purchase patterns and trends
- **Seasonal Patterns**: Time-based sales trends
- **Store Comparison**: Performance metrics across locations
- **Category Performance**: Product category analytics

#### Schema Management
- **Initialization**: [`clickhouse/init/01-schema.sql`](clickhouse/init/01-schema.sql) - Core schema
- **Enhanced Schema**: [`clickhouse/init/02-enhanced-schema.sql`](clickhouse/init/02-enhanced-schema.sql) - Streaming tables
- **Bridge Schema**: [`clickhouse/init/03-spark-streaming-bridge.sql`](clickhouse/init/03-spark-streaming-bridge.sql) - Spark integration
- **Verification**: [`docs/clickhouse_table_verification.md`](docs/clickhouse_table_verification.md) - Data quality checks

### Workflow Orchestration (`dags/`)

#### Main Pipeline DAG
- **Schedule**: Hourly
- **Tasks**: Infrastructure checks, streaming jobs, batch processing
- **Monitoring**: Data quality, pipeline health

#### Data Quality DAG
- **Schedule**: Every 30 minutes
- **Checks**: Data freshness, completeness, consistency
- **Monitoring**: Service health, performance metrics

#### Daily Operations DAG
- **Schedule**: Daily
- **Tasks**: Comprehensive reporting, data archiving, model updates

## Machine Learning Implementation

### Demand Forecasting

#### Features
- Historical sales data with lag variables
- Time-based features (day of week, month, weekend)
- Product and store characteristics
- Rolling averages and trends

#### Model
- **Algorithm**: Random Forest Regressor
- **Evaluation**: RMSE, feature importance
- **Output**: Daily demand predictions

### Stock Optimization

#### Features
- Current stock levels and volatility
- Sales patterns and trends
- Product characteristics
- Historical stock-out events

#### Model
- **Algorithm**: Gradient Boosted Trees
- **Evaluation**: RMSE, business metrics
- **Output**: Optimal stock levels

## Business Intelligence

### Power BI Data Model

#### Key Measures
- Total Revenue, Transactions, Customers
- Profit Margins, Average Transaction Value
- Inventory Turnover, Stock-out Rates
- Customer Lifetime Value

#### Dashboard Pages
1. **Executive Overview**: High-level KPIs and trends
2. **Real-time Monitoring**: Live data and alerts
3. **Inventory Management**: Stock levels and optimization
4. **ML Insights**: Predictions and recommendations
5. **Store Analytics**: Performance comparisons

## Performance Considerations

### Streaming Performance
- **Backpressure Handling**: Adaptive rate limiting
- **Window Optimization**: Appropriate window sizes
- **Checkpointing**: Fault tolerance and recovery

### Database Performance
- **Partitioning**: Time-based partitioning for facts
- **Indexing**: Optimized primary keys
- **Aggregations**: Materialized views for common queries

### Resource Management
- **Memory Allocation**: Balanced across services
- **CPU Utilization**: Parallel processing where possible
- **Storage Optimization**: Compression and archiving

## Academic Value

### Big Data Concepts Demonstrated

#### Data Engineering
- Real-time streaming architectures
- Distributed processing patterns
- Data pipeline design and implementation
- ETL/ELT processes

#### Machine Learning
- Feature engineering at scale
- Distributed model training
- Model deployment and monitoring
- Business impact measurement

#### Data Warehousing
- Star schema design
- OLAP optimization
- Query performance tuning
- Data modeling best practices

#### DevOps & Operations
- Containerized deployment
- Service orchestration
- Monitoring and alerting
- Infrastructure as code

### Learning Outcomes

#### Technical Skills
- Apache Spark programming (PySpark)
- Kafka stream processing
- ClickHouse database management
- Airflow workflow design
- Power BI dashboard development

#### Architectural Skills
- Microservices design
- Event-driven architecture
- Data pipeline optimization
- System integration patterns

#### Business Skills
- Retail analytics understanding
- KPI definition and measurement
- Business intelligence implementation
- Data-driven decision making

## Extension Opportunities

### Technical Extensions
1. **Real-time ML**: Online learning for streaming data
2. **Advanced Analytics**: Customer segmentation, recommendation engines
3. **Data Governance**: Data lineage, quality monitoring
4. **Security**: Authentication, authorization, encryption

### Business Extensions
1. **Multi-channel**: E-commerce integration
2. **Supply Chain**: Vendor management, logistics
3. **Pricing**: Dynamic pricing optimization
4. **Customer Experience**: Personalization, loyalty programs

### Scalability Extensions
1. **Cluster Scaling**: Kubernetes deployment
2. **Data Volume**: Partitioning strategies for larger datasets
3. **Global Deployment**: Multi-region architecture
4. **High Availability**: Disaster recovery planning

## Testing and Validation

### Data Validation
- **Schema Validation**: JSON schema validation for incoming Kafka events
- **Business Rules**: Enforced through [`config/settings.py`](config/settings.py) configuration
- **Data Quality**: Automated monitoring via [`docs/clickhouse_table_verification.md`](docs/clickhouse_table_verification.md)
- **Anomaly Detection**: Real-time detection in streaming applications

### Pipeline Testing
- **End-to-End Testing**: [`scripts/test_spark_clickhouse_bridge.py`](scripts/test_spark_clickhouse_bridge.py) - Complete pipeline validation
- **Integration Tests**: Service connectivity and data flow verification
- **Performance Testing**: Load testing with realistic data volumes
- **Failure Scenarios**: Graceful error handling and recovery

### Model Validation
- **Cross-Validation**: Implemented in [`spark_jobs/ml_training.py`](spark_jobs/ml_training.py)
- **Business Impact**: A/B testing framework for model comparison
- **Model Drift**: Continuous monitoring of prediction accuracy
- **Feature Importance**: Analysis and reporting in ML training jobs

### Automated Testing Framework
- **Pipeline Test**: Comprehensive test suite for Kafka-Spark-ClickHouse integration
- **Data Quality Checks**: Automated validation of ClickHouse table data
- **Service Health**: Continuous monitoring of all infrastructure components
- **Alert Verification**: Testing of real-time alert generation and delivery

## Deployment Considerations

### Development Environment
- Local Docker Compose setup
- Sample data for testing
- Development tools and debugging

### Production Readiness
- Security hardening
- Monitoring and alerting
- Backup and recovery
- Performance optimization

### Cost Optimization
- Resource right-sizing
- Storage tiering
- Compute optimization
- Monitoring and adjustment

## Web Interfaces (Accessible Now)

| Service | URL | Port | Credentials | Purpose |
|---------|-----|------|-------------|---------|
| **Kafka UI** | http://localhost:8080 | 8080 | None | Monitor Kafka topics and messages |
| **MinIO Console** | http://localhost:9001 | 9001 | minioadmin/minioadmin | Object storage management |
| **Spark Master UI** | http://localhost:8082 | 8082 | None | Monitor Spark applications |
| **ClickHouse HTTP** | http://localhost:8123 | 8123 | default/clickhouse | Database HTTP interface |
| **Airflow** | http://localhost:8081 | 8081 | airflow/airflow | Workflow orchestration |

## Current Implementation Status

### Active Services
- **Kafka**: KRaft mode (no Zookeeper), topics: `retail-sales-transactions`, `retail-inventory-updates`
- **MinIO**: S3-compatible storage with buckets: `retail-raw-data`, `retail-processed-data`
- **ClickHouse**: OLAP database with retail schema and real-time tables
- **Spark**: Master-worker cluster with streaming and batch processing
- **Airflow**: LocalExecutor with PostgreSQL backend
- **Data Generator**: Automated fake data generation with realistic patterns

### Data Flow Architecture
```
Data Generator → Kafka Topics → Spark Streaming → ClickHouse Tables → Power BI
     ↓              ↓               ↓                ↓
  Sales Events  Inventory     Unified Bridge     Real-time
  (JSON)        Updates       Processing         Dashboards
```

### Key Features Implemented
1. **Unified Streaming Bridge**: [`spark_jobs/unified_streaming_bridge.py`](spark_jobs/unified_streaming_bridge.py) - Processes both sales and inventory streams
2. **Automated Bootstrap**: [`scripts/bootstrap.sh`](scripts/bootstrap.sh) - One-click service initialization
3. **Data Quality Monitoring**: [`docs/clickhouse_table_verification.md`](docs/clickhouse_table_verification.md) - Comprehensive data validation
4. **Pipeline Testing**: [`scripts/test_spark_clickhouse_bridge.py`](scripts/test_spark_clickhouse_bridge.py) - End-to-end pipeline validation
5. **Configuration Management**: [`config/settings.py`](config/settings.py) - Centralized configuration

## Quick Start Commands

### Initial Setup
```bash
# Start all services
docker-compose up -d

# Initialize infrastructure and data
./scripts/bootstrap.sh
```

### Data Generation
```bash
# Generate sample dimension data
docker exec data-generator python scripts/create_sample_data.py

# Start real-time data generation
docker exec data-generator python scripts/data_generator.py --duration 60 --rate 10
```

### Spark Job Submission
```bash
# Submit unified streaming bridge (recommended)
docker exec spark-master ./submit_jobs.sh unified

# Submit individual jobs
docker exec spark-master ./submit_jobs.sh sales
docker exec spark-master ./submit_jobs.sh inventory
docker exec spark-master ./submit_jobs.sh ml

# Check job status
docker exec spark-master ./submit_jobs.sh status
```

### Data Verification
```bash
# Check ClickHouse tables
python scripts/check_clickhouse_tables.py

# Run comprehensive pipeline test
python scripts/test_spark_clickhouse_bridge.py

# Manual ClickHouse queries
docker exec clickhouse clickhouse-client --password clickhouse --database retail
```

### Monitoring
```bash
# Check service logs
docker-compose logs -f kafka
docker-compose logs -f spark-master
docker-compose logs -f data-generator

# Access web interfaces
# Kafka UI: http://localhost:8080
# Spark UI: http://localhost:8082
# Airflow: http://localhost:8081
# MinIO: http://localhost:9001
```

## Conclusion

This project provides a comprehensive foundation for understanding and implementing big data solutions in retail inventory management. It demonstrates modern data engineering practices while maintaining academic rigor and practical applicability.

The modular architecture allows for easy extension and customization, making it suitable for both learning and real-world implementation. The use of open-source technologies ensures accessibility and community support.

### Key Success Factors
1. **Well-defined Architecture**: Clear separation of concerns with unified streaming bridge
2. **Scalable Design**: Ability to handle increasing data volumes with distributed processing
3. **Comprehensive Monitoring**: End-to-end visibility with automated testing and validation
4. **Academic Relevance**: Coverage of key big data concepts including streaming, ML, and analytics
5. **Practical Implementation**: Real-world use case with business value and production-ready components

### Recent Enhancements
- **Unified Streaming Bridge**: Multi-topic processing with ClickHouse integration
- **Automated Bootstrap**: One-click service initialization and data generation
- **Comprehensive Testing**: End-to-end pipeline validation and data quality checks
- **Enhanced Documentation**: Updated guides and verification procedures

This project serves as both an educational resource and a starting point for production implementations in retail analytics and inventory management.