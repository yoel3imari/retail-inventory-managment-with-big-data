#!/usr/bin/env python3
"""
ClickHouse Writer Utility for Spark Streaming Jobs

This module provides a reusable ClickHouse writer for Spark streaming applications
that bridges Kafka data to ClickHouse tables.
"""

import logging
from pyspark.sql import DataFrame
from pyspark.sql.functions import lit, current_timestamp
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClickHouseWriter:
    """ClickHouse writer utility for Spark streaming jobs"""
    
    def __init__(self, spark_session):
        self.spark = spark_session
        self.clickhouse_config = {
            "url": "jdbc:clickhouse://clickhouse:8123/retail",
            "driver": "com.clickhouse.jdbc.ClickHouseDriver",
            "user": "default",
            "password": "clickhouse"
        }
    
    def write_sales_metrics(self, df: DataFrame, batch_id: int = None) -> None:
        """Write sales metrics to ClickHouse"""
        try:
            if df.count() > 0:
                # Add batch metadata
                enriched_df = df \
                    .withColumn("processing_timestamp", current_timestamp()) \
                    .withColumn("spark_job_id", lit(f"sales_streaming_{batch_id or 'live'}"))
                
                # Write to ClickHouse
                enriched_df.write \
                    .format("jdbc") \
                    .option("url", self.clickhouse_config["url"]) \
                    .option("driver", self.clickhouse_config["driver"]) \
                    .option("dbtable", "spark_sales_metrics") \
                    .option("user", self.clickhouse_config["user"]) \
                    .option("password", self.clickhouse_config["password"]) \
                    .mode("append") \
                    .save()
                
                logger.info(f"Successfully wrote {df.count()} sales metrics records to ClickHouse")
            else:
                logger.info("No sales metrics to write to ClickHouse")
                
        except Exception as e:
            logger.error(f"Failed to write sales metrics to ClickHouse: {e}")
            raise
    
    def write_inventory_metrics(self, df: DataFrame, batch_id: int = None) -> None:
        """Write inventory metrics to ClickHouse"""
        try:
            if df.count() > 0:
                # Add batch metadata
                enriched_df = df \
                    .withColumn("processing_timestamp", current_timestamp()) \
                    .withColumn("spark_job_id", lit(f"inventory_streaming_{batch_id or 'live'}"))
                
                # Write to ClickHouse
                enriched_df.write \
                    .format("jdbc") \
                    .option("url", self.clickhouse_config["url"]) \
                    .option("driver", self.clickhouse_config["driver"]) \
                    .option("dbtable", "spark_inventory_metrics") \
                    .option("user", self.clickhouse_config["user"]) \
                    .option("password", self.clickhouse_config["password"]) \
                    .mode("append") \
                    .save()
                
                logger.info(f"Successfully wrote {df.count()} inventory metrics records to ClickHouse")
            else:
                logger.info("No inventory metrics to write to ClickHouse")
                
        except Exception as e:
            logger.error(f"Failed to write inventory metrics to ClickHouse: {e}")
            raise
    
    def write_streaming_alerts(self, df: DataFrame, batch_id: int = None) -> None:
        """Write streaming alerts to ClickHouse"""
        try:
            if df.count() > 0:
                # Add batch metadata
                enriched_df = df \
                    .withColumn("processing_timestamp", current_timestamp()) \
                    .withColumn("spark_job_id", lit(f"streaming_alerts_{batch_id or 'live'}"))
                
                # Write to ClickHouse
                enriched_df.write \
                    .format("jdbc") \
                    .option("url", self.clickhouse_config["url"]) \
                    .option("driver", self.clickhouse_config["driver"]) \
                    .option("dbtable", "spark_streaming_alerts") \
                    .option("user", self.clickhouse_config["user"]) \
                    .option("password", self.clickhouse_config["password"]) \
                    .mode("append") \
                    .save()
                
                logger.info(f"Successfully wrote {df.count()} alert records to ClickHouse")
            else:
                logger.info("No alerts to write to ClickHouse")
                
        except Exception as e:
            logger.error(f"Failed to write alerts to ClickHouse: {e}")
            raise
    
    def write_raw_events(self, df: DataFrame, event_type: str, batch_id: int = None) -> None:
        """Write raw events to ClickHouse for auditing"""
        try:
            if df.count() > 0:
                # Add metadata for raw events
                enriched_df = df \
                    .withColumn("event_type", lit(event_type)) \
                    .withColumn("processed_at", current_timestamp()) \
                    .withColumn("processing_batch", lit(f"batch_{batch_id or 'live'}"))
                
                # Write to ClickHouse
                enriched_df.write \
                    .format("jdbc") \
                    .option("url", self.clickhouse_config["url"]) \
                    .option("driver", self.clickhouse_config["driver"]) \
                    .option("dbtable", "streaming_events_raw") \
                    .option("user", self.clickhouse_config["user"]) \
                    .option("password", self.clickhouse_config["password"]) \
                    .mode("append") \
                    .save()
                
                logger.info(f"Successfully wrote {df.count()} raw {event_type} events to ClickHouse")
            else:
                logger.info(f"No raw {event_type} events to write to ClickHouse")
                
        except Exception as e:
            logger.error(f"Failed to write raw {event_type} events to ClickHouse: {e}")
            raise
    
    def update_job_monitoring(self, job_name: str, status: str, records_processed: int = 0, 
                            error_message: str = "", checkpoint_location: str = "") -> None:
        """Update job monitoring table in ClickHouse"""
        try:
            from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
            from datetime import datetime
            
            # Create monitoring record
            monitoring_data = [
                (f"job_{int(datetime.now().timestamp())}", job_name, datetime.now(), 
                 datetime.now() if status == "COMPLETED" else None, status, 
                 records_processed, 0, error_message, checkpoint_location, datetime.now())
            ]
            
            schema = StructType([
                StructField("job_id", StringType(), True),
                StructField("job_name", StringType(), True),
                StructField("start_time", TimestampType(), True),
                StructField("end_time", TimestampType(), True),
                StructField("status", StringType(), True),
                StructField("records_processed", IntegerType(), True),
                StructField("processing_duration_seconds", IntegerType(), True),
                StructField("error_message", StringType(), True),
                StructField("checkpoint_location", StringType(), True),
                StructField("last_updated", TimestampType(), True)
            ])
            
            monitoring_df = self.spark.createDataFrame(monitoring_data, schema)
            
            # Write to ClickHouse
            monitoring_df.write \
                .format("jdbc") \
                .option("url", self.clickhouse_config["url"]) \
                .option("driver", self.clickhouse_config["driver"]) \
                .option("dbtable", "spark_job_monitoring") \
                .option("user", self.clickhouse_config["user"]) \
                .option("password", self.clickhouse_config["password"]) \
                .mode("append") \
                .save()
            
            logger.info(f"Updated job monitoring for {job_name} with status {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job monitoring: {e}")

def create_clickhouse_writer(spark_session):
    """Factory function to create ClickHouse writer"""
    return ClickHouseWriter(spark_session)