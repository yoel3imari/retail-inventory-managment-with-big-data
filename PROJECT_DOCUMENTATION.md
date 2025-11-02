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
- **Source**: Fake data generator simulating retail operations
- **Output**: JSON events published to Kafka topics
- **Topics**: `sales_events`, `inventory_events`

### 2. Real-time Processing
- **Technology**: Spark Structured Streaming
- **Processing**: Windowed aggregations, anomaly detection
- **Output**: Real-time metrics and alerts

### 3. Batch Processing
- **Technology**: Spark Batch Jobs
- **Processing**: Daily aggregations, ML training
- **Output**: Business reports, trained models

### 4. Data Storage
- **Technology**: ClickHouse
- **Schema**: Star schema with facts and dimensions
- **Features**: Columnar storage, real-time inserts

### 5. Visualization
- **Technology**: Power BI
- **Data Source**: ClickHouse via JDBC
- **Features**: Interactive dashboards, real-time updates

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
1. **Sales Streaming** (`sales_streaming.py`)
   - Real-time sales metrics
   - Anomaly detection
   - Windowed aggregations

2. **Inventory Streaming** (`inventory_streaming.py`)
   - Stock level monitoring
   - Alert generation
   - Turnover calculations

#### Batch Applications
3. **ML Training** (`ml_training.py`)
   - Demand forecasting (Random Forest)
   - Stock optimization (GBT)
   - Model evaluation and saving

4. **Batch Processing** (`batch_processing.py`)
   - Daily KPI calculations
   - Business reports
   - Performance rankings

#### Job Management
- `submit_jobs.sh`: Automated job submission
- Configuration management
- Checkpoint handling

### Database Schema (`clickhouse/init/`)

#### Core Tables
- **Fact Tables**: `fact_sales`, `fact_inventory`, `fact_ml_predictions`
- **Dimension Tables**: `dim_date`, `dim_product`, `dim_store`
- **Raw Events**: `raw_sales_events`, `raw_inventory_events`

#### Enhanced Tables
- **Real-time Metrics**: `realtime_sales_metrics`
- **Alerts**: `realtime_inventory_alerts`
- **ML Results**: `ml_model_results`
- **Batch Results**: `batch_processing_results`

#### Analytical Views
- Real-time dashboard
- Active alerts
- ML model performance
- Inventory turnover analysis
- Customer behavior analysis
- Seasonal patterns
- Store comparison
- Category performance

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
- Schema validation for incoming data
- Business rule enforcement
- Data quality monitoring
- Anomaly detection

### Pipeline Testing
- Unit tests for individual components
- Integration tests for data flow
- Performance testing under load
- Failure scenario testing

### Model Validation
- Cross-validation for ML models
- A/B testing for business impact
- Model drift detection
- Feature importance analysis

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
- **Kafka UI**: http://localhost:8080 - Monitor Kafka topics and messages
- **MinIO Console**: http://localhost:9001 - Object storage management (minioadmin/minioadmin)
- **Spark Master UI**: http://localhost:8082 - Monitor Spark applications
- **ClickHouse HTTP**: http://localhost:8123 - Database interface

## Conclusion

This project provides a comprehensive foundation for understanding and implementing big data solutions in retail inventory management. It demonstrates modern data engineering practices while maintaining academic rigor and practical applicability.

The modular architecture allows for easy extension and customization, making it suitable for both learning and real-world implementation. The use of open-source technologies ensures accessibility and community support.

### Key Success Factors
1. **Well-defined Architecture**: Clear separation of concerns
2. **Scalable Design**: Ability to handle increasing data volumes
3. **Comprehensive Monitoring**: End-to-end visibility
4. **Academic Relevance**: Coverage of key big data concepts
5. **Practical Implementation**: Real-world use case with business value

This project serves as both an educational resource and a starting point for production implementations in retail analytics and inventory management.