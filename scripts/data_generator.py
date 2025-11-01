#!/usr/bin/env python3
"""
Real-time Data Generator for Retail Inventory Management
Generates streaming events for sales, inventory updates, and customer activities
"""

import argparse
import json
import time
import uuid
import random
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from producers.sales_producer import SalesProducer
from producers.inventory_producer import InventoryProducer
from config.settings import DATA_GENERATION_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RetailDataGenerator:
    def __init__(self):
        self.sales_producer = SalesProducer()
        self.inventory_producer = InventoryProducer()
        
        # Load sample data
        self.stores = self._load_sample_data("stores.json")
        self.products = self._load_sample_data("products.json")
        self.categories = self._load_sample_data("categories.json")
        self.brands = self._load_sample_data("brands.json")
        
        # Configuration
        self.config = DATA_GENERATION_CONFIG
        
        # Track inventory levels
        self.inventory_levels = self._initialize_inventory()
        
        # Sales patterns
        self.peak_hours = self.config["sales"]["peak_hours"]
        self.weekend_multiplier = self.config["sales"]["weekend_multiplier"]
        
        logger.info("Retail Data Generator initialized")
    
    def _load_sample_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load sample data from JSON file"""
        try:
            with open(f"data/{filename}", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Sample data file {filename} not found. Run create_sample_data.py first.")
            return []
    
    def _initialize_inventory(self) -> Dict[str, Dict[str, int]]:
        """Initialize inventory levels for all products in all stores"""
        inventory = {}
        
        for store in self.stores:
            store_id = store["store_id"]
            inventory[store_id] = {}
            
            for product in self.products:
                product_id = product["sku"]
                # Random initial stock between 20 and 200 units
                inventory[store_id][product_id] = random.randint(20, 200)
        
        return inventory
    
    def _get_current_hour_multiplier(self) -> float:
        """Get sales multiplier based on current hour"""
        current_hour = datetime.now().hour
        
        if current_hour in self.peak_hours:
            return 2.0  # Double sales during peak hours
        elif current_hour >= 22 or current_hour <= 6:
            return 0.3  # Reduced sales during night
        else:
            return 1.0  # Normal sales
    
    def _get_day_multiplier(self) -> float:
        """Get sales multiplier based on day of week"""
        current_day = datetime.now().weekday()
        
        if current_day >= 5:  # Saturday (5) or Sunday (6)
            return self.weekend_multiplier
        else:
            return 1.0
    
    def generate_sales_transaction(self) -> Dict[str, Any]:
        """Generate a single sales transaction"""
        store = random.choice(self.stores)
        product = random.choice(self.products)
        
        # Calculate quantity (usually 1-3 items, occasionally more)
        quantity = random.choices(
            [1, 2, 3, 4, 5, 10],
            weights=[0.4, 0.3, 0.15, 0.08, 0.05, 0.02]
        )[0]
        
        unit_price = product["unit_price"]
        total_amount = round(quantity * unit_price, 2)
        
        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "store_id": store["store_id"],
            "product_id": product["sku"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "timestamp": datetime.now().isoformat(),
            "customer_id": f"CUST{random.randint(1000, 9999)}",
            "payment_method": random.choice(["credit_card", "debit_card", "cash", "mobile_payment"]),
            "store_region": store["region"],
            "product_category": next(
                (cat["category_name"] for cat in self.categories 
                 if cat["category_key"] == product["category_key"]), "Unknown"
            )
        }
        
        return transaction
    
    def generate_inventory_update(self, store_id: str, product_id: str, 
                                quantity_change: int, reason: str) -> Dict[str, Any]:
        """Generate an inventory update event"""
        current_level = self.inventory_levels[store_id][product_id]
        new_level = max(0, current_level + quantity_change)
        
        # Update internal tracking
        self.inventory_levels[store_id][product_id] = new_level
        
        update = {
            "inventory_id": str(uuid.uuid4()),
            "store_id": store_id,
            "product_id": product_id,
            "quantity_change": quantity_change,
            "new_quantity": new_level,
            "previous_quantity": current_level,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        return update
    
    def generate_restock_event(self) -> Dict[str, Any]:
        """Generate a restock event for low inventory items"""
        # Find products that need restocking
        low_stock_items = []
        
        for store_id, products in self.inventory_levels.items():
            for product_id, quantity in products.items():
                if quantity <= 10:  # Low stock threshold
                    low_stock_items.append((store_id, product_id, quantity))
        
        if not low_stock_items:
            return None
        
        store_id, product_id, current_quantity = random.choice(low_stock_items)
        restock_quantity = random.randint(50, 200)  # Restock amount
        
        restock_event = {
            "restock_id": str(uuid.uuid4()),
            "store_id": store_id,
            "product_id": product_id,
            "restock_quantity": restock_quantity,
            "current_quantity": current_quantity,
            "expected_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
            "supplier": "Auto-Restock System",
            "timestamp": datetime.now().isoformat()
        }
        
        return restock_event
    
    def generate_price_change(self) -> Dict[str, Any]:
        """Generate a price change event"""
        product = random.choice(self.products)
        current_price = product["unit_price"]
        
        # Small price changes more common than large ones
        change_type = random.choices(["increase", "decrease", "no_change"], 
                                   weights=[0.3, 0.4, 0.3])[0]
        
        if change_type == "no_change":
            return None
        
        if change_type == "increase":
            change_pct = random.uniform(0.01, 0.15)  # 1-15% increase
        else:
            change_pct = -random.uniform(0.01, 0.25)  # 1-25% decrease (sales/promotions)
        
        new_price = round(current_price * (1 + change_pct), 2)
        
        price_change = {
            "price_change_id": str(uuid.uuid4()),
            "product_id": product["sku"],
            "old_price": current_price,
            "new_price": new_price,
            "change_pct": round(change_pct * 100, 2),
            "reason": random.choice(["promotion", "cost_change", "seasonal", "clearance"]),
            "effective_date": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update product price for future transactions
        product["unit_price"] = new_price
        
        return price_change
    
    def generate_customer_event(self) -> Dict[str, Any]:
        """Generate customer behavior event (foot traffic, browsing)"""
        store = random.choice(self.stores)
        
        event_types = ["store_entrance", "browsing", "product_view", "cart_addition", "cart_removal"]
        
        event = {
            "event_id": str(uuid.uuid4()),
            "store_id": store["store_id"],
            "customer_id": f"CUST{random.randint(1000, 9999)}",
            "event_type": random.choice(event_types),
            "product_id": random.choice(self.products)["sku"] if random.random() > 0.3 else None,
            "session_duration": random.randint(30, 600),  # 30 seconds to 10 minutes
            "timestamp": datetime.now().isoformat()
        }
        
        return event
    
    def run_simulation(self, duration_minutes: int = 60, events_per_minute: int = 10):
        """Run the data generation simulation"""
        logger.info(f"Starting simulation for {duration_minutes} minutes at {events_per_minute} events/minute")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        events_generated = 0
        
        try:
            while datetime.now() < end_time:
                # Calculate events for this second based on time patterns
                hour_multiplier = self._get_current_hour_multiplier()
                day_multiplier = self._get_day_multiplier()
                events_this_second = max(1, int((events_per_minute / 60) * hour_multiplier * day_multiplier))
                
                for _ in range(events_this_second):
                    # Distribute event types
                    event_type = random.choices(
                        ["sales", "inventory", "price_change", "customer", "restock"],
                        weights=[0.5, 0.2, 0.1, 0.15, 0.05]
                    )[0]
                    
                    if event_type == "sales" and self.stores and self.products:
                        transaction = self.generate_sales_transaction()
                        self.sales_producer.send_transaction(transaction)
                        
                        # Generate corresponding inventory update
                        inventory_update = self.generate_inventory_update(
                            transaction["store_id"],
                            transaction["product_id"],
                            -transaction["quantity"],  # Negative for sales
                            "sale"
                        )
                        self.inventory_producer.send_update(inventory_update)
                        
                    elif event_type == "inventory" and self.stores and self.products:
                        store = random.choice(self.stores)
                        product = random.choice(self.products)
                        reason = random.choice(["receipt", "adjustment", "damage", "theft"])
                        quantity_change = random.randint(-5, 10)  # Small adjustments
                        
                        inventory_update = self.generate_inventory_update(
                            store["store_id"],
                            product["sku"],
                            quantity_change,
                            reason
                        )
                        self.inventory_producer.send_update(inventory_update)
                        
                    elif event_type == "price_change" and self.products:
                        price_change = self.generate_price_change()
                        if price_change:
                            # Send to appropriate topic
                            pass  # Price change producer would go here
                        
                    elif event_type == "customer" and self.stores:
                        customer_event = self.generate_customer_event()
                        # Send to customer events topic
                        pass  # Customer events producer would go here
                        
                    elif event_type == "restock" and self.stores and self.products:
                        restock_event = self.generate_restock_event()
                        if restock_event:
                            # Send to restock alerts topic
                            pass  # Restock producer would go here
                    
                    events_generated += 1
                
                # Wait for next second
                time.sleep(1)
                
                # Print progress every 30 seconds
                if int(time.time()) % 30 == 0:
                    remaining = (end_time - datetime.now()).total_seconds() / 60
                    logger.info(f"Progress: {events_generated} events generated, {remaining:.1f} minutes remaining")
        
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        
        finally:
            logger.info(f"Simulation completed. Total events generated: {events_generated}")
            self.sales_producer.close()
            self.inventory_producer.close()

def main():
    parser = argparse.ArgumentParser(description="Retail Data Generator")
    parser.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    parser.add_argument("--rate", type=int, default=10, help="Events per minute")
    parser.add_argument("--stores", type=int, help="Override store count")
    parser.add_argument("--products", type=int, help="Override product count")
    
    args = parser.parse_args()
    
    # Check if sample data exists
    if not os.path.exists("data/stores.json") or not os.path.exists("data/products.json"):
        logger.error("Sample data not found. Please run create_sample_data.py first.")
        return
    
    generator = RetailDataGenerator()
    generator.run_simulation(
        duration_minutes=args.duration,
        events_per_minute=args.rate
    )

if __name__ == "__main__":
    main()