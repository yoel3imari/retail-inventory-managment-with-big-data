#!/usr/bin/env python3
"""
Simple Spark Streaming Bridge for Kafka to ClickHouse
This is a simplified version that focuses on getting the data flowing
"""

import logging
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleStreamingBridge:
    """Simple streaming bridge for processing both sales and inventory events"""
    
    def __init__(self):
        self.spark = None
        self.job_id = str(uuid.uuid4())[:8]
        
    def initialize_spark_session(self):
        """Initialize Spark session with unified configurations"""
        try:
            self.spark = SparkSession.builder \
                .appName(f"SimpleStreamingBridge-{self.job_id}") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.streaming.backpressure.enabled", "true") \
                .config("spark.streaming.kafka.maxRatePerPartition", "50") \
                .getOrCreate()
            
            logger.info("Simple Spark session initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def define_sales_schema(self):
        """Define schema for sales events"""
        return StructType([
            StructField("transaction_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("unit_price", DoubleType(), True),
            StructField("total_amount", DoubleType(), True),
            StructField("timestamp", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("payment_method", StringType(), True),
            StructField("store_region", StringType(), True),
            StructField("product_category", StringType(), True)
        ])
    
    def define_inventory_schema(self):
        """Define schema for inventory events"""
        return StructType([
            StructField("inventory_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("quantity_change", IntegerType(), True),
            StructField("new_quantity", IntegerType(), True),
            StructField("previous_quantity", IntegerType(), True),
            StructField("reason", StringType(), True),
            StructField("timestamp", StringType(), True)
        ])
    
    def process_sales_stream(self):
        """Process sales data stream and write to console for testing"""
        try:
            # Read from Kafka
            sales_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "retail-sales-transactions") \
                .option("startingOffsets", "latest") \
                .load()
            
            # Parse JSON and process
            parsed_sales = sales_df \
                .select(
                    col("key").cast("string"),
                    col("value").cast("string"),
                    col("timestamp")
                ) \
                .withColumn("parsed_data", from_json(col("value"), self.define_sales_schema())) \
                .select(
                    col("parsed_data.transaction_id").alias("sale_id"),
                    col("parsed_data.store_id"),
                    col("parsed_data.product_id"),
                    col("parsed_data.quantity"),
                    col("parsed_data.total_amount"),
                    to_timestamp(col("parsed_data.timestamp")).alias("sale_timestamp"),
                    col("timestamp").alias("kafka_timestamp")
                )
            
            # Write to console for testing
            query = parsed_sales \
                .writeStream \
                .outputMode("append") \
                .format("console") \
                .option("truncate", "false") \
                .start()
            
            logger.info("Sales streaming query started")
            return query
            
        except Exception as e:
            logger.error(f"Error processing sales stream: {e}")
            raise
    
    def process_inventory_stream(self):
        """Process inventory data stream and write to console for testing"""
        try:
            # Read from Kafka
            inventory_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:19092") \
                .option("subscribe", "retail-inventory-updates") \
                .option("startingOffsets", "latest") \
                .load()
            
            # Parse JSON and process
            parsed_inventory = inventory_df \
                .select(
                    col("key").cast("string"),
                    col("value").cast("string"),
                    col("timestamp")
                ) \
                .withColumn("parsed_data", from_json(col("value"), self.define_inventory_schema())) \
                .select(
                    col("parsed_data.inventory_id"),
                    col("parsed_data.store_id"),
                    col("parsed_data.product_id"),
                    col("parsed_data.quantity_change"),
                    col("parsed_data.new_quantity").alias("current_stock"),
                    to_timestamp(col("parsed_data.timestamp")).alias("update_timestamp"),
                    col("timestamp").alias("kafka_timestamp")
                )
            
            # Write to console for testing
            query = parsed_inventory \
                .writeStream \
                .outputMode("append") \
                .format("console") \
                .option("truncate", "false") \
                .start()
            
            logger.info("Inventory streaming query started")
            return query
            
        except Exception as e:
            logger.error(f"Error processing inventory stream: {e}")
            raise
    
    def process_streams(self):
        """Main method to process streaming data"""
        if not self.initialize_spark_session():
            return
        
        try:
            logger.info("Starting streaming processing...")
            
            # Start sales stream
            sales_query = self.process_sales_stream()
            
            # Start inventory stream
            inventory_query = self.process_inventory_stream()
            
            logger.info("Both streaming queries started successfully")
            logger.info("Streaming data from Kafka to console...")
            
            # Wait for termination
            sales_query.awaitTermination()
            inventory_query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in streaming processing: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def main():
    """Main entry point"""
    bridge = SimpleStreamingBridge()
    bridge.process_streams()

if __name__ == "__main__":
    main()