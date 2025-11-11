#!/bin/bash
# Quick ClickHouse Table Verification Script

echo "🔍 Quick ClickHouse Table Verification"
echo "========================================"

# Check database exists
echo "📊 Checking database 'retail'..."
DB_EXISTS=$(curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20count(*)%20FROM%20system.databases%20WHERE%20name%20%3D%20'retail'")
if [ "$DB_EXISTS" = "1" ]; then
    echo "✅ Database 'retail' exists"
else
    echo "❌ Database 'retail' does not exist"
    exit 1
fi

# Get list of tables
echo ""
echo "📋 Tables in 'retail' database:"
curl -s "http://default:clickhouse@localhost:8123/?query=SHOW%20TABLES%20FROM%20retail"

# Check key tables for data
echo ""
echo "🔍 Checking key tables for data:"

TABLES=("dim_date" "fact_sales" "fact_inventory" "dim_product" "dim_store" "raw_sales_events" "raw_inventory_events")

for table in "${TABLES[@]}"; do
    COUNT=$(curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20count(*)%20FROM%20retail.${table}")
    if [ "$COUNT" = "0" ]; then
        echo "❌ $table: EMPTY (0 rows)"
    else
        echo "✅ $table: HAS DATA ($COUNT rows)"
    fi
done

# Check if any tables have data
echo ""
echo "📈 Summary:"
TOTAL_TABLES=$(curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20count(*)%20FROM%20system.tables%20WHERE%20database%20%3D%20'retail'")
TABLES_WITH_DATA=$(curl -s "http://default:clickhouse@localhost:8123/?query=SELECT%20count(distinct%20table)%20FROM%20system.parts%20WHERE%20database%20%3D%20'retail'%20AND%20active%20AND%20rows%20%3E%200")

echo "Total tables: $TOTAL_TABLES"
echo "Tables with data: $TABLES_WITH_DATA"

if [ "$TABLES_WITH_DATA" = "0" ]; then
    echo ""
    echo "🚨 All tables are empty! Data generation may not be running."
    echo "💡 Try running: docker-compose up data-generator"
    echo "💡 Or check data generator logs: docker logs data-generator"
fi