#!/usr/bin/env python3
"""
MinIO Client Utility for Retail Inventory Management

This module provides a unified interface for MinIO operations
across all Spark jobs and applications.
"""

import logging
from minio import Minio
from minio.error import S3Error
import tempfile
import os
import io

logger = logging.getLogger(__name__)

class MinIOClient:
    """MinIO client wrapper for distributed storage operations"""
    
    def __init__(self, endpoint="minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False):
        """Initialize MinIO client with connection parameters"""
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.buckets = {
            "raw_data": "retail-raw-data",
            "processed_data": "retail-processed-data",
            "models": "retail-models",
            "features": "retail-features"
        }
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Ensure all required buckets exist"""
        for bucket_name in self.buckets.values():
            if not self.client.bucket_exists(bucket_name):
                try:
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created MinIO bucket: {bucket_name}")
                except S3Error as e:
                    logger.error(f"Failed to create bucket {bucket_name}: {e}")
                    raise
    
    def save_model(self, model, model_name, model_type="ml_model"):
        """Save ML model to MinIO models bucket"""
        try:
            bucket_name = self.buckets["models"]
            
            # Create temporary directory for model files
            with tempfile.TemporaryDirectory() as temp_dir:
                model_path = f"{temp_dir}/{model_name}"
                
                # Save model to temporary directory
                model.write().overwrite().save(model_path)
                
                # Upload model files to MinIO
                for root, dirs, files in os.walk(model_path):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        object_name = f"{model_type}/{model_name}/{file}"
                        
                        self.client.fput_object(
                            bucket_name,
                            object_name,
                            local_file_path
                        )
                
                logger.info(f"Model {model_name} saved to MinIO bucket: {bucket_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save model {model_name} to MinIO: {e}")
            return False
    
    def save_dataframe(self, dataframe, dataset_name, data_type="processed"):
        """Save Spark DataFrame to MinIO as Parquet files"""
        try:
            bucket_name = self.buckets["processed_data"]
            
            # Create temporary directory for Parquet files
            with tempfile.TemporaryDirectory() as temp_dir:
                local_path = f"{temp_dir}/{dataset_name}"
                
                # Write DataFrame to temporary Parquet files
                dataframe.write.mode("overwrite").parquet(local_path)
                
                # Upload Parquet files to MinIO
                for root, dirs, files in os.walk(local_path):
                    for file in files:
                        local_file_path = os.path.join(root, file)
                        object_name = f"{data_type}/{dataset_name}/{file}"
                        
                        self.client.fput_object(
                            bucket_name,
                            object_name,
                            local_file_path
                        )
                
                logger.info(f"Dataset {dataset_name} saved to MinIO bucket: {bucket_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save dataset {dataset_name} to MinIO: {e}")
            return False
    
    def save_json_data(self, json_data, object_name, data_type="reports"):
        """Save JSON data to MinIO"""
        try:
            bucket_name = self.buckets["processed_data"]
            
            # Convert JSON to bytes
            json_bytes = json_data.encode('utf-8') if isinstance(json_data, str) else json_data
            
            self.client.put_object(
                bucket_name,
                f"{data_type}/{object_name}",
                data=io.BytesIO(json_bytes),
                length=len(json_bytes)
            )
            
            logger.info(f"JSON data saved to MinIO: {data_type}/{object_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON data to MinIO: {e}")
            return False
    
    def list_objects(self, bucket_type, prefix=""):
        """List objects in a MinIO bucket"""
        try:
            bucket_name = self.buckets[bucket_type]
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"Failed to list objects in bucket {bucket_name}: {e}")
            return []
    
    def object_exists(self, bucket_type, object_name):
        """Check if an object exists in MinIO"""
        try:
            bucket_name = self.buckets[bucket_type]
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"Error checking object existence: {e}")
            return False
    
    def download_object(self, bucket_type, object_name, local_path):
        """Download object from MinIO to local path"""
        try:
            bucket_name = self.buckets[bucket_type]
            self.client.fget_object(bucket_name, object_name, local_path)
            logger.info(f"Downloaded {object_name} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download object {object_name}: {e}")
            return False

# Global MinIO client instance
minio_client = MinIOClient()

def get_minio_client():
    """Get the global MinIO client instance"""
    return minio_client