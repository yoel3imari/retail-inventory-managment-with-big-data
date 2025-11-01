"""
Sales Transaction Producer
Handles production of sales transaction events to Kafka
"""

import logging
from typing import Dict, Any, Optional

from .base_producer import BaseProducer
from config.settings import KAFKA_TOPICS

logger = logging.getLogger(__name__)


class SalesProducer(BaseProducer):
    """Producer for sales transaction events"""
    
    def __init__(self):
        """Initialize sales producer"""
        super().__init__(topic=KAFKA_TOPICS["sales_transactions"])
        logger.info("Sales producer initialized")
    
    def send_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Send a sales transaction event
        
        Args:
            transaction_data: Dictionary containing transaction data
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        # Validate required fields
        required_fields = [
            "transaction_id", "store_id", "product_id", 
            "quantity", "unit_price", "total_amount", "timestamp"
        ]
        
        for field in required_fields:
            if field not in transaction_data:
                logger.error(f"Missing required field in transaction: {field}")
                return False
        
        # Add metadata
        transaction_data["event_type"] = "sales_transaction"
        transaction_data["event_version"] = "1.0"
        
        # Use transaction_id as key for consistent partitioning
        key = transaction_data["transaction_id"]
        
        success = self.send_message(transaction_data, key)
        
        if success:
            logger.info(f"Sales transaction sent: {transaction_data['transaction_id']}")
        else:
            logger.error(f"Failed to send sales transaction: {transaction_data['transaction_id']}")
        
        return success
    
    def send_batch_transactions(self, transactions: list) -> bool:
        """
        Send multiple sales transactions in batch
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            bool: True if all messages were sent successfully, False otherwise
        """
        if not transactions:
            logger.warning("No transactions to send")
            return True
        
        # Validate all transactions
        valid_transactions = []
        for transaction in transactions:
            required_fields = [
                "transaction_id", "store_id", "product_id", 
                "quantity", "unit_price", "total_amount", "timestamp"
            ]
            
            if all(field in transaction for field in required_fields):
                transaction["event_type"] = "sales_transaction"
                transaction["event_version"] = "1.0"
                valid_transactions.append(transaction)
            else:
                logger.warning(f"Skipping invalid transaction: {transaction.get('transaction_id', 'unknown')}")
        
        if not valid_transactions:
            logger.error("No valid transactions to send")
            return False
        
        # Send batch
        success = self.send_batch(valid_transactions)
        
        if success:
            logger.info(f"Batch of {len(valid_transactions)} sales transactions sent successfully")
        else:
            logger.error(f"Failed to send batch of {len(valid_transactions)} sales transactions")
        
        return success
    
    def validate_transaction_schema(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Validate transaction data against expected schema
        
        Args:
            transaction_data: Dictionary containing transaction data
            
        Returns:
            bool: True if schema is valid, False otherwise
        """
        schema_checks = [
            ("transaction_id", str),
            ("store_id", str),
            ("product_id", str),
            ("quantity", int),
            ("unit_price", (int, float)),
            ("total_amount", (int, float)),
            ("timestamp", str),
            ("customer_id", str),
            ("payment_method", str)
        ]
        
        for field, expected_type in schema_checks:
            if field not in transaction_data:
                logger.error(f"Missing field: {field}")
                return False
            
            value = transaction_data[field]
            if not isinstance(value, expected_type):
                logger.error(f"Invalid type for {field}: expected {expected_type}, got {type(value)}")
                return False
        
        # Additional validation
        if transaction_data["quantity"] <= 0:
            logger.error(f"Invalid quantity: {transaction_data['quantity']}")
            return False
        
        if transaction_data["unit_price"] <= 0:
            logger.error(f"Invalid unit price: {transaction_data['unit_price']}")
            return False
        
        expected_total = transaction_data["quantity"] * transaction_data["unit_price"]
        if abs(transaction_data["total_amount"] - expected_total) > 0.01:  # Allow for floating point errors
            logger.error(f"Total amount mismatch: expected {expected_total}, got {transaction_data['total_amount']}")
            return False
        
        return True