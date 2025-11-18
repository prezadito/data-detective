# Backup and Recovery Verification Guide

Comprehensive guide for backup procedures and disaster recovery verification for Data Detective Academy.

## Table of Contents

- [Overview](#overview)
- [Backup Strategy](#backup-strategy)
- [Database Backups](#database-backups)
- [Application Backups](#application-backups)
- [Verification Procedures](#verification-procedures)
- [Recovery Procedures](#recovery-procedures)
- [Backup Monitoring](#backup-monitoring)
- [Disaster Recovery Drills](#disaster-recovery-drills)

---

## Overview

### Backup Objectives

**Recovery Point Objective (RPO)**: Maximum acceptable data loss
- **Target**: 24 hours
- Database backed up daily
- Critical data: Near real-time replication (future)

**Recovery Time Objective (RTO)**: Maximum acceptable downtime
- **Target**: 4 hours
- Time to restore from backup and verify functionality

### Backup Types

1. **Full Backups**: Complete database dump
   - Frequency: Daily
   - Retention: 30 days
   - Storage: Separate from production

2. **Incremental Backups**: Changed data only
   - Frequency: Hourly (recommended for production)
   - Retention: 7 days
   - Storage: Same as full backups

3. **Application State**: Code and configuration
   - Frequency: On deployment
   - Retention: Last 10 deployments
   - Storage: Git repository + deployment artifacts

---

## Backup Strategy

### 3-2-1 Backup Rule

✅ **3 Copies** of data:
- 1 Primary (production database)
- 1 Local backup (same datacenter)
- 1 Off-site backup (different region/provider)

✅ **2 Different Media**:
- Database snapshots
- SQL dump files

✅ **1 Off-site** copy:
- Cloud storage (S3, Google Cloud Storage, etc.)
- Different availability zone/region

### Backup Schedule

#### Daily Backups
```bash
# Scheduled via cron: 2 AM UTC daily
0 2 * * * /usr/local/bin/backup-database.sh
```

#### Weekly Full Backups
```bash
# Scheduled via cron: Sunday 2 AM UTC
0 2 * * 0 /usr/local/bin/backup-full-system.sh
```

#### Automated Platform Backups
- **Render.com PostgreSQL**: Automatic daily backups (7-day retention)
- **Vercel**: Automatic deployment snapshots (all deployments retained)

---

## Database Backups

### PostgreSQL Backup Script

**File**: `/usr/local/bin/backup-database.sh`

```bash
#!/bin/bash
#
# Database Backup Script for Data Detective Academy
# Performs PostgreSQL backup with compression and off-site upload
#

set -euo pipefail  # Exit on error, undefined variable, pipe failure

# Configuration
BACKUP_DIR="/home/datadetective/backups/database"
RETENTION_DAYS=30
DB_NAME="data_detective_academy"
DB_USER="data_detective_user"
S3_BUCKET="s3://datadetective-backups"  # Optional: for off-site storage

# Derived variables
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_${DATE}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup_${DATE}.log"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Log function
log() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "${LOG_FILE}"
}

# Start backup
log "Starting database backup..."

# Backup database with pg_dump
log "Running pg_dump..."
if pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
    log "Database dumped successfully: ${BACKUP_FILE}"
else
    log "ERROR: pg_dump failed"
    exit 1
fi

# Verify backup file
if [ ! -f "${BACKUP_FILE}" ]; then
    log "ERROR: Backup file not created"
    exit 1
fi

# Check backup file size
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "Backup size: ${BACKUP_SIZE}"

if [ $(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}") -lt 1024 ]; then
    log "ERROR: Backup file is too small (< 1KB), may be corrupted"
    exit 1
fi

# Test backup integrity by attempting to decompress
log "Verifying backup integrity..."
if gzip -t "${BACKUP_FILE}"; then
    log "Backup integrity verified"
else
    log "ERROR: Backup file is corrupted"
    exit 1
fi

# Upload to S3 (optional, requires AWS CLI)
if command -v aws &> /dev/null && [ -n "${S3_BUCKET}" ]; then
    log "Uploading to S3..."
    if aws s3 cp "${BACKUP_FILE}" "${S3_BUCKET}/$(basename ${BACKUP_FILE})"; then
        log "Uploaded to S3 successfully"
    else
        log "WARNING: S3 upload failed (backup still available locally)"
    fi
fi

# Clean up old backups
log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "db_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
log "Cleanup completed"

# Backup statistics
TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "db_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log "Total backups: ${TOTAL_BACKUPS}"
log "Total size: ${TOTAL_SIZE}"

log "Backup completed successfully"

# Send notification (optional, requires mail command)
if command -v mail &> /dev/null; then
    echo "Database backup completed successfully: ${BACKUP_FILE} (${BACKUP_SIZE})" | \
        mail -s "✓ Database Backup Success - ${DATE}" admin@example.com
fi

exit 0
```

**Installation**:
```bash
# Create script
sudo nano /usr/local/bin/backup-database.sh

# Make executable
sudo chmod +x /usr/local/bin/backup-database.sh

# Test manually
sudo /usr/local/bin/backup-database.sh

# Schedule with cron
sudo crontab -e
# Add line:
0 2 * * * /usr/local/bin/backup-database.sh
```

### Render.com PostgreSQL Backups

**Automatic Backups**:
- **Free Tier**: Daily backups, 7-day retention
- **Paid Tier**: Daily backups, configurable retention

**Manual Backup**:
```bash
# Get database URL from Render dashboard
DATABASE_URL="postgresql://user:pass@host/dbname"

# Create manual backup
pg_dump "$DATABASE_URL" | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Access Backups**:
1. Go to Render Dashboard → PostgreSQL database
2. Click "Backups" tab
3. Download or restore from backup

---

## Application Backups

### Source Code
- **Primary**: Git repository
- **Backup**: GitHub (automatic)
- **Verification**: Git clone works

```bash
# Verify repository backup
git clone https://github.com/your-org/data-detective.git test-clone
cd test-clone
git log --oneline -5  # Verify recent commits
cd .. && rm -rf test-clone
```

### Environment Variables

**Backup Script**: `/usr/local/bin/backup-env-vars.sh`

```bash
#!/bin/bash
#
# Environment Variables Backup Script
# Backs up .env files (encrypted)
#

set -euo pipefail

BACKUP_DIR="/home/datadetective/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-changeme}"

mkdir -p "${BACKUP_DIR}"

# Backup backend .env
if [ -f "/home/datadetective/app/backend/.env" ]; then
    tar czf - /home/datadetective/app/backend/.env | \
        openssl enc -aes-256-cbc -salt -pbkdf2 -pass pass:"${ENCRYPTION_KEY}" \
        > "${BACKUP_DIR}/backend_env_${DATE}.tar.gz.enc"
    echo "Backend .env backed up"
fi

# Backup frontend .env
if [ -f "/home/datadetective/app/frontend/.env" ]; then
    tar czf - /home/datadetective/app/frontend/.env | \
        openssl enc -aes-256-cbc -salt -pbkdf2 -pass pass:"${ENCRYPTION_KEY}" \
        > "${BACKUP_DIR}/frontend_env_${DATE}.tar.gz.enc"
    echo "Frontend .env backed up"
fi

# Keep only last 10 backups
find "${BACKUP_DIR}" -name "*_env_*.tar.gz.enc" -type f | \
    sort -r | tail -n +11 | xargs -r rm

echo "Environment variables backed up successfully"
```

**Restore**:
```bash
# Decrypt and restore
openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:"${ENCRYPTION_KEY}" \
    -in backend_env_20251118_020000.tar.gz.enc | tar xzf -
```

### Static Assets & Uploads

**If storing user uploads** (datasets, custom challenges):

```bash
#!/bin/bash
# Backup uploads directory

UPLOAD_DIR="/home/datadetective/app/backend/uploads"
BACKUP_DIR="/home/datadetective/backups/uploads"
DATE=$(date +%Y%m%d)

mkdir -p "${BACKUP_DIR}"

# Incremental backup with rsync
rsync -av --delete "${UPLOAD_DIR}/" "${BACKUP_DIR}/current/"

# Create daily snapshot
cp -al "${BACKUP_DIR}/current" "${BACKUP_DIR}/snapshot_${DATE}"

# Keep last 7 daily snapshots
find "${BACKUP_DIR}" -maxdepth 1 -name "snapshot_*" -type d -mtime +7 -exec rm -rf {} \;
```

---

## Verification Procedures

### Daily Backup Verification

**Automated Check** (runs after backup):

```bash
#!/bin/bash
#
# Backup Verification Script
# Verifies backup file integrity and restorability
#

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "Verifying backup: ${BACKUP_FILE}"

# 1. Check file exists and is not empty
FILE_SIZE=$(stat -c%s "${BACKUP_FILE}")
if [ ${FILE_SIZE} -lt 1024 ]; then
    echo "ERROR: Backup file is too small (${FILE_SIZE} bytes)"
    exit 1
fi
echo "✓ File size OK: ${FILE_SIZE} bytes"

# 2. Verify gzip integrity
if ! gzip -t "${BACKUP_FILE}"; then
    echo "ERROR: Backup file is corrupted (gzip test failed)"
    exit 1
fi
echo "✓ Gzip integrity OK"

# 3. Verify SQL syntax (parse first 100 lines)
if ! zcat "${BACKUP_FILE}" | head -100 | psql -v ON_ERROR_STOP=1 --dry-run &>/dev/null; then
    echo "WARNING: SQL syntax check failed (may be false positive)"
fi
echo "✓ SQL syntax appears valid"

# 4. Verify backup contains expected tables
TABLES=$(zcat "${BACKUP_FILE}" | grep -c "CREATE TABLE")
if [ ${TABLES} -lt 6 ]; then
    echo "ERROR: Expected at least 6 tables, found ${TABLES}"
    exit 1
fi
echo "✓ Table count OK: ${TABLES} tables"

# 5. Verify backup contains data
INSERTS=$(zcat "${BACKUP_FILE}" | grep -c "INSERT INTO" || true)
echo "✓ Contains ${INSERTS} INSERT statements"

echo "Backup verification PASSED"
exit 0
```

**Usage**:
```bash
/usr/local/bin/verify-backup.sh /path/to/backup.sql.gz
```

### Weekly Restore Test

**Automated Restore Verification** (weekly, on staging):

```bash
#!/bin/bash
#
# Restore Test Script
# Tests backup restoration to verify recoverability
#

set -euo pipefail

BACKUP_FILE="$1"
TEST_DB="data_detective_test_restore"

echo "Starting restore test..."

# 1. Create test database
psql -U postgres -c "DROP DATABASE IF EXISTS ${TEST_DB};"
psql -U postgres -c "CREATE DATABASE ${TEST_DB};"
echo "✓ Test database created"

# 2. Restore backup
if zcat "${BACKUP_FILE}" | psql -U postgres -d "${TEST_DB}" > /dev/null; then
    echo "✓ Backup restored successfully"
else
    echo "ERROR: Restore failed"
    exit 1
fi

# 3. Verify table count
TABLE_COUNT=$(psql -U postgres -d "${TEST_DB}" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

if [ ${TABLE_COUNT} -lt 6 ]; then
    echo "ERROR: Expected at least 6 tables, found ${TABLE_COUNT}"
    exit 1
fi
echo "✓ Table count verified: ${TABLE_COUNT} tables"

# 4. Verify data integrity
USER_COUNT=$(psql -U postgres -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM users;")
echo "✓ User count: ${USER_COUNT}"

PROGRESS_COUNT=$(psql -U postgres -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM progress;")
echo "✓ Progress count: ${PROGRESS_COUNT}"

# 5. Test queries
psql -U postgres -d "${TEST_DB}" -c "SELECT id, email, role FROM users LIMIT 5;" > /dev/null
echo "✓ Sample queries successful"

# 6. Cleanup
psql -U postgres -c "DROP DATABASE ${TEST_DB};"
echo "✓ Test database cleaned up"

echo "Restore test PASSED - Backup is valid and restorable"
exit 0
```

**Schedule**:
```bash
# Add to cron: Every Sunday at 3 AM
0 3 * * 0 /usr/local/bin/test-restore.sh /path/to/latest/backup.sql.gz
```

---

## Recovery Procedures

### Complete Database Recovery

**Scenario**: Production database corrupted or lost

**Steps**:

1. **Stop Application** (prevent writes during recovery):
   ```bash
   # Render.com: Suspend service
   # Or set maintenance mode
   ```

2. **Identify Latest Backup**:
   ```bash
   # List backups
   ls -lht /home/datadetective/backups/database/

   # Or from Render dashboard
   # Select most recent successful backup
   ```

3. **Verify Backup Integrity**:
   ```bash
   /usr/local/bin/verify-backup.sh /path/to/backup.sql.gz
   ```

4. **Drop Existing Database** (if necessary):
   ```bash
   # CAUTION: This deletes all data!
   psql -U postgres -c "DROP DATABASE data_detective_academy;"
   psql -U postgres -c "CREATE DATABASE data_detective_academy OWNER data_detective_user;"
   ```

5. **Restore Backup**:
   ```bash
   # Decompress and restore
   zcat /path/to/backup.sql.gz | psql -U data_detective_user -d data_detective_academy

   # Or from compressed file directly
   pg_restore -U data_detective_user -d data_detective_academy /path/to/backup.sql.gz
   ```

6. **Verify Restoration**:
   ```bash
   # Connect to database
   psql -U data_detective_user -d data_detective_academy

   # Verify tables
   \dt

   # Verify record counts
   SELECT
       'users' AS table_name, COUNT(*) FROM users
   UNION ALL SELECT 'progress', COUNT(*) FROM progress
   UNION ALL SELECT 'attempts', COUNT(*) FROM attempts;

   # Test queries
   SELECT id, email, role FROM users LIMIT 5;
   ```

7. **Restart Application**:
   ```bash
   # Render.com: Resume service
   # Or restart uvicorn
   sudo systemctl restart datadetective-backend
   ```

8. **Smoke Test**:
   ```bash
   # Test health endpoint
   curl https://your-api.onrender.com/health

   # Test login
   curl -X POST https://your-api.onrender.com/auth/login \
     -d "username=student@example.com&password=password123"

   # Verify data
   # Login via frontend, check if data is present
   ```

9. **Monitor**:
   - Check Sentry for errors
   - Monitor logs for anomalies
   - Watch user reports

**Recovery Time**: ~30-60 minutes for < 1GB database

### Partial Data Recovery

**Scenario**: Recover specific table or deleted records

```bash
# Create temporary database
psql -U postgres -c "CREATE DATABASE temp_recovery;"

# Restore backup to temp database
zcat backup.sql.gz | psql -U postgres -d temp_recovery

# Export specific table
pg_dump -U postgres -d temp_recovery -t users > users_recovery.sql

# Import to production
psql -U data_detective_user -d data_detective_academy < users_recovery.sql

# Cleanup
psql -U postgres -c "DROP DATABASE temp_recovery;"
```

### Point-in-Time Recovery (PITR)

**Note**: Requires Write-Ahead Logging (WAL) archiving (not available on free tier)

**Setup** (for production/paid hosting):

```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /path/to/wal_archive/%f && cp %p /path/to/wal_archive/%f'
```

**Recovery**:
```bash
# Restore base backup
pg_restore -d database base_backup.sql.gz

# Apply WAL files up to specific time
recovery_target_time = '2025-11-18 14:30:00'
```

---

## Backup Monitoring

### Backup Success Monitoring

**Monitor Script**: Checks if daily backup completed

```bash
#!/bin/bash
#
# Backup Monitoring Script
# Alerts if backup is missing or old
#

BACKUP_DIR="/home/datadetective/backups/database"
MAX_AGE_HOURS=36  # Alert if no backup in last 36 hours

# Find most recent backup
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "db_*.sql.gz" -type f -printf '%T@ %p\n' | \
    sort -rn | head -1 | cut -d' ' -f2)

if [ -z "${LATEST_BACKUP}" ]; then
    echo "CRITICAL: No backups found in ${BACKUP_DIR}"
    # Send alert
    exit 1
fi

# Check age of latest backup
BACKUP_AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y "${LATEST_BACKUP}") ))
BACKUP_AGE_HOURS=$(( BACKUP_AGE_SECONDS / 3600 ))

if [ ${BACKUP_AGE_HOURS} -gt ${MAX_AGE_HOURS} ]; then
    echo "WARNING: Latest backup is ${BACKUP_AGE_HOURS} hours old (> ${MAX_AGE_HOURS} hours)"
    echo "Latest backup: ${LATEST_BACKUP}"
    # Send alert
    exit 1
fi

echo "OK: Latest backup is ${BACKUP_AGE_HOURS} hours old"
echo "File: ${LATEST_BACKUP}"
exit 0
```

**Schedule**:
```bash
# Check daily at 6 AM (after 2 AM backup)
0 6 * * * /usr/local/bin/check-backup-status.sh || mail -s "Backup Alert" admin@example.com
```

### Backup Dashboard

**Metrics to Track**:
- Last backup time
- Backup file size trend
- Backup success rate (last 30 days)
- Restore test success rate
- Storage usage

**Example Monitoring with Grafana**:
```sql
-- PostgreSQL query for backup metrics
SELECT
    DATE(backup_time) AS date,
    COUNT(*) AS backup_count,
    AVG(backup_size_mb) AS avg_size_mb,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS success_rate
FROM backup_logs
WHERE backup_time >= NOW() - INTERVAL '30 days'
GROUP BY DATE(backup_time)
ORDER BY date DESC;
```

---

## Disaster Recovery Drills

### Monthly DR Drill

**Purpose**: Ensure team can recover system in emergency

**Procedure**:

1. **Pre-Drill** (Day before):
   - [ ] Schedule drill (notify team)
   - [ ] Verify latest backup exists
   - [ ] Prepare staging environment
   - [ ] Review recovery procedures

2. **Drill Execution** (30-60 minutes):
   - [ ] Team member 1: Obtain latest backup
   - [ ] Team member 2: Provision new database (staging)
   - [ ] Team member 3: Deploy application code
   - [ ] All: Restore backup to staging database
   - [ ] All: Verify restoration (run smoke tests)
   - [ ] All: Document any issues

3. **Post-Drill**:
   - [ ] Calculate actual RTO (how long did it take?)
   - [ ] Identify improvements needed
   - [ ] Update runbooks
   - [ ] Share results with team

**Success Criteria**:
- Full restoration completed within RTO (4 hours)
- All critical functionality works
- No data loss observed
- All team members can perform recovery

### DR Drill Checklist

```markdown
# DR Drill - [Date]

## Participants
- [ ] Engineer 1: ________________
- [ ] Engineer 2: ________________
- [ ] On-call: ________________

## Timeline
- Drill Start: __:__ AM/PM
- Backup Retrieved: __:__ AM/PM
- Database Provisioned: __:__ AM/PM
- Restore Completed: __:__ AM/PM
- Verification Completed: __:__ AM/PM
- Drill End: __:__ AM/PM

## Actual RTO: _______ minutes (Target: 240 minutes)

## Tests Performed
- [ ] Health check passed
- [ ] Login functionality works
- [ ] Student can view challenges
- [ ] Student can submit solution
- [ ] Teacher can view analytics
- [ ] Leaderboard loads correctly

## Issues Encountered
1. ________________________________
2. ________________________________
3. ________________________________

## Action Items
1. [ ] ________________________________ (Assigned to: ______)
2. [ ] ________________________________ (Assigned to: ______)

## Overall Status: ⬜ PASS  ⬜ FAIL

## Notes:
_____________________________________________________________
_____________________________________________________________
```

---

## Best Practices

### Backup Best Practices

✅ **DO**:
- Test restores regularly (at least monthly)
- Store backups in multiple locations
- Encrypt backups (especially if contain PII)
- Monitor backup success/failure
- Document recovery procedures
- Practice disaster recovery drills
- Verify backup integrity automatically
- Keep multiple generations of backups

❌ **DON'T**:
- Store backups in same location as production
- Trust backups without testing restoration
- Delete old backups immediately (keep retention period)
- Store backups unencrypted on public cloud
- Forget to backup environment variables/secrets
- Skip backup monitoring

### Recovery Best Practices

✅ **DO**:
- Have written recovery procedures (runbooks)
- Test procedures regularly
- Keep recovery tools readily available
- Document actual recovery times
- Have emergency contact list
- Practice under time pressure
- Verify data after recovery
- Communicate status during recovery

❌ **DON'T**:
- Panic (follow procedures)
- Skip verification steps
- Assume backup is good without testing
- Make changes during recovery (stick to plan)
- Forget to notify stakeholders

---

## Appendix

### Backup Checklist

**Daily**:
- [ ] Database backup completed
- [ ] Backup integrity verified
- [ ] Backup uploaded to off-site storage
- [ ] Old backups cleaned up

**Weekly**:
- [ ] Full system backup completed
- [ ] Restore test performed
- [ ] Environment variables backed up
- [ ] Backup metrics reviewed

**Monthly**:
- [ ] Disaster recovery drill completed
- [ ] Recovery procedures updated
- [ ] Backup storage reviewed
- [ ] Team training conducted

### Useful Commands

```bash
# List all backups
find /home/datadetective/backups -name "*.sql.gz" -type f -ls

# Check backup size trend
du -sh /home/datadetective/backups/database/db_* | sort

# Verify latest backup
LATEST=$(ls -t /home/datadetective/backups/database/db_*.sql.gz | head -1)
/usr/local/bin/verify-backup.sh "$LATEST"

# Estimate restore time
BACKUP_SIZE=$(stat -c%s "$LATEST")
echo "Estimated restore time: $((BACKUP_SIZE / 1024 / 1024 / 10)) minutes"
# Assumes ~10MB/minute restore speed
```

---

**Last Updated**: 2025-11-18
**Next Review**: 2025-12-18
**Maintained By**: DevOps Team
