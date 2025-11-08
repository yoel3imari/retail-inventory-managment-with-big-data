"""
Base Kafka Producer Class
Provides common functionality for all Kafka producers
"""

import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from config.settings import KAFKA_CONFIG

logger = logging.getLogger(__name__)


class BaseProducer:
    """Base class for all Kafka producers"""
    
    def __init__(self, topic: str, **kwargs):
        """
        Initialize Kafka producer
        
        Args:
            topic: Kafka topic to produce to
            **kwargs: Additional Kafka producer configuration
        """
        self.topic = topic
        
        # Merge default config with any overrides
        producer_config = KAFKA_CONFIG.copy()
        producer_config.update(kwargs)
        
        # Remove bootstrap_servers from config if present in kwargs
        if 'bootstrap_servers' in kwargs:
            producer_config.pop('bootstrap_servers', None)
        
        try:
            self.producer = KafkaProducer(
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **producer_config
            )
            logger.info(f"Kafka producer initialized for topic: {topic}")
        except KafkaError as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def send_message(self, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        Send a message to Kafka topic
        
        Args:
            message: Dictionary containing the message data
            key: Optional key for partitioning
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            future = self.producer.send(
                topic=self.topic,
                value=message,
                key=key.encode('utf-8') if key else None
            )
            
            # Wait for the send to complete
            future.get(timeout=10)
            logger.debug(f"Message sent successfully to topic {self.topic}: {message}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            return False
    
    def send_batch(self, messages: list, key: Optional[str] = None) -> bool:
        """
        Send a batch of messages to Kafka topic
        
        Args:
            messages: List of dictionaries containing message data
            key: Optional key for partitioning
            
        Returns:
            bool: True if all messages were sent successfully, False otherwise
        """
        success_count = 0
        
        for message in messages:
            if self.send_message(message, key):
                success_count += 1
        
        total_count = len(messages)
        success_rate = success_count / total_count if total_count > 0 else 0
        
        if success_rate == 1.0:
            logger.info(f"All {total_count} messages sent successfully to topic {self.topic}")
            return True
        else:
            logger.warning(f"Sent {success_count}/{total_count} messages to topic {self.topic}")
            return success_count > 0
    
    def flush(self):
        """Flush any pending messages"""
        try:
            self.producer.flush()
            logger.debug("Producer flushed successfully")
        except KafkaError as e:
            logger.error(f"Failed to flush producer: {e}")
    
    def close(self):
        """Close the producer connection"""
        try:
            self.producer.close()
            logger.info("Kafka producer closed successfully")
        except KafkaError as e:
            logger.error(f"Error closing Kafka producer: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get producer metrics
        
        Returns:
            Dict containing producer metrics
        """
        try:
            metrics = self.producer.metrics()
            return metrics
        except Exception as e:
            logger.error(f"Failed to get producer metrics: {e}")
            return {}


class RetryProducer(BaseProducer):
    """Producer with retry logic for failed sends"""
    
    def __init__(self, topic: str, max_retries: int = 3, **kwargs):
        """
        Initialize retry producer
        
        Args:
            topic: Kafka topic to produce to
            max_retries: Maximum number of retry attempts
            **kwargs: Additional Kafka producer configuration
        """
        super().__init__(topic, **kwargs)
        self.max_retries = max_retries
    
    def send_message_with_retry(self, message: Dict[str, Any], 
                              key: Optional[str] = None) -> bool:
        """
        Send message with retry logic
        
        Args:
            message: Dictionary containing the message data
            key: Optional key for partitioning
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                if self.send_message(message, key):
                    return True
                
                # If send failed, wait before retry
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Send failed, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    import time
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error during send (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return False
        
        logger.error(f"Failed to send message after {self.max_retries} attempts")
        return False