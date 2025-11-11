#!/usr/bin/env python3
"""
ClickHouse Table Verification Script for Container Environments
This script works from within Docker containers to verify ClickHouse tables.
"""

import requests
import os
import sys

def check_clickhouse_tables():
    """Check ClickHouse tables from container environment."""
    
    # Try different possible ClickHouse hosts
    hosts_to_try = [
        os.environ.get('CLICKHOUSE_HOST', 'clickhouse'),  # Docker container name
        'clickhouse',  # Default container name
        'localhost'    # Local development
    ]
    
    username = os.environ.get('CLICKHOUSE_USER', 'default')
    password = os.environ.get('CLICKHOUSE_PASSWORD', 'clickhouse')
    database = 'retail'
    
    print("🔍 ClickHouse Table Verification (Container Edition)")
    print("=" * 60)
    
    # Find working ClickHouse connection
    base_url = None
    for host in hosts_to_try:
        try:
            test_url = f"http://{host}:8123/?query=SELECT%20version()"
            response = requests.get(test_url, auth=(username, password), timeout=5)
            if response.status_code == 200:
                base_url = f"http://{host}:8123"
                print(f"✅ Connected to ClickHouse at {host}")
                break
            else:
                print(f"❌ Failed to connect to {host}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to connect to {host}: {str(e)}")
            continue
    
    if not base_url:
        print("❌ Could not connect to ClickHouse from any host")
        print("💡 Make sure ClickHouse container is running and accessible")
        return
    
    # Check if database exists
    try:
        db_check_query = f"SELECT count(*) FROM system.databases WHERE name = '{database}'"
        db_check_url = f"{base_url}/?query={db_check_query}"
        response = requests.get(db_check_url, auth=(username, password), timeout=10)
        
        if response.text.strip() == "1":
            print(f"✅ Database '{database}' exists")
        else:
            print(f"❌ Database '{database}' does not exist")
            return
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return
    
    # Get list of tables
    try:
        tables_query = f"SHOW TABLES FROM {database}"
        tables_url = f"{base_url}/?query={tables_query}"
        response = requests.get(tables_url, auth=(username, password), timeout=10)
        tables = [table.strip() for table in response.text.strip().split('\n') if table.strip()]
        
        print(f"\n📋 Found {len(tables)} tables in '{database}' database:")
        
        # Check each table for data
        tables_with_data = 0
        empty_tables = 0
        
        for table in tables:
            try:
                count_query = f"SELECT count(*) FROM {database}.{table}"
                count_url = f"{base_url}/?query={count_query}"
                response = requests.get(count_url, auth=(username, password), timeout=10)
                row_count = int(response.text.strip()) if response.text.strip().isdigit() else 0
                
                if row_count > 0:
                    print(f"  ✅ {table}: {row_count} rows")
                    tables_with_data += 1
                else:
                    print(f"  ❌ {table}: EMPTY (0 rows)")
                    empty_tables += 1
                    
            except Exception as e:
                print(f"  ⚠️  {table}: ERROR - {e}")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  Total tables: {len(tables)}")
        print(f"  Tables with data: {tables_with_data}")
        print(f"  Empty tables: {empty_tables}")
        
        if tables_with_data == 0:
            print(f"\n🚨 All tables are empty!")
            print(f"💡 Data may not be flowing from Kafka to ClickHouse")
            print(f"💡 Check if Spark streaming jobs are running")
        
    except Exception as e:
        print(f"❌ Error getting table list: {e}")

def main():
    """Main function."""
    try:
        check_clickhouse_tables()
    except KeyboardInterrupt:
        print("\n👋 Script interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()