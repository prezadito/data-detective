#!/bin/bash
# Database restore script for Data Detective Academy
#
# This script restores a database from a backup file.
# Supports both SQLite (development) and PostgreSQL (production).
#
# Usage:
#   ./scripts/restore.sh <backup_file>
#
# Environment Variables:
#   DATABASE_URL - Database connection string (from .env)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Backup file not specified${NC}"
    echo "Usage: ./scripts/restore.sh <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  Warning: .env file not found. Using default DATABASE_URL.${NC}"
fi

# Default values
DATABASE_URL=${DATABASE_URL:-"sqlite:///./data_detective_academy.db"}

echo "🔄 Starting database restore..."
echo "   Backup file: $BACKUP_FILE"
echo "   Database: $DATABASE_URL"
echo ""

# Confirm before restoring
echo -e "${YELLOW}⚠️  WARNING: This will REPLACE the current database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""

# Detect database type
if [[ $DATABASE_URL == sqlite:* ]]; then
    # SQLite restore
    echo "📦 Detected SQLite database"

    # Extract database file path from URL
    DB_FILE=$(echo "$DATABASE_URL" | sed 's|sqlite:///\./||' | sed 's|sqlite:///||')

    # Check if backup is compressed
    if [[ $BACKUP_FILE == *.gz ]]; then
        echo "📂 Decompressing backup..."
        TEMP_FILE="${BACKUP_FILE%.gz}"
        gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
        RESTORE_FROM="$TEMP_FILE"
    else
        RESTORE_FROM="$BACKUP_FILE"
    fi

    # Backup current database if it exists
    if [ -f "$DB_FILE" ]; then
        echo "💾 Backing up current database..."
        CURRENT_BACKUP="${DB_FILE}.before_restore_$(date +%Y%m%d_%H%M%S)"
        cp "$DB_FILE" "$CURRENT_BACKUP"
        echo "   Current database backed up to: $CURRENT_BACKUP"
    fi

    # Restore database
    echo "📥 Restoring database..."
    cp "$RESTORE_FROM" "$DB_FILE"

    # Clean up temp file if we decompressed
    if [[ $BACKUP_FILE == *.gz ]]; then
        rm -f "$TEMP_FILE"
    fi

    echo -e "${GREEN}✅ SQLite database restored successfully${NC}"

elif [[ $DATABASE_URL == postgresql:* ]] || [[ $DATABASE_URL == postgres:* ]]; then
    # PostgreSQL restore
    echo "📦 Detected PostgreSQL database"

    # Parse PostgreSQL connection string
    DB_URL_NO_SCHEME=$(echo "$DATABASE_URL" | sed 's|postgresql://||' | sed 's|postgres://||')

    # Extract components
    DB_USER=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f1)
    DB_PASS=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f2 | cut -d@ -f1)
    DB_HOST=$(echo "$DB_URL_NO_SCHEME" | cut -d@ -f2 | cut -d: -f1)
    DB_PORT=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f3 | cut -d/ -f1)
    DB_NAME=$(echo "$DB_URL_NO_SCHEME" | cut -d/ -f2)

    # Default port if not specified
    DB_PORT=${DB_PORT:-5432}

    # Check if psql is available
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}❌ Error: psql not found. Please install PostgreSQL client tools.${NC}"
        exit 1
    fi

    # Set password for psql
    export PGPASSWORD="$DB_PASS"

    # Check if backup is compressed
    if [[ $BACKUP_FILE == *.gz ]]; then
        echo "📂 Decompressing backup..."
        TEMP_FILE="${BACKUP_FILE%.gz}"
        gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
        RESTORE_FROM="$TEMP_FILE"
    else
        RESTORE_FROM="$BACKUP_FILE"
    fi

    # Drop and recreate database
    echo "🗑️  Dropping existing database..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS $DB_NAME;"

    echo "🏗️  Creating new database..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE $DB_NAME;"

    # Restore database
    echo "📥 Restoring database..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$RESTORE_FROM" > /dev/null

    # Clean up temp file if we decompressed
    if [[ $BACKUP_FILE == *.gz ]]; then
        rm -f "$TEMP_FILE"
    fi

    # Unset password
    unset PGPASSWORD

    echo -e "${GREEN}✅ PostgreSQL database restored successfully${NC}"

else
    echo -e "${RED}❌ Error: Unsupported database type: $DATABASE_URL${NC}"
    exit 1
fi

echo ""
echo "📋 Restore Summary:"
echo "   Restored from: $BACKUP_FILE"
echo "   Database: $DATABASE_URL"
echo ""
echo -e "${GREEN}✅ Restore process completed successfully!${NC}"
echo ""
echo "💡 Next steps:"
echo "   1. Verify the database: uv run sqlite_web $DB_FILE (for SQLite)"
echo "   2. Run any pending migrations: uv run alembic upgrade head"
echo "   3. Restart the application: uvicorn app.main:app --reload"
