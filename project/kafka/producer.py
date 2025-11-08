#!/usr/bin/env python3
"""
Kafka Producer for Retail Inventory System
Produces sales, inventory, and stock movement events to Kafka topics
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import uuid
from faker import Faker

fake = Faker()

class RetailKafkaProducer:
    def __init__(self, bootstrap_servers='localhost:9092'):
        """Initialize Kafka producer with configuration"""
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.connect()
        
    def connect(self):
        """Connect to Kafka broker with retry logic"""
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=5,
                    compression_type='gzip',
                    linger_ms=10,  # Batch messages for efficiency
                    batch_size=16384
                )
                print(f"✅ Connected to Kafka at {self.bootstrap_servers}")
                return
            except Exception as e:
                print(f"⏳ Attempt {attempt + 1}/{max_retries}: Waiting for Kafka... ({e})")
                time.sleep(5)
        raise Exception("Failed to connect to Kafka broker")
    
    def send_message(self, topic, message, key=None):
        """Send a message to Kafka topic with callback"""
        try:
            future = self.producer.send(
                topic, 
                key=key,
                value=message
            )
            
            # Add callback for success/failure
            future.add_callback(self.on_send_success, topic)
            future.add_errback(self.on_send_error)
            
            return future
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    def on_send_success(self, topic, record_metadata):
        """Callback for successful message send"""
        # Uncomment for debugging
        # print(f"✓ Sent to {topic} [partition: {record_metadata.partition}, offset: {record_metadata.offset}]")
        pass
    
    def on_send_error(self, exc):
        """Callback for failed message send"""
        print(f"❌ Failed to send message: {exc}")
    
    def produce_sale_transaction(self, product_id=None, store_id=None):
        """Produce a sales transaction event"""
        if not product_id:
            product_id = f'PROD-{random.randint(1, 250):03d}'
        if not store_id:
            store_id = f'STORE-{random.randint(1, 20):03d}'
        
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(5.99, 999.99), 2)
        discount = round(random.uniform(0, unit_price * 0.3), 2) if random.random() < 0.2 else 0
        
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'product_id': product_id,
            'store_id': store_id,
            'quantity_sold': quantity,
            'unit_price': unit_price,
            'discount_amount': discount,
            'total_amount': round((unit_price * quantity) - discount, 2),
            'payment_method': random.choice(['CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'MOBILE_PAY']),
            'customer_id': f'CUST-{random.randint(1000, 9999)}',
            'transaction_time': datetime.now().isoformat(),
            'timestamp': int(time.time() * 1000)
        }
        
        self.send_message(
            topic='retail-sales',
            message=transaction,
            key=transaction['transaction_id']
        )
        return transaction
    
    def produce_inventory_update(self, product_id=None, store_id=None):
        """Produce an inventory update event"""
        if not product_id:
            product_id = f'PROD-{random.randint(1, 250):03d}'
        if not store_id:
            store_id = f'STORE-{random.randint(1, 20):03d}'
        
        quantity_on_hand = random.randint(0, 1000)
        quantity_reserved = random.randint(0, min(50, quantity_on_hand))
        
        inventory = {
            'inventory_id': str(uuid.uuid4()),
            'product_id': product_id,
            'store_id': store_id,
            'warehouse_id': f'WH-{random.randint(1, 5):02d}',
            'quantity_on_hand': quantity_on_hand,
            'quantity_reserved': quantity_reserved,
            'quantity_available': quantity_on_hand - quantity_reserved,
            'reorder_point': random.randint(20, 100),
            'reorder_quantity': random.randint(100, 500),
            'last_updated': datetime.now().isoformat(),
            'timestamp': int(time.time() * 1000)
        }
        
        self.send_message(
            topic='retail-inventory-updates',
            message=inventory,
            key=f"{product_id}:{store_id}"
        )
        return inventory
    
    def produce_stock_movement(self, product_id=None):
        """Produce a stock movement event"""
        if not product_id:
            product_id = f'PROD-{random.randint(1, 250):03d}'
        
        movement_type = random.choice(['PURCHASE', 'SALE', 'TRANSFER', 'ADJUSTMENT', 'RETURN'])
        stores = [f'STORE-{i:03d}' for i in range(1, 21)]
        
        movement = {
            'movement_id': str(uuid.uuid4()),
            'product_id': product_id,
            'from_location': random.choice(stores + ['SUPPLIER', 'WAREHOUSE']),
            'to_location': random.choice(stores + ['CUSTOMER', 'WAREHOUSE']),
            'movement_type': movement_type,
            'quantity': random.randint(1, 100),
            'movement_time': datetime.now().isoformat(),
            'reason': fake.sentence(nb_words=6),
            'user_id': f'USER-{random.randint(1, 50):03d}',
            'timestamp': int(time.time() * 1000)
        }
        
        self.send_message(
            topic='retail-stock-movements',
            message=movement,
            key=movement['movement_id']
        )
        return movement
    
    def produce_batch(self, event_type='all', count=10, delay=0.5):
        """Produce a batch of events"""
        print(f"🚀 Producing {count} {event_type} events...")
        
        producers_map = {
            'sales': self.produce_sale_transaction,
            'inventory': self.produce_inventory_update,
            'movements': self.produce_stock_movement
        }
        
        for i in range(count):
            if event_type == 'all':
                # Weighted random selection
                selected = random.choices(
                    ['sales', 'inventory', 'movements'],
                    weights=[0.6, 0.3, 0.1]
                )[0]
                producers_map[selected]()
            else:
                producers_map[event_type]()
            
            if (i + 1) % 10 == 0:
                print(f"  📊 Produced {i + 1}/{count} events")
            
            time.sleep(delay)
        
        # Flush remaining messages
        self.producer.flush()
        print(f"✅ Completed: {count} events produced")
    
    def close(self):
        """Close the producer and flush remaining messages"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            print("🔒 Producer closed")


def main():
    """Main function for interactive producer"""
    print("=" * 60)
    print("🏪 RETAIL INVENTORY - KAFKA PRODUCER")
    print("=" * 60)
    
    # Initialize producer
    producer = RetailKafkaProducer(bootstrap_servers='localhost:9092')
    
    try:
        while True:
            print("\n📋 Menu:")
            print("1. Produce sales transactions")
            print("2. Produce inventory updates")
            print("3. Produce stock movements")
            print("4. Produce all events (mixed)")
            print("5. Continuous stream")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '6':
                break
            elif choice == '5':
                print("\n🔄 Starting continuous stream (Ctrl+C to stop)...")
                try:
                    count = 0
                    while True:
                        event_type = random.choices(
                            ['sales', 'inventory', 'movements'],
                            weights=[0.6, 0.3, 0.1]
                        )[0]
                        
                        if event_type == 'sales':
                            producer.produce_sale_transaction()
                        elif event_type == 'inventory':
                            producer.produce_inventory_update()
                        else:
                            producer.produce_stock_movement()
                        
                        count += 1
                        if count % 50 == 0:
                            print(f"  📊 Total events: {count}")
                        
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    print(f"\n⏹️  Stopped. Total events produced: {count}")
            else:
                count = int(input("How many events? (default 10): ") or "10")
                delay = float(input("Delay between events in seconds? (default 0.5): ") or "0.5")
                
                event_map = {
                    '1': 'sales',
                    '2': 'inventory',
                    '3': 'movements',
                    '4': 'all'
                }
                
                if choice in event_map:
                    producer.produce_batch(
                        event_type=event_map[choice],
                        count=count,
                        delay=delay
                    )
                else:
                    print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    finally:
        producer.close()


if __name__ == '__main__':
    main()