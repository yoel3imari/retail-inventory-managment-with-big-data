#!/usr/bin/env python3
"""
Spark Streaming Application for Real-time Sales Data Processing

This application:
1. Consumes sales events from Kafka
2. Performs real-time aggregations
3. Detects anomalies and patterns
4. Writes processed data to ClickHouse
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import DataFrame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SalesStreamingProcessor:
    """Real-time sales data streaming processor"""
    
    def __init__(self):
        self.spark = None
        self.ssc = None
        self.kafka_params = {
            "bootstrap.servers": "kafka:9092",
            "group.id": "sales-streaming-group"
        }
        
    def initialize_spark_session(self):
        """Initialize Spark session with necessary configurations"""
        try:
            self.spark = SparkSession.builder \
                .appName("RetailSalesStreaming") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skew.enabled", "true") \
                .config("spark.streaming.backpressure.enabled", "true") \
                .config("spark.streaming.kafka.maxRatePerPartition", "100") \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                       "com.clickhouse:clickhouse-jdbc:0.4.6,"
                       "ru.yandex.clickhouse:clickhouse-jdbc:0.3.2") \
                .getOrCreate()
            
            logger.info("Spark session initialized successfully")
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
    
    def parse_sales_data(self, kafka_df: DataFrame) -> DataFrame:
        """Parse JSON data from Kafka and apply schema"""
        schema = self.define_sales_schema()
        
        parsed_df = kafka_df \
            .select(
                col("key").cast("string"),
                col("value").cast("string"),
                col("timestamp")
            ) \
            .withColumn("parsed_value", from_json(col("value"), schema)) \
            .select(
                col("parsed_value.sale_id"),
                col("parsed_value.store_id"),
                col("parsed_value.product_id"),
                col("parsed_value.customer_id"),
                col("parsed_value.quantity"),
                col("parsed_value.unit_price"),
                col("parsed_value.total_amount"),
                col("parsed_value.sale_timestamp"),
                col("parsed_value.payment_method"),
                col("parsed_value.promotion_id"),
                col("timestamp").alias("kafka_timestamp")
            ) \
            .filter(col("sale_id").isNotNull())  # Filter out invalid records
        
        return parsed_df
    
    def calculate_realtime_metrics(self, sales_df: DataFrame) -> DataFrame:
        """Calculate real-time sales metrics"""
        metrics_df = sales_df \
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
        
        return metrics_df
    
    def detect_anomalies(self, sales_df: DataFrame) -> DataFrame:
        """Detect anomalies in sales data"""
        # Calculate moving averages for anomaly detection
        window_spec = Window.partitionBy("store_id", "product_id") \
                          .orderBy("sale_timestamp") \
                          .rowsBetween(-10, 0)
        
        anomaly_df = sales_df \
            .withColumn("moving_avg", 
                       avg("total_amount").over(window_spec)) \
            .withColumn("std_dev", 
                       stddev("total_amount").over(window_spec)) \
            .withColumn("anomaly_score", 
                       abs((col("total_amount") - col("moving_avg")) / 
                          greatest(col("std_dev"), lit(0.001)))) \
            .withColumn("is_anomaly", 
                       when(col("anomaly_score") > 3, True).otherwise(False))
        
        return anomaly_df
    
    def write_to_clickhouse(self, df: DataFrame, table_name: str):
        """Write streaming data to ClickHouse"""
        query = df \
            .writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", "false") \
            .option("checkpointLocation", f"/tmp/checkpoint/{table_name}") \
            .start()
        
        # For production, uncomment the ClickHouse writer:
        # query = df \
        #     .writeStream \
        #     .outputMode("update") \
        #     .format("jdbc") \
        #     .option("url", "jdbc:clickhouse://clickhouse:8123/default") \
        #     .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
        #     .option("dbtable", table_name) \
        #     .option("user", "default") \
        #     .option("password", "clickhouse") \
        #     .option("checkpointLocation", f"/tmp/checkpoint/{table_name}") \
        #     .start()
        
        return query
    
    def process_sales_stream(self):
        """Main method to process sales streaming data"""
        if not self.initialize_spark_session():
            return
        
        try:
            # Read from Kafka
            kafka_df = self.read_from_kafka("sales_events")
            
            # Parse and process data
            sales_df = self.parse_sales_data(kafka_df)
            
            # Calculate real-time metrics
            metrics_df = self.calculate_realtime_metrics(sales_df)
            
            # Detect anomalies
            anomaly_df = self.detect_anomalies(sales_df)
            
            # Write to console for demonstration
            console_query_metrics = metrics_df \
                .writeStream \
                .outputMode("update") \
                .format("console") \
                .option("truncate", "false") \
                .start()
            
            console_query_anomalies = anomaly_df \
                .writeStream \
                .outputMode("update") \
                .format("console") \
                .option("truncate", "false") \
                .start()
            
            logger.info("Sales streaming processing started")
            
            # Wait for termination
            console_query_metrics.awaitTermination()
            console_query_anomalies.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in sales streaming processing: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def main():
    """Main entry point"""
    processor = SalesStreamingProcessor()
    processor.process_sales_stream()

if __name__ == "__main__":
    main()