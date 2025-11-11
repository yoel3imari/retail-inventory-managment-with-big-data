#!/usr/bin/env python3
"""
Simple script to populate ClickHouse with sample data
This demonstrates that ClickHouse tables can be populated and verified
"""

import requests
import json
from datetime import datetime, timedelta

def populate_sample_data():
    """Populate ClickHouse with sample data."""
    
    base_url = "http://clickhouse:8123"
    auth = ('default', 'clickhouse')
    
    print("📊 Populating ClickHouse with Sample Data")
    print("=" * 50)
    
    # Insert sample dimension data
    print("\n📋 Inserting dimension data...")
    
    # Insert sample products
    products = [
        ("PROD001", "SKU10001", "Premium Headphones", "Electronics", "Audio", "TechBrand", "SupplierA", 299.99, 365),
        ("PROD002", "SKU10002", "Smart Watch", "Electronics", "Wearables", "TechBrand", "SupplierB", 199.99, 365),
        ("PROD003", "SKU10003", "Coffee Maker", "Home & Kitchen", "Appliances", "HomeBrand", "SupplierC", 89.99, 730)
    ]
    
    for product in products:
        query = f"""
        INSERT INTO retail.dim_product VALUES 
        ('{product[0]}', '{product[1]}', '{product[2]}', '{product[3]}', '{product[4]}', 
         '{product[5]}', '{product[6]}', {product[7]}, {product[8]}, now())
        """
        try:
            response = requests.post(f"{base_url}/", params={"query": query}, auth=auth, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Inserted product: {product[2]}")
        except Exception as e:
            print(f"  ❌ Failed to insert product: {e}")
    
    # Insert sample stores
    stores = [
        ("STORE001", "STORE101", "Downtown Flagship", "New York", "Northeast", "USA", 5000, "Flagship"),
        ("STORE002", "STORE102", "Mall Location", "Chicago", "Midwest", "USA", 3000, "Mall"),
        ("STORE003", "STORE103", "Airport Store", "Los Angeles", "West", "USA", 1500, "Airport")
    ]
    
    for store in stores:
        query = f"""
        INSERT INTO retail.dim_store VALUES 
        ('{store[0]}', '{store[1]}', '{store[2]}', '{store[3]}', '{store[4]}', 
         '{store[5]}', {store[6]}, '{store[7]}', now())
        """
        try:
            response = requests.post(f"{base_url}/", params={"query": query}, auth=auth, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Inserted store: {store[2]}")
        except Exception as e:
            print(f"  ❌ Failed to insert store: {e}")
    
    # Insert sample sales data
    print("\n💰 Inserting sample sales data...")
    today = datetime.now().date()
    
    sales = [
        ("SALE001", today.isoformat(), "PROD001", "STORE001", 2, 599.98, 400.00, 199.98, 
         datetime.now().isoformat(), "CUST001", "credit_card"),
        ("SALE002", today.isoformat(), "PROD002", "STORE002", 1, 199.99, 120.00, 79.99, 
         (datetime.now() - timedelta(hours=1)).isoformat(), "CUST002", "debit_card"),
        ("SALE003", today.isoformat(), "PROD003", "STORE003", 3, 269.97, 180.00, 89.97, 
         (datetime.now() - timedelta(hours=2)).isoformat(), "CUST003", "cash")
    ]
    
    for sale in sales:
        query = f"""
        INSERT INTO retail.fact_sales VALUES 
        ('{sale[0]}', '{sale[1]}', '{sale[2]}', '{sale[3]}', {sale[4]}, {sale[5]}, 
         {sale[6]}, {sale[7]}, '{sale[8]}', '{sale[9]}', '{sale[10]}')
        """
        try:
            response = requests.post(f"{base_url}/", params={"query": query}, auth=auth, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Inserted sale: {sale[0]}")
        except Exception as e:
            print(f"  ❌ Failed to insert sale: {e}")
    
    # Insert sample inventory data
    print("\n📦 Inserting sample inventory data...")
    
    inventory = [
        ("INV001", today.isoformat(), "PROD001", "STORE001", 45, 10, 5, now()),
        ("INV002", today.isoformat(), "PROD002", "STORE002", 22, 5, 3, now()),
        ("INV003", today.isoformat(), "PROD003", "STORE003", 67, 15, 8, now())
    ]
    
    for inv in inventory:
        query = f"""
        INSERT INTO retail.fact_inventory VALUES 
        ('{inv[0]}', '{inv[1]}', '{inv[2]}', '{inv[3]}', {inv[4]}, {inv[5]}, {inv[6]}, '{inv[7]}')
        """
        try:
            response = requests.post(f"{base_url}/", params={"query": query}, auth=auth, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Inserted inventory: {inv[0]}")
        except Exception as e:
            print(f"  ❌ Failed to insert inventory: {e}")
    
    print("\n✅ Sample data population completed!")
    print("💡 Run the verification script to check the populated tables")

def now():
    """Get current datetime in ISO format."""
    return datetime.now().isoformat()

if __name__ == "__main__":
    try:
        populate_sample_data()
    except Exception as e:
        print(f"❌ Error: {e}")