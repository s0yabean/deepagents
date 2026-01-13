#!/bin/bash
# Verify postgres password is correctly set after deployment

echo "Verifying postgres authentication..."

# Wait for postgres to be ready
sleep 5

# Test connection from API container
if docker exec tiktok_slideshow_agent-langgraph-api-1 python -c "
import psycopg
try:
    conn = psycopg.connect('postgres://postgres:postgres@langgraph-postgres:5432/postgres')
    conn.close()
    print('✅ Postgres authentication working')
    exit(0)
except Exception as e:
    print(f'❌ Postgres authentication failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo "All good!"
else
    echo "⚠️  Authentication issue detected. Resetting password..."
    docker exec tiktok_slideshow_agent-langgraph-postgres-1 psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
    echo "Password reset. Restarting API..."
    docker compose -f docker-compose.prod.yml restart langgraph-api
fi
