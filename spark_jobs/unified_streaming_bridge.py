#!/usr/bin/env python3
"""
Unified Spark Streaming Bridge for Kafka to ClickHouse

This application provides a unified streaming bridge that processes both sales and inventory
events from Kafka and writes processed data to ClickHouse tables in real-time.

Features:
- Multi-topic Kafka consumption (sales_events, inventory_events)
- Unified error handling and monitoring
- Real-time metrics aggregation
- Alert detection and notification
- ClickHouse integration for both raw and processed data
"""

import logging
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import DataFrame
from pyspark.sql.window import Window
from clickhouse_writer import create_clickhouse_writer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedStreamingBridge:
    """Unified streaming bridge for processing both sales and inventory events"""
    
    def __init__(self):
        self.spark = None
        self.clickhouse_writer = None
        self.job_id = str(uuid.uuid4())[:8]
        
        # Kafka configuration
        self.kafka_config = {
            "bootstrap.servers": "kafka:9092",
            "group.id": f"unified-bridge-group-{self.job_id}"
        }
        
        # Topics to subscribe to
        self.topics = ["retail-sales-transactions", "retail-inventory-updates"]
        
    def initialize_spark_session(self):
        """Initialize Spark session with unified configurations"""
        try:
            self.spark = SparkSession.builder \
                .appName(f"UnifiedStreamingBridge-{self.job_id}") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skew.enabled", "true") \
                .config("spark.streaming.backpressure.enabled", "true") \
                .config("spark.streaming.kafka.maxRatePerPartition", "75") \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                       "com.clickhouse:clickhouse-jdbc:0.4.6") \
                .getOrCreate()
            
            logger.info("Unified Spark session initialized successfully")
            
            # Initialize ClickHouse writer
            self.clickhouse_writer = create_clickhouse_writer(self.spark)
            logger.info("ClickHouse writer initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def define_sales_schema(self):
        """Define schema for sales events"""
        return StructType([
            StructField("sale_id", StringType(), True),
            StructField("store_id", StringType(), True),
            StructField("product_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("unit_price", DoubleType(), True),
            StructField("total_amount", DoubleType(), True),
            StructField("sale_timestamp", TimestampType(), True),
            StructField("payment_method", StringType(), True),
            StructField("promotion_id", StringType(), True)
        ])
    
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
    
    def read_from_kafka(self):
        """Read streaming data from multiple Kafka topics"""
        try:
            df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:9092") \
                .option("subscribe", ",".join(self.topics)) \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .load()
            
            logger.info(f"Successfully connected to Kafka topics: {self.topics}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read from Kafka topics: {e}")
            raise
    
    def parse_unified_data(self, kafka_df: DataFrame) -> DataFrame:
        """Parse JSON data from Kafka and apply appropriate schemas"""
        # Parse sales events separately
        sales_df = kafka_df \
            .filter(col("topic") == "retail-sales-transactions") \
            .select(
                col("topic"),
                col("key").cast("string"),
                col("value").cast("string"),
                col("timestamp")
            ) \
            .withColumn("parsed_data", from_json(col("value"), self.define_sales_schema())) \
            .filter(col("parsed_data").isNotNull())
        
        # Parse inventory events separately
        inventory_df = kafka_df \
            .filter(col("topic") == "retail-inventory-updates") \
            .select(
                col("topic"),
                col("key").cast("string"),
                col("value").cast("string"),
                col("timestamp")
            ) \
            .withColumn("parsed_data", from_json(col("value"), self.define_inventory_schema())) \
            .filter(col("parsed_data").isNotNull())
        
        # Return both dataframes separately - we'll process them individually
        return sales_df, inventory_df
    
    def process_sales_stream(self, sales_df: DataFrame) -> tuple:
        """Process sales data stream"""
        # Extract sales data
        sales_data = sales_df \
            .select(
                col("parsed_data.sale_id"),
                col("parsed_data.store_id"),
                col("parsed_data.product_id"),
                col("parsed_data.customer_id"),
                col("parsed_data.quantity"),
                col("parsed_data.unit_price"),
                col("parsed_data.total_amount"),
                col("parsed_data.sale_timestamp"),
                col("parsed_data.payment_method"),
                col("timestamp").alias("kafka_timestamp")
            )
        
        # Calculate real-time metrics
        sales_metrics = sales_data \
            .withWatermark("sale_timestamp", "1 minute") \
            .groupBy(
                window(col("sale_timestamp"), "5 minutes", "1 minute"),
                col("store_id"),
                col("product_id")
            ) \
            .agg(
                sum("quantity").alias("total_quantity"),
                sum("total_amount").alias("total_revenue"),
                avg("unit_price").alias("avg_unit_price"),
                count("sale_id").alias("transaction_count"),
                approx_count_distinct("customer_id").alias("unique_customers")
            ) \
            .withColumn("window_start", col("window.start")) \
            .withColumn("window_end", col("window.end")) \
            .drop("window")
        
        # Simple anomaly detection for streaming (avoid window functions)
        sales_anomalies = sales_data \
            .withColumn("is_anomaly",
                       when(col("total_amount") > 1000, True).otherwise(False))
        
        return sales_data, sales_metrics, sales_anomalies
    
    def process_inventory_stream(self, inventory_df: DataFrame) -> tuple:
        """Process inventory data stream"""
        # Extract inventory data
        inventory_data = inventory_df \
            .select(
                col("parsed_data.inventory_id"),
                col("parsed_data.store_id"),
                col("parsed_data.product_id"),
                col("parsed_data.current_stock"),
                col("parsed_data.minimum_stock"),
                col("parsed_data.maximum_stock"),
                col("parsed_data.reorder_point"),
                col("parsed_data.update_timestamp"),
                col("timestamp").alias("kafka_timestamp")
            )
        
        # Calculate inventory metrics
        inventory_metrics = inventory_data \
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
        
        # Simple inventory alerts for streaming (avoid window functions)
        inventory_alerts = inventory_data \
            .withColumn("alert_type",
                       when(col("current_stock") <= 0, "CRITICAL_OUT_OF_STOCK")
                       .when(col("current_stock") <= col("reorder_point"), "LOW_STOCK_ALERT")
                       .when(col("current_stock") > col("maximum_stock"), "OVERSTOCKED")
                       .otherwise("NORMAL")) \
            .withColumn("alert_severity",
                       when(col("alert_type") == "CRITICAL_OUT_OF_STOCK", "CRITICAL")
                       .when(col("alert_type") == "LOW_STOCK_ALERT", "HIGH")
                       .when(col("alert_type") == "OVERSTOCKED", "LOW")
                       .otherwise("INFO")) \
            .filter(col("alert_type") != "NORMAL")
        
        return inventory_data, inventory_metrics, inventory_alerts
    
    def write_sales_metrics_to_clickhouse(self, df: DataFrame, batch_id: int):
        """Write sales metrics to ClickHouse"""
        if self.clickhouse_writer:
            self.clickhouse_writer.write_sales_metrics(df, batch_id)
    
    def write_inventory_metrics_to_clickhouse(self, df: DataFrame, batch_id: int):
        """Write inventory metrics to ClickHouse"""
        if self.clickhouse_writer:
            self.clickhouse_writer.write_inventory_metrics(df, batch_id)
    
    def write_unified_alerts_to_clickhouse(self, df: DataFrame, batch_id: int):
        """Write unified alerts to ClickHouse"""
        if self.clickhouse_writer:
            alerts_df = df.select(
                col("alert_id"),
                col("alert_type"),
                col("alert_severity"),
                col("store_id"),
                col("product_id"),
                col("current_value"),
                col("threshold_value"),
                col("alert_message"),
                col("alert_timestamp")
            )
            
            self.clickhouse_writer.write_streaming_alerts(alerts_df, batch_id)
    
    def write_raw_events_to_clickhouse(self, df: DataFrame, batch_id: int):
        """Write raw events to ClickHouse for auditing"""
        if self.clickhouse_writer:
            raw_events_df = df.select(
                when(col("topic") == "retail-sales-transactions", col("sale_id"))
                 .when(col("topic") == "retail-inventory-updates", col("inventory_id"))
                 .alias("event_id"),
                col("topic"),
                when(col("topic") == "retail-sales-transactions", "SALES")
                 .when(col("topic") == "retail-inventory-updates", "INVENTORY")
                 .alias("event_type"),
                when(col("topic") == "retail-sales-transactions", col("sale_timestamp"))
                 .when(col("topic") == "retail-inventory-updates", col("update_timestamp"))
                 .alias("event_timestamp"),
                col("kafka_timestamp"),
                col("store_id"),
                col("product_id"),
                to_json(struct("*")).alias("payload")
            )
            
            # Write each event type separately
            sales_raw = raw_events_df.filter(col("event_type") == "SALES")
            inventory_raw = raw_events_df.filter(col("event_type") == "INVENTORY")
            
            if sales_raw.count() > 0:
                self.clickhouse_writer.write_raw_events(sales_raw, "SALES", batch_id)
            if inventory_raw.count() > 0:
                self.clickhouse_writer.write_raw_events(inventory_raw, "INVENTORY", batch_id)
    
    def process_unified_stream(self):
        """Main method to process unified streaming data"""
        if not self.initialize_spark_session():
            return
        
        try:
            # Update job monitoring
            self.clickhouse_writer.update_job_monitoring(
                "unified_streaming_bridge", "RUNNING", 0, "", f"/tmp/checkpoint/unified_bridge_{self.job_id}"
            )
            
            # Read from Kafka
            kafka_df = self.read_from_kafka()
            
            # Parse unified data
            sales_df, inventory_df = self.parse_unified_data(kafka_df)
            
            # Process sales stream
            sales_data, sales_metrics, sales_anomalies = self.process_sales_stream(sales_df)
            
            # Process inventory stream
            inventory_data, inventory_metrics, inventory_alerts = self.process_inventory_stream(inventory_df)
            
            # Prepare unified alerts
            sales_alerts = sales_anomalies.filter(col("is_anomaly") == True) \
                .select(
                    col("sale_id").alias("alert_id"),
                    lit("HIGH_VALUE_SALE").alias("alert_type"),
                    lit("HIGH").alias("alert_severity"),
                    col("store_id"),
                    col("product_id"),
                    col("total_amount").alias("current_value"),
                    lit(1000).alias("threshold_value"),
                    concat(
                        lit("High value sale detected: $"),
                        col("total_amount")
                    ).alias("alert_message"),
                    col("sale_timestamp").alias("alert_timestamp")
                )
            
            inventory_alerts_formatted = inventory_alerts.select(
                col("inventory_id").alias("alert_id"),
                col("alert_type"),
                col("alert_severity"),
                col("store_id"),
                col("product_id"),
                col("current_stock").alias("current_value"),
                col("reorder_point").alias("threshold_value"),
                concat(
                    lit("Inventory alert: "), 
                    col("alert_type"), 
                    lit(" - Current stock: "), 
                    col("current_stock"),
                    lit(", Reorder point: "),
                    col("reorder_point")
                ).alias("alert_message"),
                col("update_timestamp").alias("alert_timestamp")
            )
            
            # Combine all alerts
            unified_alerts = sales_alerts.unionByName(inventory_alerts_formatted)
            
            # Write to ClickHouse
            sales_metrics_query = sales_metrics \
                .writeStream \
                .outputMode("update") \
                .foreachBatch(self.write_sales_metrics_to_clickhouse) \
                .option("checkpointLocation", f"/tmp/checkpoint/unified_sales_metrics_{self.job_id}") \
                .start()
            
            inventory_metrics_query = inventory_metrics \
                .writeStream \
                .outputMode("update") \
                .foreachBatch(self.write_inventory_metrics_to_clickhouse) \
                .option("checkpointLocation", f"/tmp/checkpoint/unified_inventory_metrics_{self.job_id}") \
                .start()
            
            alerts_query = unified_alerts \
                .writeStream \
                .outputMode("update") \
                .foreachBatch(self.write_unified_alerts_to_clickhouse) \
                .option("checkpointLocation", f"/tmp/checkpoint/unified_alerts_{self.job_id}") \
                .start()
            
            # Combine raw data for auditing
            raw_combined = sales_data.unionByName(
                inventory_data.select(
                    col("inventory_id").alias("sale_id"),  # Map to common schema
                    col("store_id"),
                    col("product_id"),
                    lit(None).cast(StringType()).alias("customer_id"),
                    lit(0).cast(IntegerType()).alias("quantity"),
                    lit(0.0).cast(DoubleType()).alias("unit_price"),
                    lit(0.0).cast(DoubleType()).alias("total_amount"),
                    col("update_timestamp").alias("sale_timestamp"),
                    lit(None).cast(StringType()).alias("payment_method"),
                    col("kafka_timestamp")
                )
            ).withColumn("topic", lit("combined"))
            
            raw_events_query = raw_combined \
                .writeStream \
                .outputMode("append") \
                .foreachBatch(self.write_raw_events_to_clickhouse) \
                .option("checkpointLocation", f"/tmp/checkpoint/unified_raw_{self.job_id}") \
                .start()
            
            logger.info("Unified streaming bridge processing started")
            
            # Wait for termination
            sales_metrics_query.awaitTermination()
            inventory_metrics_query.awaitTermination()
            alerts_query.awaitTermination()
            raw_events_query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in unified streaming processing: {e}")
            if self.clickhouse_writer:
                self.clickhouse_writer.update_job_monitoring(
                    "unified_streaming_bridge", "FAILED", 0, str(e), f"/tmp/checkpoint/unified_bridge_{self.job_id}"
                )
            raise
        finally:
            if self.spark:
                if self.clickhouse_writer:
                    self.clickhouse_writer.update_job_monitoring(
                        "unified_streaming_bridge", "COMPLETED", 0, "", f"/tmp/checkpoint/unified_bridge_{self.job_id}"
                    )
                self.spark.stop()

def main():
    """Main entry point"""
    bridge = UnifiedStreamingBridge()
    bridge.process_unified_stream()

if __name__ == "__main__":
    main()