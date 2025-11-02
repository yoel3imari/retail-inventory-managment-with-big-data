import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application Settings
APP_NAME = "retail-inventory-management"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Kafka Configuration
KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "client_id": APP_NAME,
    "acks": "all",
    "retries": 3,
    "batch_size": 16384,
    "linger_ms": 10,
    "compression_type": "gzip",
}

# Kafka Topics
KAFKA_TOPICS = {
    "sales_transactions": "retail-sales-transactions",
    "inventory_updates": "retail-inventory-updates",
    "restock_alerts": "retail-restock-alerts",
    "price_changes": "retail-price-changes",
    "customer_events": "retail-customer-events",
}

# MinIO Configuration
MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    "secure": False,
    "region": "us-east-1",
}

# MinIO Buckets
MINIO_BUCKETS = {
    "raw_data": "retail-raw-data",
    "processed_data": "retail-processed-data",
    "models": "retail-models",
    "features": "retail-features",
}

# MinIO Storage Paths
MINIO_PATHS = {
    "models": {
        "demand_forecasting": "models/demand_forecasting",
        "stock_optimization": "models/stock_optimization",
        "anomaly_detection": "models/anomaly_detection"
    },
    "data": {
        "batch_results": "batch_results",
        "streaming_checkpoints": "streaming_checkpoints",
        "feature_store": "feature_store",
        "reports": "reports"
    }
}

# ClickHouse Configuration
CLICKHOUSE_CONFIG = {
    "host": os.getenv("CLICKHOUSE_HOST", "clickhouse"),
    "port": int(os.getenv("CLICKHOUSE_PORT", "8123")),
    "username": os.getenv("CLICKHOUSE_USER", "default"),
    "password": os.getenv("CLICKHOUSE_PASSWORD", "clickhouse"),
    "database": os.getenv("CLICKHOUSE_DATABASE", "retail"),
    "secure": False,
}

# Spark Configuration
SPARK_CONFIG = {
    "app_name": f"{APP_NAME}-spark",
    "master": os.getenv("SPARK_MASTER", "local[*]"),
    "config": {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.streaming.backpressure.enabled": "true",
        "spark.sql.shuffle.partitions": "200",
        "spark.default.parallelism": "200",
        "spark.driver.memory": "2g",
        "spark.executor.memory": "2g",
        "spark.driver.maxResultSize": "2g",
    }
}

# Airflow Configuration
AIRFLOW_CONFIG = {
    "dag_default_args": {
        "owner": "retail-team",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": 300,  # 5 minutes
    },
    "schedule_intervals": {
        "daily_etl": "0 8 * * *",  # 8:00 AM daily
        "feature_engineering": "0 9 * * *",  # 9:00 AM daily
        "batch_predictions": "0 10 * * *",  # 10:00 AM daily
        "model_training": "0 2 * * 0",  # 2:00 AM Sunday
    }
}

# ML Configuration
ML_CONFIG = {
    "demand_forecast": {
        "horizon_days": 7,
        "features": [
            "historical_sales_7d", "historical_sales_14d", "historical_sales_30d",
            "day_of_week", "month", "is_weekend", "is_holiday",
            "promotion_flag", "price_change_pct"
        ],
        "model_type": "gradient_boosting",
    },
    "stock_optimization": {
        "safety_stock_days": 3,
        "reorder_point_buffer": 1.2,
        "max_stock_days": 30,
    }
}

# Data Generation Configuration
DATA_GENERATION_CONFIG = {
    "stores": {
        "count": int(os.getenv("STORE_COUNT", "10")),
        "regions": ["North", "South", "East", "West", "Central"],
        "types": ["Supermarket", "Convenience", "Hypermarket", "Specialty"],
    },
    "products": {
        "count": int(os.getenv("PRODUCT_COUNT", "1000")),
        "categories": [
            "Electronics", "Clothing", "Food", "Home", "Sports", 
            "Beauty", "Toys", "Books", "Automotive", "Health"
        ],
        "brands_per_category": 5,
    },
    "sales": {
        "transactions_per_hour": 100,
        "peak_hours": [10, 11, 12, 17, 18, 19],  # 10AM-1PM, 5PM-8PM
        "weekend_multiplier": 1.5,
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "/app/logs/retail_inventory.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "DEBUG"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Feature Store Configuration
FEATURE_STORE_CONFIG = {
    "tables": {
        "sales_features": "retail.sales_features",
        "inventory_features": "retail.inventory_features",
        "product_features": "retail.product_features",
        "store_features": "retail.store_features",
    },
    "refresh_intervals": {
        "real_time": "5 minutes",
        "daily": "1 day",
        "weekly": "7 days",
    }
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "prometheus": {
        "port": 8000,
        "endpoint": "/metrics",
    },
    "health_checks": {
        "kafka": "kafka:9092",
        "clickhouse": "clickhouse:8123",
        "minio": "minio:9000",
    }
}