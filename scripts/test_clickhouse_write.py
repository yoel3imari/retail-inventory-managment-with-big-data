#!/usr/bin/env python3
"""
Enhanced ClickHouse write test with connection fallback
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_clickhouse_write():
    """Test writing to ClickHouse with connection fallback"""
    try:
        spark = SparkSession.builder \
            .appName("ClickHouseTest") \
            .config("spark.jars.packages", "com.clickhouse:clickhouse-jdbc:0.4.6") \
            .getOrCreate()
        
        # Create test data matching the actual schema from producers
        test_data = [
            ("test_txn_1", "STORE001", "SKU001", 10, 25.99, 259.90,
             datetime.now().isoformat(), "CUST1001", "credit_card", "North", "Electronics")
        ]
        
        schema = StructType([
            StructField("transaction_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("unit_price", DoubleType(), True),
            StructField("total_amount", DoubleType(), True),
            StructField("timestamp", StringType(), True),  # ISO format string
            StructField("customer_id", StringType(), True),
            StructField("payment_method", StringType(), True),
            StructField("store_region", StringType(), True),
            StructField("product_category", StringType(), True)
        ])
        
        df = spark.createDataFrame(test_data, schema)
        
        # Add processing metadata
        enriched_df = df \
            .withColumn("processing_timestamp", current_timestamp()) \
            .withColumn("spark_job_id", lit("test_batch"))
        
        # Connection configurations
        primary_config = {
            "url": "jdbc:clickhouse://localhost:8123/retail",
            "driver": "com.clickhouse.jdbc.ClickHouseDriver",
            "user": "default",
            "password": "clickhouse"
        }
        
        alt_config = {
            "url": "jdbc:clickhouse://clickhouse:8123/retail",
            "driver": "com.clickhouse.jdbc.ClickHouseDriver",
            "user": "default",
            "password": "clickhouse"
        }
        
        # Try primary connection first
        try:
            enriched_df.write \
                .format("jdbc") \
                .option("url", primary_config["url"]) \
                .option("driver", primary_config["driver"]) \
                .option("dbtable", "raw_sales_events") \
                .option("user", primary_config["user"]) \
                .option("password", primary_config["password"]) \
                .mode("append") \
                .save()
            
            print("✅ Successfully wrote test data to ClickHouse using primary connection (localhost)")
            return True
            
        except Exception as primary_error:
            print(f"⚠️ Primary connection failed: {primary_error}")
            print("Trying alternative connection...")
            
            # Try alternative connection
            try:
                enriched_df.write \
                    .format("jdbc") \
                    .option("url", alt_config["url"]) \
                    .option("driver", alt_config["driver"]) \
                    .option("dbtable", "raw_sales_events") \
                    .option("user", alt_config["user"]) \
                    .option("password", alt_config["password"]) \
                    .mode("append") \
                    .save()
                
                print("✅ Successfully wrote test data to ClickHouse using alternative connection (clickhouse container)")
                return True
                
            except Exception as alt_error:
                print(f"❌ Alternative connection also failed: {alt_error}")
                return False
        
    except Exception as e:
        print(f"❌ Failed to write to ClickHouse: {e}")
        return False

def test_connection_options():
    """Test different connection options"""
    print("\n🔍 Testing ClickHouse connection options...")
    
    connection_urls = [
        "jdbc:clickhouse://localhost:8123/retail",
        "jdbc:clickhouse://clickhouse:8123/retail",
        "jdbc:clickhouse://127.0.0.1:8123/retail"
    ]
    
    for url in connection_urls:
        print(f"\nTesting: {url}")
        try:
            spark = SparkSession.builder \
                .appName("ConnectionTest") \
                .config("spark.jars.packages", "com.clickhouse:clickhouse-jdbc:0.4.6") \
                .getOrCreate()
            
            # Simple test query
            test_df = spark.read \
                .format("jdbc") \
                .option("url", url) \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .option("dbtable", "system.tables") \
                .option("user", "default") \
                .option("password", "clickhouse") \
                .load() \
                .limit(1)
            
            count = test_df.count()
            print(f"✅ Connection successful - found {count} system tables")
            spark.stop()
            return url
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            if spark:
                spark.stop()
    
    return None

if __name__ == "__main__":
    print("🚀 Starting ClickHouse connectivity test...")
    
    # First test connection options
    working_url = test_connection_options()
    
    if working_url:
        print(f"\n🎯 Using working connection: {working_url}")
        # Then test write operation
        success = test_clickhouse_write()
        if success:
            print("\n🎉 All ClickHouse tests passed!")
        else:
            print("\n💥 Write test failed")
    else:
        print("\n💥 No working ClickHouse connection found")