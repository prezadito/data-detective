#!/bin/bash
# Database backup script for Data Detective Academy
#
# This script creates backups of the database with timestamps.
# Supports both SQLite (development) and PostgreSQL (production).
#
# Usage:
#   ./scripts/backup.sh [output_directory]
#
# Environment Variables:
#   DATABASE_URL - Database connection string (from .env)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  Warning: .env file not found. Using default DATABASE_URL.${NC}"
fi

# Default values
DATABASE_URL=${DATABASE_URL:-"sqlite:///./data_detective_academy.db"}
BACKUP_DIR=${1:-"./backups"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."
echo "   Database: $DATABASE_URL"
echo "   Backup directory: $BACKUP_DIR"
echo "   Timestamp: $TIMESTAMP"
echo ""

# Detect database type
if [[ $DATABASE_URL == sqlite:* ]]; then
    # SQLite backup
    echo "📦 Detected SQLite database"

    # Extract database file path from URL
    DB_FILE=$(echo "$DATABASE_URL" | sed 's|sqlite:///\./||' | sed 's|sqlite:///||')

    if [ ! -f "$DB_FILE" ]; then
        echo -e "${RED}❌ Error: Database file not found: $DB_FILE${NC}"
        exit 1
    fi

    BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.db"

    # Copy database file
    cp "$DB_FILE" "$BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"

    echo -e "${GREEN}✅ SQLite backup completed${NC}"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"

elif [[ $DATABASE_URL == postgresql:* ]] || [[ $DATABASE_URL == postgres:* ]]; then
    # PostgreSQL backup
    echo "📦 Detected PostgreSQL database"

    # Parse PostgreSQL connection string
    # Format: postgresql://user:password@host:port/dbname
    DB_URL_NO_SCHEME=$(echo "$DATABASE_URL" | sed 's|postgresql://||' | sed 's|postgres://||')

    # Extract components
    DB_USER=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f1)
    DB_PASS=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f2 | cut -d@ -f1)
    DB_HOST=$(echo "$DB_URL_NO_SCHEME" | cut -d@ -f2 | cut -d: -f1)
    DB_PORT=$(echo "$DB_URL_NO_SCHEME" | cut -d: -f3 | cut -d/ -f1)
    DB_NAME=$(echo "$DB_URL_NO_SCHEME" | cut -d/ -f2)

    # Default port if not specified
    DB_PORT=${DB_PORT:-5432}

    BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"

    # Set password for pg_dump
    export PGPASSWORD="$DB_PASS"

    # Create backup using pg_dump
    if command -v pg_dump &> /dev/null; then
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-acl \
            -f "$BACKUP_FILE"

        # Compress backup
        gzip "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE}.gz"

        echo -e "${GREEN}✅ PostgreSQL backup completed${NC}"
        echo "   File: $BACKUP_FILE"
        echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        echo -e "${RED}❌ Error: pg_dump not found. Please install PostgreSQL client tools.${NC}"
        exit 1
    fi

    # Unset password
    unset PGPASSWORD

else
    echo -e "${RED}❌ Error: Unsupported database type: $DATABASE_URL${NC}"
    exit 1
fi

echo ""
echo "📋 Backup Summary:"
echo "   Location: $BACKUP_FILE"
echo "   Timestamp: $TIMESTAMP"
echo ""
echo "💡 To restore this backup, run:"
echo "   ./scripts/restore.sh $BACKUP_FILE"
echo ""

# Keep only last 10 backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.gz" | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo "🧹 Cleaning up old backups (keeping last 10)..."
    find "$BACKUP_DIR" -name "backup_*.gz" -type f -printf '%T+ %p\n' | \
        sort -r | tail -n +11 | cut -d' ' -f2- | xargs rm -f
    echo "   Old backups removed"
fi

echo -e "${GREEN}✅ Backup process completed successfully!${NC}"
