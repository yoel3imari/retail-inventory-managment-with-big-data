#!/usr/bin/env python3
"""
Test script for MinIO integration in Retail Inventory Management

This script tests the MinIO distributed storage integration
to ensure models and data are properly saved to MinIO buckets.
"""

import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minio_connection():
    """Test basic MinIO connection and bucket operations"""
    try:
        import sys
        import os
        # Add the project root to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from src.utils.minio_client import get_minio_client
        
        # Get MinIO client
        minio_client = get_minio_client()
        
        # Test bucket listing
        buckets = minio_client.buckets
        logger.info(f"Available buckets: {buckets}")
        
        # Test object listing
        for bucket_type in buckets:
            objects = minio_client.list_objects(bucket_type)
            logger.info(f"Objects in {bucket_type}: {len(objects)} objects")
        
        logger.info("✅ MinIO connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ MinIO connection test failed: {e}")
        return False

def test_json_save():
    """Test saving JSON data to MinIO"""
    try:
        import sys
        import os
        # Add the project root to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from src.utils.minio_client import get_minio_client
        
        minio_client = get_minio_client()
        
        # Create test data
        test_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_message": "This is a test of MinIO integration",
            "status": "success"
        }
        
        # Save JSON to MinIO
        json_string = json.dumps(test_data, indent=2)
        object_name = f"test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        success = minio_client.save_json_data(json_string, object_name, "test")
        
        if success:
            logger.info(f"✅ JSON save test passed - saved to: test/{object_name}")
            return True
        else:
            logger.error("❌ JSON save test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ JSON save test failed: {e}")
        return False

def test_bucket_operations():
    """Test bucket operations and object existence checks"""
    try:
        import sys
        import os
        # Add the project root to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from src.utils.minio_client import get_minio_client
        
        minio_client = get_minio_client()
        
        # Test object existence (should be False for non-existent object)
        exists = minio_client.object_exists("processed_data", "non_existent_object.txt")
        if not exists:
            logger.info("✅ Object existence check passed for non-existent object")
        else:
            logger.error("❌ Object existence check failed")
            return False
        
        logger.info("✅ Bucket operations test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bucket operations test failed: {e}")
        return False

def main():
    """Run all MinIO integration tests"""
    logger.info("Starting MinIO integration tests...")
    
    tests = [
        ("MinIO Connection", test_minio_connection),
        ("JSON Save", test_json_save),
        ("Bucket Operations", test_bucket_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("MINIO INTEGRATION TEST SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All MinIO integration tests passed!")
        return True
    else:
        logger.error("💥 Some MinIO integration tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)