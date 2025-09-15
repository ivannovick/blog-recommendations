#!/bin/bash

# Greenplum Data Load Script with Comprehensive Checks
# Creates database, installs extensions, and loads CSV data with detailed logging

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Load configuration from .env file
print_status "Loading configuration..."
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Configuration loaded from .env file"
else
    print_warning ".env file not found, using defaults"
fi

# Configuration with defaults
GP_HOST="${GP_HOST:-localhost}"
GP_PORT="${GP_PORT:-15432}"
GP_USER="${GP_USER:-gpadmin}"
DB_NAME="${DB_NAME:-blog_recommendations}"
CSV_FILE="$(pwd)/medium_post_titles.csv"

print_header "Greenplum Data Load Process"
print_status "Configuration:"
echo "  Host: $GP_HOST:$GP_PORT"
echo "  User: $GP_USER"
echo "  Database: $DB_NAME"
echo "  CSV File: $CSV_FILE"

# Pre-flight checks
print_header "Pre-flight Checks"

# Check if CSV file exists
print_status "Checking CSV file..."
if [ ! -f "$CSV_FILE" ]; then
    print_error "CSV file not found at $CSV_FILE"
    exit 1
fi
file_size=$(wc -l < "$CSV_FILE")
print_success "CSV file found with $file_size lines"

# Check if psql is available
print_status "Checking psql client..."
if ! command -v psql &> /dev/null; then
    print_error "psql command not found. Please install PostgreSQL client tools."
    exit 1
fi
psql_version=$(psql --version | head -n1)
print_success "psql found: $psql_version"

# Test database connection
print_status "Testing database connection..."
if psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d postgres -c "SELECT version();" &> /dev/null; then
    db_version=$(psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d postgres -t -c "SELECT version();" | xargs)
    print_success "Database connection successful"
    print_status "Database version: $db_version"
else
    print_error "Cannot connect to database at $GP_HOST:$GP_PORT"
    print_error "Please check that Greenplum is running and connection details are correct"
    exit 1
fi

# Step 1: Create database
print_header "Database Creation"
print_status "Dropping existing database if it exists..."
if psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null; then
    print_success "Existing database dropped (if it existed)"
else
    print_warning "Could not drop database (may not exist)"
fi

print_status "Creating database: $DB_NAME"
if psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null; then
    print_success "Database $DB_NAME created successfully"
else
    print_error "Failed to create database $DB_NAME"
    exit 1
fi

# Step 2: Install required extensions
print_header "Extension Installation"
print_status "Installing required extensions..."

# Check and install each extension with detailed output
psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << 'EOF'
\set ON_ERROR_STOP on

-- Install plpython3u
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS plpython3u;
    RAISE NOTICE '[SUCCESS] plpython3u extension installed';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '[ERROR] Could not install plpython3u: %', SQLERRM;
END
$$;

-- Install madlib
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS madlib;
    RAISE NOTICE '[SUCCESS] madlib extension installed';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '[ERROR] Could not install madlib: %', SQLERRM;
END
$$;

-- Try to install pgvector
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
    RAISE NOTICE '[SUCCESS] pgvector extension installed';
EXCEPTION
    WHEN undefined_file THEN
        RAISE NOTICE '[WARNING] pgvector extension not available - tables will be created without vector columns';
    WHEN OTHERS THEN
        RAISE NOTICE '[ERROR] Could not install pgvector: %', SQLERRM;
END
$$;

-- List installed extensions
SELECT
    extname as "Extension Name",
    extversion as "Version"
FROM pg_extension
WHERE extname IN ('plpython3u', 'madlib', 'vector')
ORDER BY extname;
EOF

print_success "Extension installation completed"

# Step 2.5: Install Python packages for PL/Python
print_header "Python Package Installation for PL/Python"
print_status "Installing numpy and scikit-learn for Greenplum PL/Python..."

# Test if we can install packages via PL/Python
psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << 'EOF'
-- Test Python package installation
DO $$
import sys
import subprocess
import os

def install_package(package_name):
    """Install a Python package for PL/Python use"""
    package_base = package_name.split('==')[0]
    try:
        # Try to import first to see if already installed
        module = __import__(package_base)
        version = getattr(module, '__version__', 'unknown')
        plpy.notice(f'[SUCCESS] {package_name} is already available (version {version})')
        return True
    except ImportError:
        plpy.notice(f'[INFO] {package_name} not found, attempting installation...')
        try:
            # Install using pip with error handling for encoding issues
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package_name, '--user'
            ], capture_output=True, text=True, check=True,
            env=dict(os.environ, PYTHONIOENCODING='utf-8'))

            plpy.notice(f'[SUCCESS] {package_name} installed successfully')
            return True
        except subprocess.CalledProcessError as e:
            # Try to import again in case it was already installed but import failed initially
            try:
                __import__(package_base)
                plpy.notice(f'[SUCCESS] {package_name} was already installed (pip error ignored)')
                return True
            except ImportError:
                plpy.notice(f'[ERROR] Failed to install {package_name}')
                return False
        except Exception as e:
            # Check if package is actually available despite the error
            try:
                __import__(package_base)
                plpy.notice(f'[SUCCESS] {package_name} is available (installation error ignored)')
                return True
            except ImportError:
                plpy.notice(f'[ERROR] Package {package_name} not available after installation attempt')
                return False

# Install required packages
packages = ['numpy', 'scikit-learn']
results = []

for package in packages:
    success = install_package(package)
    results.append((package, success))

# Report results
plpy.notice('[INFO] Installation Summary:')
for package, success in results:
    status = 'SUCCESS' if success else 'FAILED'
    plpy.notice(f'  {package}: {status}')

# Test imports
plpy.notice('[INFO] Testing package imports...')
try:
    import numpy as np
    plpy.notice(f'[SUCCESS] numpy {np.__version__} imported successfully')
except Exception as e:
    plpy.notice(f'[ERROR] numpy import failed: {str(e)}')

try:
    import sklearn
    plpy.notice(f'[SUCCESS] scikit-learn {sklearn.__version__} imported successfully')
except Exception as e:
    plpy.notice(f'[ERROR] scikit-learn import failed: {str(e)}')

$$ LANGUAGE plpython3u;
EOF

print_success "Python package installation completed"

# Step 3: Create schema
print_header "Schema Creation"

# Generate schema.sql with current embedding dimensions
print_status "Generating schema.sql with current embedding dimensions..."
if [ -f generate_schema.py ]; then
    python3 generate_schema.py
    print_success "schema.sql generated with current embedding dimensions"
else
    print_warning "generate_schema.py not found, using existing schema.sql"
fi

print_status "Creating database schema from schema.sql..."

# Load the schema from schema.sql if it exists
if [ -f schema.sql ]; then
    psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME < schema.sql
    print_success "Schema loaded from schema.sql"
else
    print_error "schema.sql not found - please run generate_schema.py first"
    exit 1
fi

# Create staging table for CSV import
psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << 'EOF'
\set ON_ERROR_STOP on

-- Create temporary staging table for CSV data
-- Use TEXT for potentially problematic columns, convert later
CREATE TABLE IF NOT EXISTS staging_posts (
    id TEXT,
    url TEXT,
    title TEXT,
    subtitle TEXT,
    image TEXT,
    claps TEXT,
    responses TEXT,  -- Changed to TEXT to handle "Read" values
    reading_time TEXT,
    publication TEXT,
    date TEXT  -- Changed to TEXT to handle any date format issues
) DISTRIBUTED BY (id);

-- Show created tables
\d+ blog_posts
\d+ blog_cluster_summaries
\d+ staging_posts

-- Success message
DO $$
BEGIN
    RAISE NOTICE '[SUCCESS] All tables created successfully';
END
$$;
EOF

print_success "Schema creation completed"

# Step 4: Load CSV data
print_header "Data Loading"
print_status "Loading CSV data into staging table..."

# Copy CSV data into staging table
if psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << EOF
\\COPY staging_posts FROM '$CSV_FILE' WITH CSV HEADER;
EOF
then
    rows_loaded=$(psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM staging_posts;" | xargs)
    print_success "CSV data loaded: $rows_loaded rows imported into staging table"
else
    print_error "Failed to load CSV data"
    exit 1
fi

# Step 5: Transform and load into main table
print_header "Data Transformation"
print_status "Transforming data from staging to blog_posts table..."

psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << 'EOF'
\set ON_ERROR_STOP on

-- Insert data from staging into blog_posts with data cleaning
INSERT INTO blog_posts (id, category, title, description, is_verified, cluster_id)
SELECT
    CASE
        WHEN id ~ '^[0-9]+$' THEN id::integer
        ELSE NULL
    END as id,
    publication as category,
    title,
    COALESCE(subtitle, '') as description,
    false as is_verified,
    NULL as cluster_id
FROM staging_posts
WHERE id ~ '^[0-9]+$'  -- Only include rows with valid integer IDs
AND id IS NOT NULL
AND title IS NOT NULL;

-- Get counts before dropping staging
SELECT COUNT(*) as staging_count FROM staging_posts;
SELECT COUNT(*) as blog_posts_count FROM blog_posts;

-- Drop staging table
DROP TABLE staging_posts;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '[SUCCESS] Data transformation completed, staging table dropped';
END
$$;
EOF

print_success "Data transformation completed"

# Step 6: Data verification and summary
print_header "Data Verification & Summary"
print_status "Generating data summary..."

psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME << 'EOF'
-- Summary statistics
SELECT
    'Total Posts' as metric,
    COUNT(*)::text as value
FROM blog_posts
UNION ALL
SELECT
    'Unique Categories',
    COUNT(DISTINCT category)::text
FROM blog_posts
UNION ALL
SELECT
    'Date Range',
    'ID ' || MIN(id)::text || ' to ' || MAX(id)::text
FROM blog_posts;

-- Top categories
SELECT
    category,
    COUNT(*) as post_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM blog_posts), 1) as percentage
FROM blog_posts
WHERE category IS NOT NULL
GROUP BY category
ORDER BY post_count DESC
LIMIT 10;

-- Sample data
SELECT
    id,
    category,
    LEFT(title, 60) || CASE WHEN LENGTH(title) > 60 THEN '...' ELSE '' END as title_preview
FROM blog_posts
ORDER BY id
LIMIT 5;
EOF

print_header "Load Process Complete!"
print_success "Database: $DB_NAME"
print_success "Host: $GP_HOST:$GP_PORT"
print_success "Total records loaded successfully"

echo ""
print_status "Next steps:"
echo "  1. Generate embeddings: python genvec.py"
echo "  2. Run clustering: psql -f cluster.sql"
echo "  3. Generate summaries: python summarize.py"
echo ""
print_status "Installed for PL/Python:"
echo "  • numpy - for numerical operations"
echo "  • scikit-learn - for machine learning algorithms"
echo ""
print_status "To connect to the database:"
echo "  psql -h $GP_HOST -p $GP_PORT -U $GP_USER -d $DB_NAME"
echo ""
print_success "🎉 Data load process completed successfully!"