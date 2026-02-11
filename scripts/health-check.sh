#!/bin/bash
set -e

echo "Checking Postgres..."
# Check postgres container health
docker compose exec postgres pg_isready -U postgres || { echo "❌ Postgres check failed"; exit 1; }
echo "✅ Postgres is ready"

echo "Checking Redis..."
docker compose exec redis redis-cli ping | grep PONG > /dev/null || { echo "❌ Redis check failed"; exit 1; }
echo "✅ Redis is ready"

echo "Checking LiveKit..."
# Check LiveKit HTTP endpoint
if command -v curl &> /dev/null; then
    curl -s http://localhost:7881/ > /dev/null || { echo "❌ LiveKit HTTP check failed"; exit 1; }
elif command -v wget &> /dev/null; then
    wget -qO- http://localhost:7881/ > /dev/null || { echo "❌ LiveKit HTTP check failed"; exit 1; }
else
    echo "⚠️ curl and wget not found on host, assuming LiveKit is okay if container is running."
fi
echo "✅ LiveKit is ready (http://localhost:7881)"

echo "🎉 All services healthy!"
