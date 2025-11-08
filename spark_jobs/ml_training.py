#!/usr/bin/env python3
"""
Spark ML Training Application for Demand Forecasting and Stock Optimization

This application:
1. Trains machine learning models for demand forecasting
2. Optimizes inventory levels using ML algorithms
3. Generates predictions for future demand
4. Saves trained models to MinIO for deployment
"""

import logging
import os
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler, StringIndexer, OneHotEncoder
from pyspark.ml.regression import RandomForestRegressor, GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLTrainingProcessor:
    """Machine Learning model training processor"""
    
    def __init__(self):
        self.spark = None
        self.models = {}
        
    def initialize_spark_session(self):
        """Initialize Spark session with ML configurations"""
        try:
            self.spark = SparkSession.builder \
                .appName("RetailMLTraining") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.executor.memory", "2g") \
                .config("spark.driver.memory", "2g") \
                .config("spark.jars.packages",
                       "com.clickhouse:clickhouse-jdbc:0.4.6") \
                .config("spark.jars.repositories", "https://repo1.maven.org/maven2/") \
                .getOrCreate()
            
            logger.info("Spark session for ML training initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            return False
    
    def load_training_data(self):
        """Load historical data for model training"""
        try:
            # Load sales data from ClickHouse
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
            
            # Load product and store dimensions
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
            
            logger.info("Training data loaded successfully")
            return sales_df, inventory_df, products_df, stores_df
            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            raise
    
    def prepare_demand_forecasting_data(self, sales_df, products_df, stores_df):
        """Prepare data for demand forecasting model"""
        try:
            # Aggregate sales by product, store, and time period
            demand_data = sales_df \
                .join(products_df, "product_id", "left") \
                .join(stores_df, "store_id", "left") \
                .groupBy(
                    "product_id", 
                    "store_id", 
                    "category_id",
                    "brand",
                    "store_region",
                    window(col("sale_timestamp"), "1 day").alias("time_window")
                ) \
                .agg(
                    sum("quantity").alias("daily_demand"),
                    sum("total_amount").alias("daily_revenue"),
                    count("sale_id").alias("transaction_count"),
                    avg("unit_price").alias("avg_unit_price")
                ) \
                .withColumn("date", col("time_window.start")) \
                .withColumn("day_of_week", dayofweek("date")) \
                .withColumn("month", month("date")) \
                .withColumn("is_weekend", 
                           when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1)
                           .otherwise(0)) \
                .drop("time_window")
            
            # Add lag features for time series
            window_spec = Window.partitionBy("product_id", "store_id") \
                              .orderBy("date")
            
            demand_data_with_lags = demand_data \
                .withColumn("demand_lag_1", lag("daily_demand", 1).over(window_spec)) \
                .withColumn("demand_lag_7", lag("daily_demand", 7).over(window_spec)) \
                .withColumn("demand_lag_30", lag("daily_demand", 30).over(window_spec)) \
                .withColumn("rolling_avg_7", 
                           avg("daily_demand").over(window_spec.rowsBetween(-7, -1))) \
                .withColumn("rolling_avg_30", 
                           avg("daily_demand").over(window_spec.rowsBetween(-30, -1))) \
                .filter(col("demand_lag_30").isNotNull())  # Ensure we have enough history
            
            logger.info("Demand forecasting data prepared successfully")
            return demand_data_with_lags
            
        except Exception as e:
            logger.error(f"Failed to prepare demand forecasting data: {e}")
            raise
    
    def train_demand_forecasting_model(self, training_data):
        """Train demand forecasting model using Random Forest"""
        try:
            # Define feature columns
            feature_cols = [
                "category_id", "brand", "store_region", "day_of_week", 
                "month", "is_weekend", "avg_unit_price",
                "demand_lag_1", "demand_lag_7", "demand_lag_30",
                "rolling_avg_7", "rolling_avg_30"
            ]
            
            # Convert categorical variables
            categorical_cols = ["category_id", "brand", "store_region"]
            indexers = [StringIndexer(inputCol=col, outputCol=col+"_index") 
                       for col in categorical_cols]
            encoder = OneHotEncoder(inputCols=[col+"_index" for col in categorical_cols],
                                  outputCols=[col+"_encoded" for col in categorical_cols])
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=[col+"_encoded" for col in categorical_cols] + 
                         [col for col in feature_cols if col not in categorical_cols],
                outputCol="features"
            )
            
            # Define model
            rf = RandomForestRegressor(
                featuresCol="features",
                labelCol="daily_demand",
                numTrees=100,
                maxDepth=10,
                seed=42
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=indexers + [encoder, assembler, rf])
            
            # Split data
            train_data, test_data = training_data.randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_data)
            
            # Make predictions
            predictions = model.transform(test_data)
            
            # Evaluate model
            evaluator = RegressionEvaluator(
                labelCol="daily_demand",
                predictionCol="prediction",
                metricName="rmse"
            )
            
            rmse = evaluator.evaluate(predictions)
            logger.info(f"Demand forecasting model RMSE: {rmse}")
            
            self.models["demand_forecasting"] = model
            return model, predictions
            
        except Exception as e:
            logger.error(f"Failed to train demand forecasting model: {e}")
            raise
    
    def prepare_stock_optimization_data(self, inventory_df, sales_df):
        """Prepare data for stock optimization model"""
        try:
            # Calculate stock-out events and optimal stock levels
            stock_data = inventory_df \
                .join(sales_df, ["store_id", "product_id"], "left") \
                .groupBy("store_id", "product_id") \
                .agg(
                    avg("current_stock").alias("avg_stock_level"),
                    stddev("current_stock").alias("stock_volatility"),
                    sum(when(col("current_stock") <= 0, 1).otherwise(0)).alias("stock_out_events"),
                    sum("quantity").alias("total_sales"),
                    count("sale_id").alias("sales_count"),
                    avg("unit_price").alias("avg_price")
                ) \
                .withColumn("stock_out_rate", 
                           col("stock_out_events") / col("sales_count")) \
                .withColumn("sales_per_stock", 
                           when(col("avg_stock_level") > 0, 
                               col("total_sales") / col("avg_stock_level"))
                           .otherwise(0)) \
                .filter(col("sales_count") > 0)  # Only products with sales
            
            logger.info("Stock optimization data prepared successfully")
            return stock_data
            
        except Exception as e:
            logger.error(f"Failed to prepare stock optimization data: {e}")
            raise
    
    def train_stock_optimization_model(self, stock_data):
        """Train stock optimization model"""
        try:
            # Define feature columns for stock optimization
            feature_cols = [
                "avg_stock_level", "stock_volatility", "total_sales", 
                "sales_count", "avg_price", "sales_per_stock"
            ]
            
            # Target: optimal stock level (simplified as 2x average sales per period)
            stock_data_with_target = stock_data \
                .withColumn("optimal_stock", 
                           col("total_sales") / 30 * 2)  # 2 days of average sales
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=feature_cols,
                outputCol="features"
            )
            
            # Define model
            gbt = GBTRegressor(
                featuresCol="features",
                labelCol="optimal_stock",
                maxIter=100,
                maxDepth=6,
                seed=42
            )
            
            # Create pipeline
            pipeline = Pipeline(stages=[assembler, gbt])
            
            # Split data
            train_data, test_data = stock_data_with_target.randomSplit([0.8, 0.2], seed=42)
            
            # Train model
            model = pipeline.fit(train_data)
            
            # Make predictions
            predictions = model.transform(test_data)
            
            # Evaluate model
            evaluator = RegressionEvaluator(
                labelCol="optimal_stock",
                predictionCol="prediction",
                metricName="rmse"
            )
            
            rmse = evaluator.evaluate(predictions)
            logger.info(f"Stock optimization model RMSE: {rmse}")
            
            self.models["stock_optimization"] = model
            return model, predictions
            
        except Exception as e:
            logger.error(f"Failed to train stock optimization model: {e}")
            raise
    
    def save_models(self):
        """Save trained models to MinIO distributed storage"""
        try:
            from minio import Minio
            from minio.error import S3Error
            import tempfile
            import shutil
            
            # Initialize MinIO client
            minio_client = Minio(
                "minio:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                secure=False
            )
            
            # Ensure models bucket exists
            bucket_name = "retail-models"
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")
            
            # Save each model to MinIO
            for model_name, model in self.models.items():
                # Create temporary directory for model files
                with tempfile.TemporaryDirectory() as temp_dir:
                    model_path = f"{temp_dir}/{model_name}"
                    
                    # Save model to temporary directory
                    model.write().overwrite().save(model_path)
                    
                    # Upload model files to MinIO
                    for root, dirs, files in os.walk(model_path):
                        for file in files:
                            local_file_path = os.path.join(root, file)
                            object_name = f"{model_name}/{file}"
                            
                            minio_client.fput_object(
                                bucket_name,
                                object_name,
                                local_file_path
                            )
                    
                    logger.info(f"Model {model_name} saved to MinIO bucket: {bucket_name}")
                
        except Exception as e:
            logger.error(f"Failed to save models to MinIO: {e}")
            raise
    
    def generate_predictions(self, future_date):
        """Generate predictions for future demand"""
        try:
            # This would use the trained models to generate future predictions
            # For demo purposes, we'll just log the process
            logger.info(f"Generating predictions for date: {future_date}")
            
            # In a real implementation, this would:
            # 1. Load the latest data
            # 2. Use the trained models to predict future demand
            # 3. Calculate optimal stock levels
            # 4. Save predictions to database
            
            predictions_summary = {
                "prediction_date": str(future_date),
                "models_used": list(self.models.keys()),
                "status": "completed"
            }
            
            logger.info(f"Predictions generated: {predictions_summary}")
            return predictions_summary
            
        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
            raise
    
    def run_training_pipeline(self):
        """Main method to run the complete ML training pipeline"""
        if not self.initialize_spark_session():
            return
        
        try:
            logger.info("Starting ML training pipeline...")
            
            # Load training data
            sales_df, inventory_df, products_df, stores_df = self.load_training_data()
            
            # Train demand forecasting model
            demand_data = self.prepare_demand_forecasting_data(sales_df, products_df, stores_df)
            demand_model, demand_predictions = self.train_demand_forecasting_model(demand_data)
            
            # Train stock optimization model
            stock_data = self.prepare_stock_optimization_data(inventory_df, sales_df)
            stock_model, stock_predictions = self.train_stock_optimization_model(stock_data)
            
            # Save models
            self.save_models()
            
            # Generate sample predictions
            future_date = datetime.now() + timedelta(days=7)
            predictions = self.generate_predictions(future_date)
            
            logger.info("ML training pipeline completed successfully")
            
            return {
                "demand_model_rmse": demand_predictions.agg(
                    sqrt(avg(pow(col("daily_demand") - col("prediction"), 2)))
                ).collect()[0][0],
                "stock_model_rmse": stock_predictions.agg(
                    sqrt(avg(pow(col("optimal_stock") - col("prediction"), 2)))
                ).collect()[0][0],
                "predictions": predictions
            }
            
        except Exception as e:
            logger.error(f"Error in ML training pipeline: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def main():
    """Main entry point"""
    processor = MLTrainingProcessor()
    results = processor.run_training_pipeline()
    
    if results:
        logger.info(f"Training completed with results: {results}")

if __name__ == "__main__":
    main()