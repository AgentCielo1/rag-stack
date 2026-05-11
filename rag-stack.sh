#!/bin/bash

# RAG Stack Helper Script

set -e

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="rag-stack"

case "$1" in
  start)
    echo "🚀 Starting RAG stack..."
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    echo "✅ RAG stack started"
    echo ""
    echo "Services running:"
    echo "  - Qdrant: http://localhost:6333"
    echo "  - Chroma: http://localhost:8000"
    echo "  - SearXNG: http://localhost:8888"
    echo "  - Open WebUI: http://localhost:8081"
    ;;
  stop)
    echo "⏹️  Stopping RAG stack..."
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    echo "✅ RAG stack stopped"
    ;;
  status)
    echo "📊 RAG stack status:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    ;;
  logs)
    echo "📋 RAG stack logs:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f ${2:-}
    ;;
  health)
    echo "🏥 Checking health..."
    echo ""
    echo "Qdrant:"
    curl -s http://localhost:6333/health || echo "❌ Qdrant unavailable"
    echo ""
    echo "Chroma:"
    curl -s http://localhost:8000/api/v2 || echo "❌ Chroma unavailable"
    echo ""
    echo "SearXNG:"
    curl -s http://localhost:8888/info || echo "❌ SearXNG unavailable"
    ;;
  restart)
    echo "🔄 Restarting RAG stack..."
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart
    echo "✅ RAG stack restarted"
    ;;
  clean)
    echo "🧹 Cleaning up RAG stack..."
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v
    echo "✅ RAG stack cleaned (volumes removed)"
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs|health|restart|clean}"
    echo ""
    echo "Commands:"
    echo "  start   - Start all RAG services"
    echo "  stop    - Stop all services"
    echo "  status  - Show running status"
    echo "  logs    - Stream logs (optional: service name)"
    echo "  health  - Check service health"
    echo "  restart - Restart all services"
    echo "  clean   - Stop and remove volumes"
    exit 1
    ;;
esac
