# RAG Stack - Docker Compose Setup

Complete retrieval-augmented generation stack with persistent volumes and healthchecks.

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Qdrant** | 6333-6334 | Vector database for semantic search |
| **Chroma** | 8000 | Alternative vector database |
| **SearXNG** | 8888 | Self-hosted meta-search engine |
| **Open WebUI** | 8081 | ChatGPT-style UI for Ollama |

## Quick Start

```bash
cd ~/rag-stack

# Start all services
./rag-stack.sh start

# Check status
./rag-stack.sh status

# View logs
./rag-stack.sh logs

# Health check
./rag-stack.sh health

# Stop all services
./rag-stack.sh stop

# Remove volumes
./rag-stack.sh clean
```

## Configuration

Edit `.env` to customize:
- `QDRANT_API_KEY` — Optional API key for Qdrant
- `SEARXNG_BASE_URL` — SearXNG instance URL
- `OLLAMA_BASE_URL` — Ollama endpoint (default: `http://host.docker.internal:11434`)

## Usage

### Qdrant (Vector Search)
```python
from qdrant_client import QdrantClient

client = QdrantClient("http://localhost:6333")
collections = client.get_collections()
```

### Chroma (Vector Store)
```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_or_create_collection("documents")
```

### SearXNG (Meta-Search)
Open http://localhost:8888 in your browser.

### Open WebUI (Chat)
Open http://localhost:8081 in your browser.

## Volumes

All data persists in Docker volumes:
- `qdrant_storage` — Qdrant index data
- `chroma_data` — Chroma embeddings
- `searxng_data` — SearXNG configuration
- `open_webui_data` — WebUI history and settings

## Healthchecks

Each service includes a healthcheck:
- Qdrant: `GET /health`
- Chroma: `GET /api/v2`
- SearXNG: `GET /info`
- Open WebUI: `GET /api/v1/auth/test`

Monitor with: `./rag-stack.sh health`

## Network

Services communicate on the `rag-stack` bridge network. Open WebUI waits for Qdrant to be healthy before starting.

## Troubleshooting

**Service won't start:**
```bash
docker logs qdrant  # or chroma, searxng, open-webui-rag
```

**Port conflicts:**
Edit `docker-compose.yml` to use different ports.

**Reset everything:**
```bash
./rag-stack.sh clean
./rag-stack.sh start
```
