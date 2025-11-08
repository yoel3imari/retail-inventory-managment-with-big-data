#!/bin/bash

# ClickHouse Database Initialization Script
# This script initializes the retail database with all required schemas

set -e

# Configuration
CLICKHOUSE_HOST="clickhouse"
CLICKHOUSE_PORT="8123"
CLICKHOUSE_USER="default"
CLICKHOUSE_PASSWORD="clickhouse"
DATABASE="retail"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Wait for ClickHouse to be ready
wait_for_clickhouse() {
    log "Waiting for ClickHouse to be ready..."
    until curl -s "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/ping" > /dev/null; do
        log "ClickHouse is not ready yet. Waiting..."
        sleep 5
    done
    log_success "ClickHouse is ready!"
}

# Execute ClickHouse query
execute_query() {
    local query="$1"
    local description="$2"
    
    log "Executing: $description"
    
    if curl -s \
        -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
        -X POST \
        -d "$query" \
        "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" > /dev/null; then
        log_success "Successfully executed: $description"
    else
        log_error "Failed to execute: $description"
        return 1
    fi
}

# Execute SQL file
execute_sql_file() {
    local file="$1"
    local description="$2"
    
    log "Executing SQL file: $description"
    
    if curl -s \
        -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
        -X POST \
        --data-binary @"$file" \
        "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" > /dev/null; then
        log_success "Successfully executed SQL file: $description"
    else
        log_error "Failed to execute SQL file: $description"
        return 1
    fi
}

# Check if database exists
check_database_exists() {
    local query="SHOW DATABASES LIKE '${DATABASE}'"
    
    if curl -s \
        -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
        -X POST \
        -d "$query" \
        "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" | grep -q "${DATABASE}"; then
        return 0  # Database exists
    else
        return 1  # Database doesn't exist
    fi
}

# Drop database (for testing/development)
drop_database() {
    log "Dropping database: ${DATABASE}"
    execute_query "DROP DATABASE IF EXISTS ${DATABASE}" "Drop database ${DATABASE}"
}

# Initialize database
initialize_database() {
    log "Starting database initialization..."
    
    # Wait for ClickHouse to be ready
    wait_for_clickhouse
    
    # Check if database already exists
    if check_database_exists; then
        log_warning "Database '${DATABASE}' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            drop_database
        else
            log "Using existing database"
            return 0
        fi
    fi
    
    # Execute schema files in order
    log "Creating database schema..."
    
    # Execute main schema
    execute_sql_file "01-schema.sql" "Main database schema"
    
    # Execute enhanced schema
    execute_sql_file "02-enhanced-schema.sql" "Enhanced database schema"
    
    # Verify database creation
    if check_database_exists; then
        log_success "Database '${DATABASE}' initialized successfully!"
        
        # Show table count
        local table_count=$(curl -s \
            -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
            -X POST \
            -d "SELECT count() FROM system.tables WHERE database = '${DATABASE}'" \
            "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" | tail -n 1)
        
        log "Created ${table_count} tables in database '${DATABASE}'"
        
        # Show table list
        log "Tables created:"
        curl -s \
            -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
            -X POST \
            -d "SELECT name FROM system.tables WHERE database = '${DATABASE}' ORDER BY name" \
            "http://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/" | tail -n +2
        
    else
        log_error "Failed to verify database creation"
        return 1
    fi
}

# Test database connectivity
test_connectivity() {
    log "Testing database connectivity..."
    
    if execute_query "SELECT 'Connection test successful' as test_result" "Connection test"; then
        log_success "Database connectivity test passed"
        return 0
    else
        log_error "Database connectivity test failed"
        return 1
    fi
}

# Show database status
show_status() {
    log "Database Status:"
    
    # Show database info
    execute_query "SELECT name, engine, tables, partitions FROM system.databases WHERE name = '${DATABASE}'" "Database info"
    
    # Show table sizes
    execute_query "
    SELECT 
        table,
        formatReadableSize(sum(bytes)) as size,
        sum(rows) as rows,
        max(modification_time) as last_modified
    FROM system.parts 
    WHERE database = '${DATABASE}' AND active
    GROUP BY table
    ORDER BY sum(bytes) DESC
    " "Table sizes"
}

# Show usage
usage() {
    echo "Usage: $0 {init|drop|test|status|help}"
    echo ""
    echo "Commands:"
    echo "  init    - Initialize database with schemas"
    echo "  drop    - Drop database (for testing)"
    echo "  test    - Test database connectivity"
    echo "  status  - Show database status"
    echo "  help    - Show this help message"
    echo ""
}

# Main execution
case "$1" in
    init)
        initialize_database
        ;;
    drop)
        drop_database
        ;;
    test)
        test_connectivity
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Invalid command: $1"
        usage
        exit 1
        ;;
esac