#!/usr/bin/env python3
"""
Simple batch test to verify Kafka connectivity and data reading
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, expr
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchKafkaTest:
    def __init__(self):
        self.spark = None
        
    def initialize_spark(self):
        """Initialize Spark session"""
        try:
            self.spark = SparkSession.builder \
                .appName("BatchKafkaTest") \
                .config("spark.sql.adaptive.enabled", "false") \
                .getOrCreate()
            
            # Set log level to WARN to reduce noise
            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info("Spark session initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def test_kafka_connectivity(self):
        """Test basic Kafka connectivity and read messages"""
        try:
            logger.info("Testing Kafka connectivity...")
            
            # Read from sales topic
            sales_df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "sales") \
                .option("startingOffsets", "earliest") \
                .load()
            
            logger.info(f"Successfully connected to Kafka. Found {sales_df.count()} sales messages")
            
            # Read from inventory topic
            inventory_df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "inventory") \
                .option("startingOffsets", "earliest") \
                .load()
            
            logger.info(f"Successfully connected to Kafka. Found {inventory_df.count()} inventory messages")
            
            # Show sample data
            logger.info("Sample sales data:")
            sales_df.select("value").limit(5).show(truncate=False)
            
            logger.info("Sample inventory data:")
            inventory_df.select("value").limit(5).show(truncate=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False
    
    def process_data(self):
        """Process and parse the Kafka messages"""
        try:
            logger.info("Processing Kafka messages...")
            
            # Define schemas for parsing
            sales_schema = StructType([
                StructField("transaction_id", StringType()),
                StructField("product_id", IntegerType()),
                StructField("store_id", IntegerType()),
                StructField("quantity", IntegerType()),
                StructField("price", DoubleType()),
                StructField("timestamp", StringType())
            ])
            
            inventory_schema = StructType([
                StructField("product_id", IntegerType()),
                StructField("store_id", IntegerType()),
                StructField("quantity", IntegerType()),
                StructField("timestamp", StringType())
            ])
            
            # Read and parse sales data
            sales_df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "sales") \
                .option("startingOffsets", "earliest") \
                .load() \
                .select(
                    col("key").cast("string"),
                    col("value").cast("string"),
                    col("topic"),
                    col("partition"),
                    col("offset"),
                    col("timestamp")
                )
            
            # Parse JSON data
            parsed_sales = sales_df.select(
                col("key"),
                from_json(col("value"), sales_schema).alias("parsed_data"),
                col("topic"),
                col("partition"),
                col("offset"),
                col("timestamp")
            ).select(
                col("key"),
                col("parsed_data.transaction_id"),
                col("parsed_data.product_id"),
                col("parsed_data.store_id"),
                col("parsed_data.quantity"),
                col("parsed_data.price"),
                col("parsed_data.timestamp"),
                col("topic"),
                col("partition"),
                col("offset"),
                col("timestamp")
            )
            
            logger.info("Parsed sales data:")
            parsed_sales.show(10, truncate=False)
            
            # Read and parse inventory data
            inventory_df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "inventory") \
                .option("startingOffsets", "earliest") \
                .load() \
                .select(
                    col("key").cast("string"),
                    col("value").cast("string"),
                    col("topic"),
                    col("partition"),
                    col("offset"),
                    col("timestamp")
                )
            
            # Parse JSON data
            parsed_inventory = inventory_df.select(
                col("key"),
                from_json(col("value"), inventory_schema).alias("parsed_data"),
                col("topic"),
                col("partition"),
                col("offset"),
                col("timestamp")
            ).select(
                col("key"),
                col("parsed_data.product_id"),
                col("parsed_data.store_id"),
                col("parsed_data.quantity"),
                col("parsed_data.timestamp"),
                col("topic"),
                col("partition"),
                col("offset"),
                col("timestamp")
            )
            
            logger.info("Parsed inventory data:")
            parsed_inventory.show(10, truncate=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process data: {e}")
            return False
    
    def run_test(self):
        """Run the complete batch test"""
        logger.info("Starting batch Kafka test...")
        
        if not self.initialize_spark():
            return False
        
        try:
            if not self.test_kafka_connectivity():
                return False
            
            if not self.process_data():
                return False
            
            logger.info("Batch Kafka test completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Batch test failed: {e}")
            return False
        finally:
            if self.spark:
                self.spark.stop()
                logger.info("Spark session stopped")

def main():
    """Main function"""
    test = BatchKafkaTest()
    success = test.run_test()
    
    if success:
        logger.info("SUCCESS: Batch Kafka test passed!")
        exit(0)
    else:
        logger.error("FAILED: Batch Kafka test failed!")
        exit(1)

if __name__ == "__main__":
    main()