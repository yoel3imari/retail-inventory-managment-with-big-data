#!/usr/bin/env python3
"""
Spark Streaming Application for Real-time Inventory Data Processing

This application:
1. Consumes inventory events from Kafka
2. Tracks stock levels in real-time
3. Detects low stock and out-of-stock situations
4. Calculates inventory turnover metrics
5. Writes processed data to ClickHouse
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import DataFrame
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InventoryStreamingProcessor:
    """Real-time inventory data streaming processor"""
    
    def __init__(self):
        self.spark = None
        self.kafka_params = {
            "bootstrap.servers": "kafka:9092",
            "group.id": "inventory-streaming-group"
        }
        
    def initialize_spark_session(self):
        """Initialize Spark session with necessary configurations"""
        try:
            self.spark = SparkSession.builder \
                .appName("RetailInventoryStreaming") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.streaming.backpressure.enabled", "true") \
                .config("spark.streaming.kafka.maxRatePerPartition", "50") \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                       "com.clickhouse:clickhouse-jdbc:0.4.6") \
                .getOrCreate()
            
            logger.info("Spark session initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def define_inventory_schema(self):
        """Define schema for inventory events"""
        return StructType([
            StructField("inventory_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("current_stock", IntegerType(), True),
            StructField("minimum_stock", IntegerType(), True),
            StructField("maximum_stock", IntegerType(), True),
            StructField("reorder_point", IntegerType(), True),
            StructField("last_restock_date", TimestampType(), True),
            StructField("next_restock_date", TimestampType(), True),
            StructField("update_timestamp", TimestampType(), True)
        ])
    
    def read_from_kafka(self, topic: str) -> DataFrame:
        """Read streaming data from Kafka topic"""
        try:
            df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:9092") \
                .option("subscribe", topic) \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .load()
            
            logger.info(f"Successfully connected to Kafka topic: {topic}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read from Kafka topic {topic}: {e}")
            raise
    
    def parse_inventory_data(self, kafka_df: DataFrame) -> DataFrame:
        """Parse JSON data from Kafka and apply schema"""
        schema = self.define_inventory_schema()
        
        parsed_df = kafka_df \
            .select(
                col("key").cast("string"),
                col("value").cast("string"),
                col("timestamp")
            ) \
            .withColumn("parsed_value", from_json(col("value"), schema)) \
            .select(
                col("parsed_value.inventory_id"),
                col("parsed_value.store_id"),
                col("parsed_value.product_id"),
                col("parsed_value.current_stock"),
                col("parsed_value.minimum_stock"),
                col("parsed_value.maximum_stock"),
                col("parsed_value.reorder_point"),
                col("parsed_value.last_restock_date"),
                col("parsed_value.next_restock_date"),
                col("parsed_value.update_timestamp"),
                col("timestamp").alias("kafka_timestamp")
            ) \
            .filter(col("inventory_id").isNotNull())  # Filter out invalid records
        
        return parsed_df
    
    def calculate_stock_metrics(self, inventory_df: DataFrame) -> DataFrame:
        """Calculate real-time inventory metrics"""
        metrics_df = inventory_df \
            .withWatermark("update_timestamp", "2 minutes") \
            .groupBy(
                window(col("update_timestamp"), "10 minutes", "2 minutes"),
                col("store_id"),
                col("product_id")
            ) \
            .agg(
                last("current_stock").alias("latest_stock"),
                last("minimum_stock").alias("min_stock"),
                last("maximum_stock").alias("max_stock"),
                last("reorder_point").alias("reorder_level"),
                count("inventory_id").alias("update_count"),
                min("current_stock").alias("min_observed_stock"),
                max("current_stock").alias("max_observed_stock")
            ) \
            .withColumn("window_start", col("window.start")) \
            .withColumn("window_end", col("window.end")) \
            .withColumn("stock_status", 
                       when(col("latest_stock") <= 0, "OUT_OF_STOCK")
                       .when(col("latest_stock") <= col("reorder_level"), "LOW_STOCK")
                       .otherwise("IN_STOCK")) \
            .withColumn("stock_percentage", 
                       (col("latest_stock") / col("max_stock")) * 100) \
            .drop("window")
        
        return metrics_df
    
    def detect_stock_alerts(self, inventory_df: DataFrame) -> DataFrame:
        """Detect stock alerts and critical situations"""
        # Define window for trend analysis
        window_spec = Window.partitionBy("store_id", "product_id") \
                          .orderBy("update_timestamp") \
                          .rowsBetween(-5, 0)
        
        alert_df = inventory_df \
            .withColumn("prev_stock", 
                       lag("current_stock").over(window_spec)) \
            .withColumn("stock_change", 
                       col("current_stock") - col("prev_stock")) \
            .withColumn("stock_change_rate", 
                       when(col("prev_stock") > 0, 
                           (col("stock_change") / col("prev_stock")) * 100)
                       .otherwise(0)) \
            .withColumn("alert_type",
                       when(col("current_stock") <= 0, "CRITICAL_OUT_OF_STOCK")
                       .when(col("current_stock") <= col("reorder_point"), "LOW_STOCK_ALERT")
                       .when(col("stock_change_rate") < -50, "RAPID_DEPLETION")
                       .when(col("current_stock") > col("maximum_stock"), "OVERSTOCKED")
                       .otherwise("NORMAL")) \
            .withColumn("alert_severity",
                       when(col("alert_type") == "CRITICAL_OUT_OF_STOCK", "CRITICAL")
                       .when(col("alert_type") == "LOW_STOCK_ALERT", "HIGH")
                       .when(col("alert_type") == "RAPID_DEPLETION", "MEDIUM")
                       .when(col("alert_type") == "OVERSTOCKED", "LOW")
                       .otherwise("INFO")) \
            .filter(col("alert_type") != "NORMAL")  # Only show alerts
        
        return alert_df
    
    def calculate_turnover_metrics(self, inventory_df: DataFrame) -> DataFrame:
        """Calculate inventory turnover and performance metrics"""
        # This would typically integrate with sales data
        # For now, we'll calculate basic turnover indicators
        
        turnover_df = inventory_df \
            .withWatermark("update_timestamp", "5 minutes") \
            .groupBy(
                window(col("update_timestamp"), "30 minutes", "5 minutes"),
                col("store_id"),
                col("product_id")
            ) \
            .agg(
                avg("current_stock").alias("avg_stock_level"),
                stddev("current_stock").alias("stock_volatility"),
                count("inventory_id").alias("stock_updates"),
                (sum(when(col("current_stock") <= col("reorder_point"), 1).otherwise(0)) / 
                 count("*") * 100).alias("low_stock_percentage")
            ) \
            .withColumn("window_start", col("window.start")) \
            .withColumn("window_end", col("window.end")) \
            .drop("window")
        
        return turnover_df
    
    def write_to_console(self, df: DataFrame, output_name: str):
        """Write streaming data to console for monitoring"""
        query = df \
            .writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", "false") \
            .option("checkpointLocation", f"/tmp/checkpoint/inventory_{output_name}") \
            .start()
        
        return query
    
    def process_inventory_stream(self):
        """Main method to process inventory streaming data"""
        if not self.initialize_spark_session():
            return
        
        try:
            # Read from Kafka
            kafka_df = self.read_from_kafka("inventory_events")
            
            # Parse and process data
            inventory_df = self.parse_inventory_data(kafka_df)
            
            # Calculate real-time metrics
            metrics_df = self.calculate_stock_metrics(inventory_df)
            
            # Detect stock alerts
            alert_df = self.detect_stock_alerts(inventory_df)
            
            # Calculate turnover metrics
            turnover_df = self.calculate_turnover_metrics(inventory_df)
            
            # Write to console for demonstration
            console_query_metrics = self.write_to_console(metrics_df, "metrics")
            console_query_alerts = self.write_to_console(alert_df, "alerts")
            console_query_turnover = self.write_to_console(turnover_df, "turnover")
            
            logger.info("Inventory streaming processing started")
            
            # Wait for termination
            console_query_metrics.awaitTermination()
            console_query_alerts.awaitTermination()
            console_query_turnover.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in inventory streaming processing: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def main():
    """Main entry point"""
    processor = InventoryStreamingProcessor()
    processor.process_inventory_stream()

if __name__ == "__main__":
    main()