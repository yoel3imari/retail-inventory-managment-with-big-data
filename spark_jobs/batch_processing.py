#!/usr/bin/env python3
"""
Spark Batch Processing Application for Daily Aggregations

This application:
1. Processes daily sales and inventory data
2. Generates business intelligence reports
3. Calculates key performance indicators (KPIs)
4. Updates materialized views in ClickHouse
"""

import json
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchProcessing:
    """Batch processing for daily aggregations and reports"""
    
    def __init__(self):
        self.spark = None
        
    def initialize_spark_session(self):
        """Initialize Spark session for batch processing"""
        try:
            self.spark = SparkSession.builder \
                .appName("RetailBatchProcessing") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128m") \
                .config("spark.jars.packages", 
                       "com.clickhouse:clickhouse-jdbc:0.4.6") \
                .getOrCreate()
            
            logger.info("Spark session for batch processing initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def load_batch_data(self):
        """Load data for batch processing"""
        try:
            # Load sales data
            sales_df = self.spark.read \
                .format("jdbc") \
                .option("url", "jdbc:clickhouse://clickhouse:8123/default") \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .option("user", "default") \
                .option("password", "clickhouse") \
                .option("dbtable", "sales_fact") \
                .load()
            
            # Load inventory data
            inventory_df = self.spark.read \
                .format("jdbc") \
                .option("url", "jdbc:clickhouse://clickhouse:8123/default") \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .option("user", "default") \
                .option("password", "clickhouse") \
                .option("dbtable", "inventory_fact") \
                .load()
            
            # Load dimension tables
            products_df = self.spark.read \
                .format("jdbc") \
                .option("url", "jdbc:clickhouse://clickhouse:8123/default") \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .option("user", "default") \
                .option("password", "clickhouse") \
                .option("dbtable", "products_dim") \
                .load()
            
            stores_df = self.spark.read \
                .format("jdbc") \
                .option("url", "jdbc:clickhouse://clickhouse:8123/default") \
                .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                .option("user", "default") \
                .option("password", "clickhouse") \
                .option("dbtable", "stores_dim") \
                .load()
            
            logger.info("Batch data loaded successfully")
            return sales_df, inventory_df, products_df, stores_df
            
        except Exception as e:
            logger.error(f"Failed to load batch data: {e}")
            raise
    
    def calculate_daily_sales_kpis(self, sales_df, products_df, stores_df):
        """Calculate daily sales KPIs"""
        try:
            # Join with dimension tables
            enriched_sales = sales_df \
                .join(products_df, "product_id", "left") \
                .join(stores_df, "store_id", "left")
            
            # Daily sales aggregations
            daily_sales = enriched_sales \
                .withColumn("sale_date", to_date("sale_timestamp")) \
                .groupBy("sale_date", "store_id", "store_region", "product_id", "category_id", "brand") \
                .agg(
                    sum("quantity").alias("daily_quantity"),
                    sum("total_amount").alias("daily_revenue"),
                    count("sale_id").alias("daily_transactions"),
                    approx_count_distinct("customer_id").alias("daily_customers"),
                    avg("unit_price").alias("avg_unit_price")
                ) \
                .withColumn("avg_transaction_value", 
                           col("daily_revenue") / col("daily_transactions")) \
                .withColumn("revenue_per_customer", 
                           col("daily_revenue") / col("daily_customers"))
            
            logger.info("Daily sales KPIs calculated successfully")
            return daily_sales
            
        except Exception as e:
            logger.error(f"Failed to calculate daily sales KPIs: {e}")
            raise
    
    def calculate_inventory_kpis(self, inventory_df, products_df):
        """Calculate inventory KPIs"""
        try:
            # Join with product information
            enriched_inventory = inventory_df \
                .join(products_df, "product_id", "left")
            
            # Latest inventory status
            window_spec = Window.partitionBy("store_id", "product_id") \
                              .orderBy(desc("update_timestamp"))
            
            latest_inventory = enriched_inventory \
                .withColumn("row_num", row_number().over(window_spec)) \
                .filter(col("row_num") == 1) \
                .drop("row_num")
            
            # Inventory KPIs
            inventory_kpis = latest_inventory \
                .groupBy("store_id", "category_id", "brand") \
                .agg(
                    sum("current_stock").alias("total_stock"),
                    sum(when(col("current_stock") <= 0, 1).otherwise(0)).alias("out_of_stock_items"),
                    sum(when(col("current_stock") <= col("reorder_point"), 1).otherwise(0)).alias("low_stock_items"),
                    avg("current_stock").alias("avg_stock_level"),
                    count("product_id").alias("total_products")
                ) \
                .withColumn("out_of_stock_rate", 
                           (col("out_of_stock_items") / col("total_products")) * 100) \
                .withColumn("low_stock_rate", 
                           (col("low_stock_items") / col("total_products")) * 100)
            
            logger.info("Inventory KPIs calculated successfully")
            return inventory_kpis
            
        except Exception as e:
            logger.error(f"Failed to calculate inventory KPIs: {e}")
            raise
    
    def calculate_product_performance(self, sales_df, products_df):
        """Calculate product performance metrics"""
        try:
            # Product sales performance
            product_performance = sales_df \
                .join(products_df, "product_id", "left") \
                .groupBy("product_id", "product_name", "category_id", "brand") \
                .agg(
                    sum("quantity").alias("total_quantity_sold"),
                    sum("total_amount").alias("total_revenue"),
                    count("sale_id").alias("total_transactions"),
                    approx_count_distinct("customer_id").alias("unique_customers"),
                    avg("unit_price").alias("avg_selling_price"),
                    min("sale_timestamp").alias("first_sale_date"),
                    max("sale_timestamp").alias("last_sale_date")
                ) \
                .withColumn("avg_quantity_per_transaction", 
                           col("total_quantity_sold") / col("total_transactions")) \
                .withColumn("revenue_per_transaction", 
                           col("total_revenue") / col("total_transactions")) \
                .withColumn("customer_penetration_rate", 
                           (col("unique_customers") / 1000) * 100)  # Assuming 1000 total customers
            
            # Calculate product rankings
            window_spec_revenue = Window.orderBy(desc("total_revenue"))
            window_spec_quantity = Window.orderBy(desc("total_quantity_sold"))
            
            ranked_products = product_performance \
                .withColumn("revenue_rank", dense_rank().over(window_spec_revenue)) \
                .withColumn("quantity_rank", dense_rank().over(window_spec_quantity)) \
                .withColumn("performance_score", 
                           (100 - col("revenue_rank") + 100 - col("quantity_rank")) / 2)
            
            logger.info("Product performance metrics calculated successfully")
            return ranked_products
            
        except Exception as e:
            logger.error(f"Failed to calculate product performance: {e}")
            raise
    
    def calculate_store_performance(self, sales_df, stores_df):
        """Calculate store performance metrics"""
        try:
            # Store sales performance
            store_performance = sales_df \
                .join(stores_df, "store_id", "left") \
                .groupBy("store_id", "store_name", "store_region", "store_size") \
                .agg(
                    sum("total_amount").alias("total_revenue"),
                    count("sale_id").alias("total_transactions"),
                    approx_count_distinct("customer_id").alias("unique_customers"),
                    sum("quantity").alias("total_quantity_sold"),
                    avg("total_amount").alias("avg_transaction_value")
                ) \
                .withColumn("revenue_per_customer", 
                           col("total_revenue") / col("unique_customers")) \
                .withColumn("transactions_per_customer", 
                           col("total_transactions") / col("unique_customers")) \
                .withColumn("revenue_per_sqft", 
                           col("total_revenue") / col("store_size"))
            
            # Calculate store rankings
            window_spec_revenue = Window.orderBy(desc("total_revenue"))
            window_spec_efficiency = Window.orderBy(desc("revenue_per_sqft"))
            
            ranked_stores = store_performance \
                .withColumn("revenue_rank", dense_rank().over(window_spec_revenue)) \
                .withColumn("efficiency_rank", dense_rank().over(window_spec_efficiency)) \
                .withColumn("overall_score", 
                           (100 - col("revenue_rank") + 100 - col("efficiency_rank")) / 2)
            
            logger.info("Store performance metrics calculated successfully")
            return ranked_stores
            
        except Exception as e:
            logger.error(f"Failed to calculate store performance: {e}")
            raise
    
    def generate_daily_report(self, daily_sales, inventory_kpis, product_performance, store_performance):
        """Generate comprehensive daily report"""
        try:
            # Calculate overall business metrics
            total_revenue = daily_sales.agg(sum("daily_revenue")).collect()[0][0]
            total_transactions = daily_sales.agg(sum("daily_transactions")).collect()[0][0]
            total_customers = daily_sales.agg(sum("daily_customers")).collect()[0][0]
            
            # Inventory health metrics
            avg_out_of_stock_rate = inventory_kpis.agg(avg("out_of_stock_rate")).collect()[0][0]
            avg_low_stock_rate = inventory_kpis.agg(avg("low_stock_rate")).collect()[0][0]
            
            # Top performing products
            top_products = product_performance \
                .filter(col("revenue_rank") <= 10) \
                .select("product_name", "total_revenue", "total_quantity_sold", "revenue_rank") \
                .orderBy("revenue_rank")
            
            # Top performing stores
            top_stores = store_performance \
                .filter(col("revenue_rank") <= 5) \
                .select("store_name", "total_revenue", "revenue_per_sqft", "revenue_rank") \
                .orderBy("revenue_rank")
            
            # Compile daily report
            report_date = datetime.now().strftime("%Y-%m-%d")
            daily_report = {
                "report_date": report_date,
                "business_metrics": {
                    "total_revenue": total_revenue,
                    "total_transactions": total_transactions,
                    "total_customers": total_customers,
                    "avg_transaction_value": total_revenue / total_transactions if total_transactions > 0 else 0,
                    "revenue_per_customer": total_revenue / total_customers if total_customers > 0 else 0
                },
                "inventory_health": {
                    "avg_out_of_stock_rate": avg_out_of_stock_rate,
                    "avg_low_stock_rate": avg_low_stock_rate
                },
                "top_products_count": top_products.count(),
                "top_stores_count": top_stores.count(),
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Daily report generated for {report_date}")
            return daily_report
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            raise
    
    def save_results(self, daily_sales, inventory_kpis, product_performance, store_performance, daily_report):
        """Save batch processing results"""
        try:
            # Save to temporary storage (in production, this would save to ClickHouse)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Write results to local files (for demo purposes)
            daily_sales.write.mode("overwrite").parquet(f"/tmp/batch_results/daily_sales_{timestamp}")
            inventory_kpis.write.mode("overwrite").parquet(f"/tmp/batch_results/inventory_kpis_{timestamp}")
            product_performance.write.mode("overwrite").parquet(f"/tmp/batch_results/product_performance_{timestamp}")
            store_performance.write.mode("overwrite").parquet(f"/tmp/batch_results/store_performance_{timestamp}")
            
            # Save daily report as JSON
            import json
            with open(f"/tmp/batch_results/daily_report_{timestamp}.json", "w") as f:
                json.dump(daily_report, f, indent=2)
            
            logger.info("Batch processing results saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save batch processing results: {e}")
            raise
    
    def run_batch_processing(self):
        """Main method to run batch processing"""
        if not self.initialize_spark_session():
            return
        
        try:
            logger.info("Starting batch processing...")
            
            # Load data
            sales_df, inventory_df, products_df, stores_df = self.load_batch_data()
            
            # Calculate KPIs
            daily_sales = self.calculate_daily_sales_kpis(sales_df, products_df, stores_df)
            inventory_kpis = self.calculate_inventory_kpis(inventory_df, products_df)
            product_performance = self.calculate_product_performance(sales_df, products_df)
            store_performance = self.calculate_store_performance(sales_df, stores_df)
            
            # Generate daily report
            daily_report = self.generate_daily_report(daily_sales, inventory_kpis, product_performance, store_performance)
            
            # Save results
            self.save_results(daily_sales, inventory_kpis, product_performance, store_performance, daily_report)
            
            logger.info("Batch processing completed successfully")
            
            return daily_report
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def main():
    """Main entry point"""
    processor = BatchProcessing()
    report = processor.run_batch_processing()
    
    if report:
        logger.info(f"Batch processing completed. Report: {json.dumps(report, indent=2)}")

if __name__ == "__main__":
    main()