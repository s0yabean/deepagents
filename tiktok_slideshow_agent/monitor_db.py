#!/usr/bin/env python3
"""
Database and Connection Pool Monitoring Script for LangGraph
Run this periodically (e.g., via cron) to monitor database health
"""

import os
import sys
import subprocess
import json
from datetime import datetime

# Docker container name
CONTAINER_NAME = "tiktok_slideshow_agent-langgraph-postgres-1"

# Alert thresholds
CHECKPOINT_WARNING_THRESHOLD = 1000  # Warn if total checkpoints exceed this
THREAD_WARNING_THRESHOLD = 50  # Warn if active threads exceed this
CHECKPOINT_PER_THREAD_WARNING = 200  # Warn if any thread has more than this many checkpoints

def run_query(query):
    """Execute SQL query via docker exec"""
    cmd = [
        "docker", "exec", CONTAINER_NAME,
        "psql", "-U", "postgres", "-t", "-c", query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Query failed: {result.stderr}")
    return result.stdout.strip()

def get_db_stats():
    """Fetch database statistics"""

    stats = {}

    # 1. Total checkpoints and size
    result = run_query("""
        SELECT COUNT(*) || '|' || pg_size_pretty(SUM(pg_column_size(checkpoint)))
        FROM checkpoints;
    """)
    parts = result.split('|')
    stats['total_checkpoints'] = int(parts[0].strip())
    stats['checkpoints_size'] = parts[1].strip()

    # 2. Total checkpoint blobs and size
    result = run_query("""
        SELECT COUNT(*) || '|' || pg_size_pretty(SUM(octet_length(blob)))
        FROM checkpoint_blobs;
    """)
    parts = result.split('|')
    stats['blob_count'] = int(parts[0].strip())
    stats['blob_size'] = parts[1].strip()

    # 3. Active threads
    result = run_query("SELECT COUNT(*) FROM thread;")
    stats['active_threads'] = int(result.strip())

    # 4. Threads with excessive checkpoints
    result = run_query(f"""
        SELECT thread_id || '|' || COUNT(*)
        FROM checkpoints
        GROUP BY thread_id
        HAVING COUNT(*) > {CHECKPOINT_PER_THREAD_WARNING}
        ORDER BY COUNT(*) DESC;
    """)
    stats['heavy_threads'] = []
    if result:
        for line in result.split('\n'):
            if line.strip():
                parts = line.strip().split('|')
                stats['heavy_threads'].append((parts[0].strip(), int(parts[1].strip())))

    # 5. Expired threads waiting for cleanup
    result = run_query("""
        SELECT COUNT(*)
        FROM thread_ttl
        WHERE expires_at < NOW();
    """)
    stats['expired_threads'] = int(result.strip())

    # 6. Database size
    result = run_query("SELECT pg_size_pretty(pg_database_size(current_database()));")
    stats['db_size'] = result.strip()

    # 7. Connection stats (current connections)
    result = run_query("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();")
    stats['active_connections'] = int(result.strip())

    # 8. Max connections setting
    result = run_query("SHOW max_connections;")
    stats['max_connections'] = int(result.strip())

    return stats

def print_report(stats):
    """Print formatted monitoring report"""
    print(f"\n{'='*60}")
    print(f"LangGraph Database Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Database overview
    print("📊 DATABASE OVERVIEW")
    print(f"  Total Size: {stats['db_size']}")
    print(f"  Active Connections: {stats['active_connections']}/{stats['max_connections']}")

    connection_pct = (stats['active_connections'] / stats['max_connections']) * 100
    if connection_pct > 80:
        print(f"  ⚠️  WARNING: Connection pool at {connection_pct:.1f}% capacity!")

    # Checkpoint stats
    print(f"\n💾 CHECKPOINT STATS")
    print(f"  Total Checkpoints: {stats['total_checkpoints']}")
    print(f"  Checkpoints Size: {stats['checkpoints_size']}")
    print(f"  Checkpoint Blobs: {stats['blob_count']}")
    print(f"  Blobs Size: {stats['blob_size']}")

    if stats['total_checkpoints'] > CHECKPOINT_WARNING_THRESHOLD:
        print(f"  ⚠️  WARNING: High checkpoint count ({stats['total_checkpoints']} > {CHECKPOINT_WARNING_THRESHOLD})")

    # Thread stats
    print(f"\n🧵 THREAD STATS")
    print(f"  Active Threads: {stats['active_threads']}")
    print(f"  Expired (pending cleanup): {stats['expired_threads']}")

    if stats['active_threads'] > THREAD_WARNING_THRESHOLD:
        print(f"  ⚠️  WARNING: High thread count ({stats['active_threads']} > {THREAD_WARNING_THRESHOLD})")

    if stats['expired_threads'] > 0:
        print(f"  ℹ️  INFO: {stats['expired_threads']} expired threads waiting for TTL sweeper")

    # Heavy threads
    if stats['heavy_threads']:
        print(f"\n⚠️  HEAVY THREADS (>{CHECKPOINT_PER_THREAD_WARNING} checkpoints)")
        for thread_id, count in stats['heavy_threads']:
            print(f"  {thread_id}: {count} checkpoints")

    print(f"\n{'='*60}\n")

def cleanup_old_data(dry_run=True):
    """
    Optional: Manually trigger cleanup of old checkpoints

    NOTE: LangGraph's TTL sweeper should handle this automatically,
    but this function can be used for manual cleanup if needed.
    """
    # Find threads that have expired
    result = run_query("""
        SELECT t.thread_id
        FROM thread t
        JOIN thread_ttl tt ON t.thread_id = tt.thread_id
        WHERE tt.expires_at < NOW();
    """)

    expired_threads = []
    if result:
        expired_threads = [line.strip() for line in result.split('\n') if line.strip()]

    if dry_run:
        print(f"\n🧹 DRY RUN: Would delete {len(expired_threads)} expired threads and their checkpoints")
        if expired_threads:
            print("Thread IDs:")
            for thread_id in expired_threads[:10]:  # Show first 10
                print(f"  - {thread_id}")
            if len(expired_threads) > 10:
                print(f"  ... and {len(expired_threads) - 10} more")
    else:
        print(f"\n🧹 Deleting {len(expired_threads)} expired threads...")
        for thread_id in expired_threads:
            run_query(f"DELETE FROM thread WHERE thread_id = '{thread_id}';")
        print("✅ Cleanup complete")

if __name__ == "__main__":
    try:
        stats = get_db_stats()
        print_report(stats)

        # Optional: Add cleanup command
        if "--cleanup" in sys.argv:
            cleanup_old_data(dry_run="--dry-run" in sys.argv)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
