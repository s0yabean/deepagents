#!/bin/bash
# Quick health check script for LangGraph database and connection pool

echo "=========================================="
echo "LangGraph Quick Health Check"
echo "=========================================="
echo ""

# 1. Container status
echo "📦 Container Status:"
docker ps --filter "name=langgraph" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep langgraph
echo ""

# 2. Resource usage
echo "💻 Resource Usage:"
docker stats --no-stream | grep langgraph | awk '{printf "  %-40s CPU: %6s  RAM: %12s\n", $2, $3, $4}'
echo ""

# 3. Database quick stats
echo "💾 Database Stats:"
docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -t -c "
  SELECT
    'Threads: ' || COUNT(*)
  FROM thread;
" 2>/dev/null | xargs echo "  "

docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -t -c "
  SELECT
    'Checkpoints: ' || COUNT(*)
  FROM checkpoints;
" 2>/dev/null | xargs echo "  "

docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -t -c "
  SELECT
    'DB Size: ' || pg_size_pretty(pg_database_size(current_database()));
" 2>/dev/null | xargs echo "  "

docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -t -c "
  SELECT
    'Connections: ' || count(*) || '/' || current_setting('max_connections')
  FROM pg_stat_activity
  WHERE datname = current_database();
" 2>/dev/null | xargs echo "  "
echo ""

# 4. Latest log entries
echo "📝 Recent API Logs:"
docker logs tiktok_slideshow_agent-langgraph-api-1 --tail 5 2>&1 | grep -E "(Postgres pool stats|POST|error|warning)" | tail -3
echo ""

# 5. Expired threads
echo "🧹 Cleanup Status:"
docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -t -c "
  SELECT
    'Expired threads: ' || COUNT(*)
  FROM thread_ttl
  WHERE expires_at < NOW();
" 2>/dev/null | xargs echo "  "
echo ""

echo "=========================================="
echo "Run 'python monitor_db.py' for detailed stats"
echo "=========================================="
