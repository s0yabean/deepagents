# Checkpoint Cleanup & Monitoring Guide

## Overview

Your TikTok Slideshow Agent creates many checkpoints during long-running jobs (10-20 minutes). This guide explains how to manage checkpoint accumulation and prevent database overload.

---

## Current Situation

- **Jobs**: 10-20 minute execution time with heavy tool usage
- **Checkpoints per job**: 150-313 checkpoints (observed)
- **Current TTL**: 2 weeks (20,160 minutes)
- **Impact**: Old threads and checkpoints accumulate, consuming database resources

---

## How LangGraph Handles Cleanup

### Automatic TTL-Based Cleanup

LangGraph has a built-in **TTL sweeper** that runs every 5 minutes:

1. Checks `thread_ttl` table for expired threads
2. Deletes expired threads
3. **Cascades deletes** to all related data:
   - Checkpoints
   - Checkpoint blobs
   - Checkpoint writes
   - Thread TTL entries

**You don't need to manually delete checkpoints** - they're automatically cleaned up when their parent thread expires.

### TTL Sweeper Logs

You can monitor the sweeper in your logs:
```bash
docker compose -f docker-compose.prod.yml logs langgraph-api | grep -i "sweep"
```

Look for:
- `Starting thread TTL sweeper` - Sweeper is running
- `Sweep runs: no runs with status='running'` - Health check

---

## Recommended: Reduce TTL to 1 Hour

### Why Reduce TTL?

**Current: 2 weeks (20,160 minutes)**
- Old completed jobs sit in DB for 14 days
- Accumulates ~1,000 checkpoints even with low usage
- Wastes database space and connection pool resources

**Recommended: 1 hour (60 minutes)**
- Jobs complete in 10-20 minutes
- 1 hour gives buffer for human review/debugging
- Auto-cleanup happens quickly after job completion

### How to Change TTL

The TTL is set **per-thread** when creating the thread via API. Update your API requests:

#### Before (2 weeks):
```bash
curl -X POST https://tt-ss-agent.elish.ai/threads \
  -H "Authorization: Basic YWRtaW46bWluZHJlYWRlcg==" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {},
    "if_exists": "raise",
    "ttl": {
      "strategy": "delete",
      "ttl": 20160
    }
  }'
```

#### After (1 hour):
```bash
curl -X POST https://tt-ss-agent.elish.ai/threads \
  -H "Authorization: Basic YWRtaW46bWluZHJlYWRlcg==" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {},
    "if_exists": "raise",
    "ttl": {
      "strategy": "delete",
      "ttl": 60
    }
  }'
```

**Just change `"ttl": 20160` to `"ttl": 60"`**

### Alternative: Set Default in Environment

You can set a default TTL in your LangGraph configuration (coming in future LangGraph releases), but for now, the TTL must be specified per-request.

---

## Monitoring Database Health

### 1. Use the Monitoring Script

Run the provided monitoring script:

```bash
cd /root/services/deepagents/tiktok_slideshow_agent
python monitor_db.py
```

This shows:
- Total checkpoints and size
- Active threads
- Expired threads waiting for cleanup
- Database connection pool usage
- Threads with excessive checkpoints (>200)

### 2. Set Up Cron for Regular Monitoring

Monitor every hour:
```bash
# Edit crontab
crontab -e

# Add this line:
0 * * * * cd /root/services/deepagents/tiktok_slideshow_agent && python monitor_db.py >> /var/log/langgraph_monitor.log 2>&1
```

### 3. Manual Cleanup (if needed)

If the TTL sweeper falls behind:
```bash
# Dry run (see what would be deleted)
python monitor_db.py --cleanup --dry-run

# Actually delete expired threads
python monitor_db.py --cleanup
```

**Note**: This is rarely needed - LangGraph's sweeper is reliable.

---

## Connection Pool Monitoring

### Check Current Pool Status

```bash
docker compose -f docker-compose.prod.yml logs langgraph-api | grep "Postgres pool stats"
```

Look for:
- `pool_available`: Should be > 0
- `requests_waiting`: Should be 0 or very low
- `requests_wait_ms`: Should be < 1000ms

### Alert Thresholds

- ⚠️ **Warning**: `pool_available < 10` or `requests_waiting > 10`
- 🚨 **Critical**: `pool_available = 0` or `requests_waiting > 100`

### Current Configuration

```yaml
# docker-compose.prod.yml
max_connections: 200  # Increased from 100
```

This should handle ~10-15 concurrent long-running jobs.

---

## Checkpoint Optimization Strategies

### 1. Reduce Checkpoint Frequency (Advanced)

By default, LangGraph checkpoints after every node and tool call. For your use case:

```python
# In agent.py - Add checkpointer configuration
from langgraph.checkpoint.postgres import PostgresSaver

# Configure checkpointer with less aggressive checkpointing
# This requires modifying deepagents library or using custom checkpointer
```

**Note**: This is advanced and may affect recovery/debugging capabilities.

### 2. Monitor Heavy Threads

Check which jobs create excessive checkpoints:

```bash
python monitor_db.py
```

Look for "HEAVY THREADS" section. If a thread has >500 checkpoints, investigate:
- Is the agent stuck in a loop?
- Are tool calls being repeated unnecessarily?
- Is there a bug in the workflow?

### 3. Clean Up After Job Completion

For production systems, consider deleting threads immediately after successful completion:

```bash
# After job completes successfully
curl -X DELETE https://tt-ss-agent.elish.ai/threads/{thread_id} \
  -H "Authorization: Basic YWRtaW46bWluZHJlYWRlcg=="
```

This is cleaner than waiting for TTL expiration.

---

## Troubleshooting

### Sweeper Not Running

Check logs:
```bash
docker compose -f docker-compose.prod.yml logs langgraph-api | grep "thread TTL sweeper"
```

Should see: `Starting thread TTL sweeper`

### Too Many Expired Threads

If `monitor_db.py` shows many expired threads:
1. Check if sweeper is running (see above)
2. Manually trigger cleanup: `python monitor_db.py --cleanup`
3. Restart API service: `docker compose -f docker-compose.prod.yml restart langgraph-api`

### Database Growing Too Large

```sql
-- Check database size
docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

-- Check table sizes
docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -c "
  SELECT schemaname, relname, pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS size
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC;
"
```

If `checkpoint_blobs` is huge (>100MB), reduce TTL to 1 hour.

---

## Summary: Action Items

1. **✅ Immediate**: Change TTL from 20,160 to 60 in your API requests
2. **✅ Recommended**: Set up cron monitoring with `monitor_db.py`
3. **✅ Optional**: Delete threads immediately after job completion
4. **✅ Monitor**: Watch connection pool stats in logs

With 1-hour TTL, your database should stay healthy with automatic cleanup happening ~50 minutes after each job completes.
