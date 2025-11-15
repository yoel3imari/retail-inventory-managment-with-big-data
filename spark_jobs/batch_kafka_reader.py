#!/usr/bin/env python3
"""
Batch Kafka Reader using older Spark Streaming API
This script uses the older RDD-based approach to read from Kafka
which might be more compatible with the available JARs.
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchKafkaReader:
    def __init__(self):
        self.spark = None
        self.kafka_broker = "kafka:19092"
        
    def initialize_spark(self):
        """Initialize Spark session with Kafka configuration"""
        try:
            self.spark = SparkSession.builder \
                .appName("BatchKafkaReader") \
                .config("spark.sql.adaptive.enabled", "false") \
                .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
                .getOrCreate()
            
            logger.info("Spark session initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def read_kafka_batch(self, topic, starting_offsets="earliest"):
        """Read data from Kafka topic using batch processing"""
        try:
            logger.info(f"Reading from Kafka topic: {topic}")
            
            # Read from Kafka using batch processing
            df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.kafka_broker) \
                .option("subscribe", topic) \
                .option("startingOffsets", starting_offsets) \
                .load()
            
            # Convert binary values to strings
            df = df.selectExpr(
                "CAST(key AS STRING) as key",
                "CAST(value AS STRING) as value",
                "topic",
                "partition",
                "offset",
                "timestamp",
                "timestampType"
            )
            
            logger.info(f"Successfully read data from topic: {topic}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read from Kafka topic {topic}: {e}")
            return None
    
    def process_sales_data(self, df):
        """Process sales data and display sample"""
        if df is None or df.count() == 0:
            logger.warning("No sales data to process")
            return
        
        logger.info(f"Processing {df.count()} sales records")
        
        # Define schema for sales data
        sales_schema = StructType([
            StructField("sale_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("quantity", StringType(), True),
            StructField("price", StringType(), True),
            StructField("timestamp", StringType(), True)
        ])
        
        # Parse JSON and show sample data
        parsed_df = df.selectExpr("value") \
            .rdd \
            .map(lambda row: json.loads(row.value)) \
            .toDF(sales_schema)
        
        logger.info("Sample sales data:")
        parsed_df.show(10, truncate=False)
        
        return parsed_df
    
    def process_inventory_data(self, df):
        """Process inventory data and display sample"""
        if df is None or df.count() == 0:
            logger.warning("No inventory data to process")
            return
        
        logger.info(f"Processing {df.count()} inventory records")
        
        # Define schema for inventory data
        inventory_schema = StructType([
            StructField("inventory_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("quantity", StringType(), True),
            StructField("timestamp", StringType(), True)
        ])
        
        # Parse JSON and show sample data
        parsed_df = df.selectExpr("value") \
            .rdd \
            .map(lambda row: json.loads(row.value)) \
            .toDF(inventory_schema)
        
        logger.info("Sample inventory data:")
        parsed_df.show(10, truncate=False)
        
        return parsed_df
    
    def run_batch_processing(self):
        """Run batch processing for both topics"""
        try:
            logger.info("Starting batch Kafka processing...")
            
            # Read sales data
            sales_df = self.read_kafka_batch("sales")
            if sales_df:
                self.process_sales_data(sales_df)
            
            # Read inventory data
            inventory_df = self.read_kafka_batch("inventory")
            if inventory_df:
                self.process_inventory_data(inventory_df)
            
            logger.info("Batch processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Spark session stopped")

def main():
    """Main function"""
    reader = BatchKafkaReader()
    
    try:
        if reader.initialize_spark():
            success = reader.run_batch_processing()
            if success:
                logger.info("SUCCESS: Batch Kafka processing completed")
            else:
                logger.error("FAILED: Batch Kafka processing failed")
        else:
            logger.error("FAILED: Could not initialize Spark session")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        reader.cleanup()

if __name__ == "__main__":
    main()