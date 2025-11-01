"""
Inventory Update Producer
Handles production of inventory update events to Kafka
"""

import logging
from typing import Dict, Any, Optional

from .base_producer import BaseProducer
from config.settings import KAFKA_TOPICS

logger = logging.getLogger(__name__)


class InventoryProducer(BaseProducer):
    """Producer for inventory update events"""
    
    def __init__(self):
        """Initialize inventory producer"""
        super().__init__(topic=KAFKA_TOPICS["inventory_updates"])
        logger.info("Inventory producer initialized")
    
    def send_update(self, inventory_data: Dict[str, Any]) -> bool:
        """
        Send an inventory update event
        
        Args:
            inventory_data: Dictionary containing inventory update data
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        # Validate required fields
        required_fields = [
            "inventory_id", "store_id", "product_id", 
            "quantity_change", "new_quantity", "reason", "timestamp"
        ]
        
        for field in required_fields:
            if field not in inventory_data:
                logger.error(f"Missing required field in inventory update: {field}")
                return False
        
        # Add metadata
        inventory_data["event_type"] = "inventory_update"
        inventory_data["event_version"] = "1.0"
        
        # Use store_id + product_id as key for consistent partitioning
        key = f"{inventory_data['store_id']}_{inventory_data['product_id']}"
        
        success = self.send_message(inventory_data, key)
        
        if success:
            logger.info(f"Inventory update sent: {inventory_data['inventory_id']} "
                       f"({inventory_data['store_id']}/{inventory_data['product_id']})")
        else:
            logger.error(f"Failed to send inventory update: {inventory_data['inventory_id']}")
        
        return success
    
    def send_stock_movement(self, store_id: str, product_id: str, 
                          movement_type: str, quantity: int, 
                          reason: str = "manual") -> bool:
        """
        Send a stock movement event (convenience method)
        
        Args:
            store_id: Store identifier
            product_id: Product identifier
            movement_type: Type of movement ('in', 'out', 'adjustment')
            quantity: Quantity moved (positive for in, negative for out)
            reason: Reason for movement
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        import uuid
        from datetime import datetime
        
        movement_data = {
            "inventory_id": str(uuid.uuid4()),
            "store_id": store_id,
            "product_id": product_id,
            "movement_type": movement_type,
            "quantity": quantity,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_update(movement_data)
    
    def send_restock_alert(self, store_id: str, product_id: str, 
                          current_quantity: int, reorder_point: int,
                          supplier: str = "default") -> bool:
        """
        Send a restock alert event
        
        Args:
            store_id: Store identifier
            product_id: Product identifier
            current_quantity: Current stock level
            reorder_point: Reorder point threshold
            supplier: Supplier information
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        import uuid
        from datetime import datetime
        
        alert_data = {
            "alert_id": str(uuid.uuid4()),
            "store_id": store_id,
            "product_id": product_id,
            "current_quantity": current_quantity,
            "reorder_point": reorder_point,
            "supplier": supplier,
            "alert_type": "low_stock",
            "severity": "high" if current_quantity <= 5 else "medium",
            "timestamp": datetime.now().isoformat(),
            "event_type": "restock_alert",
            "event_version": "1.0"
        }
        
        # Use store_id as key for consistent partitioning of alerts
        key = store_id
        
        return self.send_message(alert_data, key)
    
    def send_batch_updates(self, updates: list) -> bool:
        """
        Send multiple inventory updates in batch
        
        Args:
            updates: List of inventory update dictionaries
            
        Returns:
            bool: True if all messages were sent successfully, False otherwise
        """
        if not updates:
            logger.warning("No inventory updates to send")
            return True
        
        # Validate all updates
        valid_updates = []
        for update in updates:
            required_fields = [
                "inventory_id", "store_id", "product_id", 
                "quantity_change", "new_quantity", "reason", "timestamp"
            ]
            
            if all(field in update for field in required_fields):
                update["event_type"] = "inventory_update"
                update["event_version"] = "1.0"
                valid_updates.append(update)
            else:
                logger.warning(f"Skipping invalid inventory update: {update.get('inventory_id', 'unknown')}")
        
        if not valid_updates:
            logger.error("No valid inventory updates to send")
            return False
        
        # Send batch
        success = self.send_batch(valid_updates)
        
        if success:
            logger.info(f"Batch of {len(valid_updates)} inventory updates sent successfully")
        else:
            logger.error(f"Failed to send batch of {len(valid_updates)} inventory updates")
        
        return success
    
    def validate_inventory_schema(self, inventory_data: Dict[str, Any]) -> bool:
        """
        Validate inventory data against expected schema
        
        Args:
            inventory_data: Dictionary containing inventory data
            
        Returns:
            bool: True if schema is valid, False otherwise
        """
        schema_checks = [
            ("inventory_id", str),
            ("store_id", str),
            ("product_id", str),
            ("quantity_change", int),
            ("new_quantity", int),
            ("reason", str),
            ("timestamp", str)
        ]
        
        for field, expected_type in schema_checks:
            if field not in inventory_data:
                logger.error(f"Missing field: {field}")
                return False
            
            value = inventory_data[field]
            if not isinstance(value, expected_type):
                logger.error(f"Invalid type for {field}: expected {expected_type}, got {type(value)}")
                return False
        
        # Additional validation
        if inventory_data["new_quantity"] < 0:
            logger.error(f"Invalid new quantity: {inventory_data['new_quantity']}")
            return False
        
        valid_reasons = ["sale", "receipt", "adjustment", "damage", "theft", "return"]
        if inventory_data["reason"] not in valid_reasons:
            logger.warning(f"Unusual reason: {inventory_data['reason']}")
        
        return True