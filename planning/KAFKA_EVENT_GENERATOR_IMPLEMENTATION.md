# Kafka Event Generator with Random Delta Times - Implementation Plan

## Overview
Create an enhanced Kafka event generator that produces events with random time intervals (10-60 seconds) between each event to mimic real-life retail scenarios.

## Current Architecture Analysis

### Existing Data Generator (`scripts/data_generator.py`)
- **Timing Pattern**: Fixed rate (events per minute with 1-second intervals)
- **Event Types**: Sales, Inventory, Price Changes, Customer Events, Restock Alerts
- **Kafka Topics**: 
  - `retail-sales-transactions`
  - `retail-inventory-updates` 
  - `retail-restock-alerts`
  - `retail-price-changes`
  - `retail-customer-events`

### Key Issues with Current Implementation
1. Events generated in batches per second
2. Fixed timing intervals don't reflect real-world patterns
3. No realistic time gaps between individual events

## Implementation Strategy

### 1. Enhanced Generator Design
```python
class RealisticEventGenerator(RetailDataGenerator):
    def __init__(self):
        super().__init__()
        self.min_delta = 10  # seconds
        self.max_delta = 60  # seconds
        
    def run_realistic_simulation(self, duration_minutes=None, continuous=False):
        """
        Generate events with random time intervals between each event
        """
        # Single event generation with random sleep
        while running_condition:
            event = self.generate_single_event()
            self.send_event_to_kafka(event)
            
            # Wait random time before next event
            sleep_time = random.uniform(self.min_delta, self.max_delta)
            time.sleep(sleep_time)
```

### 2. Core Modifications Required

#### A. Replace Batch Generation with Single Event Generation
**Current (lines 244-302):**
```python
while datetime.now() < end_time:
    events_this_second = calculate_events_per_second()
    for _ in range(events_this_second):
        generate_and_send_event()
    time.sleep(1)
```

**New Approach:**
```python
while datetime.now() < end_time:
    event = generate_single_event()
    send_event_to_kafka(event)
    sleep_time = random.uniform(10, 60)
    time.sleep(sleep_time)
```

#### B. Enhanced Event Generation Method
```python
def generate_single_event(self) -> Dict[str, Any]:
    """Generate a single event with realistic timing"""
    event_type = self._select_event_type()
    
    if event_type == "sales":
        return self.generate_sales_transaction()
    elif event_type == "inventory":
        return self.generate_inventory_adjustment()
    elif event_type == "price_change":
        return self.generate_price_change()
    elif event_type == "customer":
        return self.generate_customer_event()
    elif event_type == "restock":
        return self.generate_restock_event()
```

#### C. Event Type Distribution
- **Sales Transactions**: 50% (most common)
- **Inventory Updates**: 20% 
- **Customer Events**: 15%
- **Price Changes**: 10%
- **Restock Alerts**: 5%

### 3. Configuration Updates

#### Add to `config/settings.py`:
```python
REALISTIC_GENERATOR_CONFIG = {
    "timing": {
        "min_delta_seconds": 10,
        "max_delta_seconds": 60,
        "event_distribution": {
            "sales": 0.5,
            "inventory": 0.2,
            "customer": 0.15,
            "price_change": 0.1,
            "restock": 0.05
        }
    }
}
```

### 4. New Script Implementation

#### File: `scripts/kafka_event_generator.py`
```python
#!/usr/bin/env python3
"""
Realistic Kafka Event Generator
Generates retail events with random time intervals (10-60 seconds) between events
to mimic real-world scenarios.
"""

import argparse
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import existing components
from scripts.data_generator import RetailDataGenerator
from config.settings import REALISTIC_GENERATOR_CONFIG

class RealisticEventGenerator(RetailDataGenerator):
    """Enhanced generator with realistic timing between events"""
    
    def __init__(self):
        super().__init__()
        self.config = REALISTIC_GENERATOR_CONFIG
        self.min_delta = self.config["timing"]["min_delta_seconds"]
        self.max_delta = self.config["timing"]["max_delta_seconds"]
        self.event_weights = self.config["timing"]["event_distribution"]
        
    def _select_event_type(self) -> str:
        """Select event type based on configured distribution"""
        event_types = list(self.event_weights.keys())
        weights = list(self.event_weights.values())
        return random.choices(event_types, weights=weights)[0]
    
    def generate_single_event(self) -> Optional[Dict[str, Any]]:
        """Generate a single event of random type"""
        event_type = self._select_event_type()
        
        try:
            if event_type == "sales" and self.stores and self.products:
                transaction = self.generate_sales_transaction()
                self.sales_producer.send_transaction(transaction)
                
                # Generate corresponding inventory update
                inventory_update = self.generate_inventory_update(
                    transaction["store_id"],
                    transaction["product_id"],
                    -transaction["quantity"],
                    "sale"
                )
                self.inventory_producer.send_update(inventory_update)
                return transaction
                
            elif event_type == "inventory" and self.stores and self.products:
                store = random.choice(self.stores)
                product = random.choice(self.products)
                reason = random.choice(["receipt", "adjustment", "damage", "theft"])
                quantity_change = random.randint(-5, 10)
                
                inventory_update = self.generate_inventory_update(
                    store["store_id"],
                    product["sku"],
                    quantity_change,
                    reason
                )
                self.inventory_producer.send_update(inventory_update)
                return inventory_update
                
            elif event_type == "price_change" and self.products:
                price_change = self.generate_price_change()
                # TODO: Add price change producer
                return price_change
                
            elif event_type == "customer" and self.stores:
                customer_event = self.generate_customer_event()
                # TODO: Add customer events producer
                return customer_event
                
            elif event_type == "restock" and self.stores and self.products:
                restock_event = self.generate_restock_event()
                # TODO: Add restock producer
                return restock_event
                
        except Exception as e:
            logging.error(f"Error generating {event_type} event: {e}")
            return None
            
        return None
    
    def run_realistic_simulation(self, duration_minutes: Optional[int] = None, 
                               continuous: bool = False):
        """Run simulation with realistic timing between events"""
        if duration_minutes:
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            logging.info(f"Starting realistic simulation for {duration_minutes} minutes")
        else:
            end_time = None
            logging.info("Starting continuous realistic simulation")
        
        events_generated = 0
        
        try:
            while True:
                # Check if we should stop based on duration
                if end_time and datetime.now() >= end_time:
                    break
                    
                # Generate and send single event
                event = self.generate_single_event()
                if event:
                    events_generated += 1
                    event_type = event.get("event_type", "unknown")
                    logging.info(f"Event #{events_generated}: {event_type} generated")
                
                # Wait random time before next event
                sleep_time = random.uniform(self.min_delta, self.max_delta)
                logging.debug(f"Waiting {sleep_time:.2f} seconds before next event")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logging.info("Simulation interrupted by user")
            
        finally:
            logging.info(f"Realistic simulation completed. Total events: {events_generated}")
            self.sales_producer.close()
            self.inventory_producer.close()

def main():
    parser = argparse.ArgumentParser(description="Realistic Kafka Event Generator")
    parser.add_argument("--duration", type=int, help="Duration in minutes (optional for continuous)")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--min-delta", type=float, default=10, help="Minimum seconds between events")
    parser.add_argument("--max-delta", type=float, default=60, help="Maximum seconds between events")
    
    args = parser.parse_args()
    
    # Check sample data
    if not os.path.exists("data/stores.json"):
        logging.error("Sample data not found. Run create_sample_data.py first.")
        return
    
    generator = RealisticEventGenerator()
    
    # Override timing if provided
    if args.min_delta:
        generator.min_delta = args.min_delta
    if args.max_delta:
        generator.max_delta = args.max_delta
    
    if args.continuous or not args.duration:
        generator.run_realistic_simulation(continuous=True)
    else:
        generator.run_realistic_simulation(duration_minutes=args.duration)

if __name__ == "__main__":
    main()
```

### 5. Integration Points

#### A. Update Docker Compose
Add the new generator to `docker-compose.yml`:
```yaml
realistic-event-generator:
  build:
    context: .
    dockerfile: docker/data-generator/Dockerfile
  container_name: realistic-event-generator
  depends_on:
    - kafka
    - clickhouse
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    - CLICKHOUSE_HOST=clickhouse
  volumes:
    - ./scripts:/app/scripts
    - ./src:/app/src
    - ./data:/app/data
  command: ["python", "scripts/kafka_event_generator.py", "--continuous"]
```

#### B. Update Configuration
Add realistic generator config to `config/settings.py`:
```python
REALISTIC_GENERATOR_CONFIG = {
    "timing": {
        "min_delta_seconds": 10,
        "max_delta_seconds": 60,
        "event_distribution": {
            "sales": 0.5,
            "inventory": 0.2,
            "customer": 0.15,
            "price_change": 0.1,
            "restock": 0.05
        }
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - REALISTIC_GEN - %(levelname)s - %(message)s"
    }
}
```

### 6. Testing Strategy

#### A. Unit Tests
```python
def test_random_timing():
    generator = RealisticEventGenerator()
    
    # Test timing range
    for _ in range(100):
        sleep_time = random.uniform(10, 60)
        assert 10 <= sleep_time <= 60
    
    # Test event distribution
    event_types = []
    for _ in range(1000):
        event_types.append(generator._select_event_type())
    
    # Verify distribution roughly matches weights
    sales_count = event_types.count("sales")
    assert 0.45 <= sales_count / 1000 <= 0.55
```

#### B. Integration Test
```python
def test_event_flow_integration():
    """Test that events flow through the entire system"""
    generator = RealisticEventGenerator()
    
    # Generate events for 5 minutes
    start_time = datetime.now()
    generator.run_realistic_simulation(duration_minutes=5)
    
    # Verify events were generated with realistic timing
    # Check Kafka topics for received events
    # Verify ClickHouse for stored data
```

### 7. Usage Examples

#### Run Continuously:
```bash
python scripts/kafka_event_generator.py --continuous
```

#### Run for Specific Duration:
```bash
python scripts/kafka_event_generator.py --duration 120  # 2 hours
```

#### Custom Timing:
```bash
python scripts/kafka_event_generator.py --continuous --min-delta 5 --max-delta 30
```

### 8. Expected Benefits

1. **Realistic Simulation**: Events occur at irregular intervals like real retail environments
2. **Better Testing**: More realistic data for testing streaming pipelines and ML models
3. **Performance Testing**: Tests system under realistic load patterns
4. **Scenario Testing**: Can simulate different retail scenarios (peak hours, weekends, etc.)

## Next Steps for Implementation

1. **Switch to Code Mode** to implement the Python script
2. **Update configuration** in `config/settings.py`
3. **Test integration** with existing Kafka topics
4. **Update Docker configuration** for the new generator
5. **Document usage** in project README

This implementation will provide a much more realistic event generation pattern that better mimics real-world retail scenarios.