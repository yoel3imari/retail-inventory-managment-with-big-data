#!/usr/bin/env python3
"""
ClickHouse Table Verification Script
This script provides multiple methods to verify if ClickHouse tables are not empty.
"""

import requests
import json
import os
from typing import Dict, List, Any

class ClickHouseTableVerifier:
    def __init__(self, host: str = None, port: int = 8123,
                 username: str = "default", password: str = "clickhouse"):
        # Use environment variable or default to localhost
        self.host = host or os.environ.get('CLICKHOUSE_HOST', 'localhost')
        self.base_url = f"http://{self.host}:{port}"
        self.auth = (username, password)
        self.database = "retail"
    
    def execute_query(self, query: str) -> Any:
        """Execute a ClickHouse query and return the result."""
        try:
            response = requests.post(
                f"{self.base_url}",
                params={"query": query},
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error executing query: {e}")
            return None
    
    def get_table_list(self) -> List[str]:
        """Get list of all tables in the retail database."""
        query = f"SHOW TABLES FROM {self.database}"
        result = self.execute_query(query)
        if result:
            return [table.strip() for table in result.split('\n') if table.strip()]
        return []
    
    def check_table_row_count(self, table_name: str) -> int:
        """Check row count for a specific table."""
        query = f"SELECT count(*) FROM {self.database}.{table_name}"
        result = self.execute_query(query)
        return int(result) if result and result.isdigit() else 0
    
    def check_table_exists_and_has_data(self, table_name: str) -> Dict[str, Any]:
        """Check if table exists and has data."""
        query = f"""
        SELECT 
            count(*) as row_count,
            min(1) as table_exists
        FROM {self.database}.{table_name}
        """
        result = self.execute_query(query)
        if result and result.isdigit():
            return {
                "table_name": table_name,
                "exists": True,
                "row_count": int(result),
                "has_data": int(result) > 0
            }
        else:
            return {
                "table_name": table_name,
                "exists": False,
                "row_count": 0,
                "has_data": False
            }
    
    def get_table_sizes(self) -> List[Dict[str, Any]]:
        """Get table sizes and row counts from system tables."""
        query = f"""
        SELECT 
            table,
            sum(bytes) as size_bytes,
            formatReadableSize(sum(bytes)) as size_readable,
            sum(rows) as row_count
        FROM system.parts 
        WHERE database = '{self.database}' AND active
        GROUP BY table
        ORDER BY size_bytes DESC
        """
        result = self.execute_query(query)
        if result:
            lines = result.strip().split('\n')
            headers = ['table', 'size_bytes', 'size_readable', 'row_count']
            tables = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) == len(headers):
                    table_data = dict(zip(headers, parts))
                    table_data['size_bytes'] = int(table_data['size_bytes'])
                    table_data['row_count'] = int(table_data['row_count'])
                    tables.append(table_data)
            return tables
        return []
    
    def verify_all_tables(self) -> Dict[str, Any]:
        """Verify all tables in the database."""
        tables = self.get_table_list()
        results = {
            "database": self.database,
            "total_tables": len(tables),
            "tables_with_data": 0,
            "empty_tables": 0,
            "table_details": []
        }
        
        for table in tables:
            table_info = self.check_table_exists_and_has_data(table)
            results["table_details"].append(table_info)
            
            if table_info["exists"]:
                if table_info["has_data"]:
                    results["tables_with_data"] += 1
                else:
                    results["empty_tables"] += 1
        
        return results
    
    def quick_health_check(self) -> Dict[str, Any]:
        """Perform a quick health check of the database."""
        # Check database exists
        db_check = self.execute_query(f"EXISTS DATABASE {self.database}")
        db_exists = db_check == "1" if db_check else False
        
        if not db_exists:
            return {"status": "error", "message": f"Database {self.database} does not exist"}
        
        # Get basic table info
        tables_info = self.verify_all_tables()
        table_sizes = self.get_table_sizes()
        
        return {
            "status": "healthy",
            "database": self.database,
            "database_exists": True,
            "total_tables": tables_info["total_tables"],
            "tables_with_data": tables_info["tables_with_data"],
            "empty_tables": tables_info["empty_tables"],
            "table_sizes": table_sizes
        }


def main():
    """Main function to demonstrate table verification."""
    # Try different hosts for container vs local execution
    hosts_to_try = [
        os.environ.get('CLICKHOUSE_HOST', 'localhost'),
        'clickhouse',  # Docker container name
        'localhost'
    ]
    
    verifier = None
    for host in hosts_to_try:
        try:
            print(f"🔍 Trying to connect to ClickHouse at {host}:8123...")
            verifier = ClickHouseTableVerifier(host=host)
            # Test connection
            test_result = verifier.execute_query("SELECT version()")
            if test_result:
                print(f"✅ Connected to ClickHouse at {host}")
                break
        except Exception as e:
            print(f"❌ Failed to connect to {host}: {e}")
            continue
    
    if not verifier:
        print("❌ Could not connect to ClickHouse from any host")
        print("💡 Make sure ClickHouse is running and accessible")
        return
    
    print("=" * 50)
    
    # Quick health check
    print("\n📊 Quick Health Check:")
    health = verifier.quick_health_check()
    if health["status"] == "healthy":
        print(f"✅ Database: {health['database']}")
        print(f"📋 Total Tables: {health['total_tables']}")
        print(f"📈 Tables with Data: {health['tables_with_data']}")
        print(f"📉 Empty Tables: {health['empty_tables']}")
        
        if health["table_sizes"]:
            print(f"\n💾 Table Sizes:")
            for table in health["table_sizes"]:
                print(f"  - {table['table']}: {table['row_count']} rows, {table['size_readable']}")
    else:
        print(f"❌ {health['message']}")
    
    # Detailed table verification
    print(f"\n🔍 Detailed Table Verification for {verifier.database}:")
    tables = verifier.get_table_list()
    
    for table in tables:
        info = verifier.check_table_exists_and_has_data(table)
        status = "✅ HAS DATA" if info["has_data"] else "❌ EMPTY"
        print(f"  {status} {table}: {info['row_count']} rows")
    
    # Alternative method using system tables
    print(f"\n📈 Alternative Method - System Tables:")
    table_sizes = verifier.get_table_sizes()
    if table_sizes:
        for table in table_sizes:
            status = "✅" if table['row_count'] > 0 else "❌"
            print(f"  {status} {table['table']}: {table['row_count']} rows, {table['size_readable']}")
    else:
        print("  No table size information available")


if __name__ == "__main__":
    main()