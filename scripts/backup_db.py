"""
NoteIQ Database Daily Backup & Retention Script.
Takes PostgreSQL pg_dump snapshot, compresses it, and purges backups older than RETENTION_DAYS.
"""

import os
import subprocess
import sys
from datetime import datetime, timezone

RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))
BACKUP_DIR = os.environ.get("BACKUP_DIR", "./backups")


def run_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"noteiq_db_{timestamp}.sql.gz")

    db_url = os.environ.get("DATABASE_URL", "")
    print(f"[BACKUP] Starting automated backup at {timestamp}...")

    # Run pg_dump piped through gzip
    cmd = f"pg_dump {db_url} | gzip > {backup_file}"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[SUCCESS] Database snapshot written to: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] pg_dump failed: {e}", file=sys.stderr)
        return

    # Enforce retention policy
    now = datetime.now(timezone.utc).timestamp()
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        if os.path.isfile(fpath) and fname.startswith("noteiq_db_"):
            mtime = os.path.getmtime(fpath)
            age_days = (now - mtime) / 86400.0
            if age_days > RETENTION_DAYS:
                os.remove(fpath)
                print(f"[PURGED] Expired backup removed: {fname} ({age_days:.1f} days old)")


if __name__ == "__main__":
    run_backup()
