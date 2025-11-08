#!/usr/bin/env python3
"""
Simple MinIO Test Script

This script tests basic MinIO connectivity without complex imports.
"""

import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minio_direct():
    """Test MinIO connection directly"""
    try:
        from minio import Minio
        
        # Initialize MinIO client directly
        minio_client = Minio(
            "minio:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        # Test bucket operations
        buckets_to_check = ["retail-raw-data", "retail-processed-data", "retail-models", "retail-features"]
        
        for bucket_name in buckets_to_check:
            if not minio_client.bucket_exists(bucket_name):
                logger.info(f"Creating bucket: {bucket_name}")
                minio_client.make_bucket(bucket_name)
            else:
                logger.info(f"Bucket exists: {bucket_name}")
        
        # Test saving a simple object
        test_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_message": "This is a direct MinIO test",
            "status": "success"
        }
        
        json_bytes = json.dumps(test_data).encode('utf-8')
        object_name = f"test/direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        minio_client.put_object(
            "retail-processed-data",
            object_name,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes)
        )
        
        logger.info(f"✅ Direct MinIO test passed - saved to: {object_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct MinIO test failed: {e}")
        return False

def main():
    """Run the simple MinIO test"""
    logger.info("Starting simple MinIO test...")
    
    try:
        import io  # Import io here to avoid issues
        success = test_minio_direct()
        
        if success:
            logger.info("🎉 Simple MinIO test passed!")
            return True
        else:
            logger.error("💥 Simple MinIO test failed!")
            return False
            
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)