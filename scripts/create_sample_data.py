#!/usr/bin/env python3
"""
Sample Data Generator for Retail Inventory Management
Creates initial dimension data for products, stores, and categories
"""

import argparse
import json
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    def __init__(self):
        self.categories = [
            "Electronics", "Clothing", "Food & Beverages", "Home & Garden", 
            "Sports & Outdoors", "Beauty & Personal Care", "Toys & Games",
            "Books & Media", "Automotive", "Health & Wellness"
        ]
        
        self.brands = {
            "Electronics": ["Apple", "Samsung", "Sony", "LG", "Dell"],
            "Clothing": ["Nike", "Adidas", "Zara", "H&M", "Levi's"],
            "Food & Beverages": ["Coca-Cola", "Nestle", "Kellogg's", "Heinz", "PepsiCo"],
            "Home & Garden": ["IKEA", "Home Depot", "Scotts", "Weber", "Black & Decker"],
            "Sports & Outdoors": ["Nike", "Adidas", "Under Armour", "Columbia", "The North Face"],
            "Beauty & Personal Care": ["L'Oreal", "Procter & Gamble", "Estee Lauder", "Johnson & Johnson", "Unilever"],
            "Toys & Games": ["Lego", "Hasbro", "Mattel", "Nintendo", "Fisher-Price"],
            "Books & Media": ["Penguin", "HarperCollins", "Random House", "Scholastic", "Disney"],
            "Automotive": ["Toyota", "Ford", "Honda", "BMW", "Mercedes-Benz"],
            "Health & Wellness": ["Pfizer", "Novartis", "Roche", "Merck", "GlaxoSmithKline"]
        }
        
        self.regions = ["North", "South", "East", "West", "Central"]
        self.store_types = ["Supermarket", "Convenience Store", "Hypermarket", "Specialty Store", "Department Store"]
        
    def generate_categories(self) -> List[Dict[str, Any]]:
        """Generate category data"""
        categories = []
        for category_name in self.categories:
            category = {
                "category_key": str(uuid.uuid4()),
                "category_name": category_name,
                "description": f"Products in {category_name} category",
                "created_date": datetime.now().isoformat()
            }
            categories.append(category)
        return categories
    
    def generate_brands(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate brand data"""
        brands = []
        for category in categories:
            category_name = category["category_name"]
            if category_name in self.brands:
                for brand_name in self.brands[category_name]:
                    brand = {
                        "brand_key": str(uuid.uuid4()),
                        "brand_name": brand_name,
                        "category_key": category["category_key"],
                        "description": f"{brand_name} brand products",
                        "created_date": datetime.now().isoformat()
                    }
                    brands.append(brand)
        return brands
    
    def generate_products(self, brands: List[Dict[str, Any]], count: int = 100) -> List[Dict[str, Any]]:
        """Generate product data"""
        products = []
        
        # Product templates by category
        product_templates = {
            "Electronics": [
                {"name": "Smartphone", "price_range": (300, 1200), "cost_multiplier": 0.6},
                {"name": "Laptop", "price_range": (500, 2500), "cost_multiplier": 0.65},
                {"name": "Headphones", "price_range": (50, 400), "cost_multiplier": 0.55},
                {"name": "Tablet", "price_range": (200, 800), "cost_multiplier": 0.6},
                {"name": "Smart Watch", "price_range": (150, 600), "cost_multiplier": 0.5}
            ],
            "Clothing": [
                {"name": "T-Shirt", "price_range": (10, 50), "cost_multiplier": 0.4},
                {"name": "Jeans", "price_range": (30, 100), "cost_multiplier": 0.45},
                {"name": "Jacket", "price_range": (50, 200), "cost_multiplier": 0.5},
                {"name": "Shoes", "price_range": (40, 150), "cost_multiplier": 0.4},
                {"name": "Dress", "price_range": (25, 120), "cost_multiplier": 0.45}
            ],
            "Food & Beverages": [
                {"name": "Snacks", "price_range": (2, 10), "cost_multiplier": 0.3},
                {"name": "Beverages", "price_range": (1, 5), "cost_multiplier": 0.25},
                {"name": "Frozen Food", "price_range": (3, 15), "cost_multiplier": 0.35},
                {"name": "Bakery", "price_range": (1, 8), "cost_multiplier": 0.2},
                {"name": "Dairy", "price_range": (2, 12), "cost_multiplier": 0.3}
            ]
        }
        
        import random
        
        for i in range(count):
            brand = random.choice(brands)
            category_name = next((cat["category_name"] for cat in self.categories_data 
                                if cat["category_key"] == brand["category_key"]), "General")
            
            if category_name in product_templates:
                template = random.choice(product_templates[category_name])
                product_name = f"{brand['brand_name']} {template['name']}"
                unit_price = random.uniform(*template["price_range"])
                cost_price = unit_price * template["cost_multiplier"]
            else:
                product_name = f"{brand['brand_name']} Product {i+1}"
                unit_price = random.uniform(10, 100)
                cost_price = unit_price * 0.5
            
            product = {
                "product_key": str(uuid.uuid4()),
                "sku": f"SKU{10000 + i}",
                "product_name": product_name,
                "category_key": brand["category_key"],
                "brand_key": brand["brand_key"],
                "unit_price": round(unit_price, 2),
                "cost_price": round(cost_price, 2),
                "shelf_life_days": random.randint(7, 365),
                "supplier": f"Supplier {random.randint(1, 20)}",
                "created_date": datetime.now().isoformat()
            }
            products.append(product)
        
        return products
    
    def generate_stores(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate store data"""
        stores = []
        
        cities = {
            "North": ["New York", "Boston", "Chicago", "Detroit", "Philadelphia"],
            "South": ["Atlanta", "Miami", "Dallas", "Houston", "Charlotte"],
            "East": ["Washington DC", "Baltimore", "Richmond", "Raleigh", "Norfolk"],
            "West": ["Los Angeles", "San Francisco", "Seattle", "Denver", "Phoenix"],
            "Central": ["St. Louis", "Kansas City", "Minneapolis", "Indianapolis", "Nashville"]
        }
        
        import random
        
        for i in range(count):
            region = random.choice(self.regions)
            city = random.choice(cities[region])
            store_type = random.choice(self.store_types)
            
            store = {
                "store_key": str(uuid.uuid4()),
                "store_id": f"STORE{100 + i}",
                "store_name": f"{city} {store_type}",
                "city": city,
                "region": region,
                "country": "USA",
                "square_footage": random.choice([5000, 10000, 15000, 20000, 25000]),
                "store_type": store_type,
                "created_date": datetime.now().isoformat()
            }
            stores.append(store)
        
        return stores
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Save data to JSON file"""
        with open(f"data/{filename}", 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} records to data/{filename}")
    
    def generate_all_data(self, stores_count: int, products_count: int, categories_count: int):
        """Generate all sample data"""
        logger.info("Starting sample data generation...")
        
        # Generate categories
        categories = self.generate_categories()
        self.categories_data = categories
        self.save_to_json(categories, "categories.json")
        
        # Generate brands
        brands = self.generate_brands(categories)
        self.save_to_json(brands, "brands.json")
        
        # Generate products
        products = self.generate_products(brands, products_count)
        self.save_to_json(products, "products.json")
        
        # Generate stores
        stores = self.generate_stores(stores_count)
        self.save_to_json(stores, "stores.json")
        
        logger.info("Sample data generation completed!")
        
        # Print summary
        print("\n📊 Sample Data Summary:")
        print("======================")
        print(f"Categories: {len(categories)}")
        print(f"Brands: {len(brands)}")
        print(f"Products: {len(products)}")
        print(f"Stores: {len(stores)}")
        print("\nData saved to ./data/ directory")

def main():
    parser = argparse.ArgumentParser(description="Generate sample data for retail inventory management")
    parser.add_argument("--stores", type=int, default=10, help="Number of stores to generate")
    parser.add_argument("--products", type=int, default=100, help="Number of products to generate")
    parser.add_argument("--categories", type=int, default=10, help="Number of categories to generate")
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    
    generator = SampleDataGenerator()
    generator.generate_all_data(
        stores_count=args.stores,
        products_count=args.products,
        categories_count=args.categories
    )

if __name__ == "__main__":
    main()