# RAG Pipeline: Firecrawl + Qdrant + LiteLLM

Complete end-to-end retrieval-augmented generation pipeline combining web scraping, vector search, and LLM generation.

## Setup

### 1. Install Dependencies

```bash
uv pip install --system firecrawl-py sentence-transformers litellm
```

### 2. Get API Keys

#### OpenAI API (for LLM generation)
```bash
export OPENAI_API_KEY="sk-..."
```
Get key at: https://platform.openai.com/api/keys

#### Firecrawl API (for web scraping - optional)
```bash
export FIRECRAWL_API_KEY="fc-..."
```
Get key at: https://firecrawl.dev

#### LiteLLM supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Ollama (local)
- DeepSeek, Mistral, etc.

See [LiteLLM docs](https://docs.litellm.ai/) for all supported models.

### 3. Ensure Services Running

```bash
cd ~/rag-stack
docker compose up -d qdrant chroma
./rag-stack.sh status
```

## Usage

### Basic Example

```python
from rag_pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline(llm_model="gpt-4")

# Add documents
docs = [
    {"title": "Docker", "content": "Docker is a containerization platform..."},
    {"title": "Kubernetes", "content": "Kubernetes orchestrates containers..."},
]
pipeline.add_documents(docs)

# Search
results = pipeline.search("What is Docker?", limit=5)
for doc in results:
    print(f"{doc['title']}: {doc['score']:.2f}")

# Generate response with RAG
answer = pipeline.generate("Explain Docker and Kubernetes")
print(answer)
```

### Scrape Website and Generate

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline(
    firecrawl_api_key="fc-...",
    llm_model="gpt-4"
)

# Scrape website
pipeline.scrape_and_store("https://docs.docker.com", limit=10)

# Query the knowledge base
answer = pipeline.generate("How do I create a Docker container?")
print(answer)
```

### Use Different LLM Models

```python
# OpenAI
pipeline = RAGPipeline(llm_model="gpt-4")

# Anthropic Claude
pipeline = RAGPipeline(llm_model="claude-3-opus-20240229")

# Ollama (local)
pipeline = RAGPipeline(llm_model="ollama/llama2")

# DeepSeek (via OpenRouter)
import os
os.environ["OPENROUTER_API_KEY"] = "sk-..."
pipeline = RAGPipeline(llm_model="openrouter/deepseek-chat")
```

## API Reference

### RAGPipeline Class

#### `__init__(firecrawl_api_key, qdrant_host, qdrant_port, collection_name, embedding_model, llm_model)`

Initialize the RAG pipeline.

**Parameters:**
- `firecrawl_api_key` (str, optional): Firecrawl API key for web scraping
- `qdrant_host` (str, default="localhost"): Qdrant server host
- `qdrant_port` (int, default=6333): Qdrant server port
- `collection_name` (str, default="web_documents"): Qdrant collection name
- `embedding_model` (str, default="all-MiniLM-L6-v2"): Sentence Transformer model
- `llm_model` (str, default="gpt-4"): LiteLLM model identifier

#### `scrape_and_store(url, limit=10) -> int`

Scrape a website and store documents in Qdrant.

**Parameters:**
- `url` (str): Website URL to scrape
- `limit` (int): Maximum number of pages to crawl

**Returns:** Number of documents stored

**Example:**
```python
count = pipeline.scrape_and_store("https://example.com", limit=5)
print(f"Stored {count} documents")
```

#### `add_documents(documents) -> int`

Add custom documents to the knowledge base.

**Parameters:**
- `documents` (list[dict]): List of documents with keys: `title`, `content`, `url`

**Returns:** Number of documents added

**Example:**
```python
docs = [
    {"title": "Doc 1", "content": "Content...", "url": "internal://doc1"},
    {"title": "Doc 2", "content": "Content...", "url": "internal://doc2"},
]
pipeline.add_documents(docs)
```

#### `search(query, limit=5) -> list[dict]`

Search for similar documents.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum results

**Returns:** List of documents with `score`, `title`, `url`, `content`

**Example:**
```python
results = pipeline.search("How to deploy?", limit=3)
for doc in results:
    print(f"{doc['title']} (score: {doc['score']:.3f})")
```

#### `generate(query, search_limit=5) -> str`

Generate response using LLM with RAG context.

**Parameters:**
- `query` (str): User question
- `search_limit` (int): Number of context documents

**Returns:** Generated response

**Example:**
```python
answer = pipeline.generate("What is Docker?")
print(answer)
```

#### `stats() -> dict`

Get pipeline statistics.

**Returns:** Dictionary with `collection`, `documents_count`, `embedding_model`, `llm_model`

## Examples

### Example 1: Local Knowledge Base

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline(llm_model="gpt-4")

# Add your documents
docs = [
    {
        "title": "Company Policy",
        "content": "All employees must follow...",
        "url": "internal://policies/general"
    },
    {
        "title": "Security Guidelines",
        "content": "Password requirements...",
        "url": "internal://policies/security"
    }
]
pipeline.add_documents(docs)

# Answer questions about your company
answer = pipeline.generate("What are the password requirements?")
print(answer)
```

### Example 2: Web Documentation

```python
from rag_pipeline import RAGPipeline
import os

pipeline = RAGPipeline(
    firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
    llm_model="gpt-4"
)

# Scrape documentation
pipeline.scrape_and_store("https://docs.example.com", limit=50)

# Create chat bot
while True:
    query = input("Q: ")
    if query.lower() == "exit":
        break
    answer = pipeline.generate(query)
    print(f"A: {answer}\n")
```

### Example 3: Multi-Model Comparison

```python
from rag_pipeline import RAGPipeline

docs = [{"title": "Doc", "content": "Content..."}]

models = ["gpt-4", "claude-3-opus-20240229", "gpt-3.5-turbo"]

for model in models:
    print(f"\n=== {model} ===")
    pipeline = RAGPipeline(llm_model=model)
    pipeline.add_documents(docs)
    
    answer = pipeline.generate("Your question")
    print(answer)
```

### Example 4: Batch Processing

```python
from rag_pipeline import RAGPipeline
import json

pipeline = RAGPipeline(llm_model="gpt-4")

# Load documents
with open("documents.jsonl") as f:
    docs = [json.loads(line) for line in f]

pipeline.add_documents(docs)

# Process queries
queries = [
    "What is the pricing?",
    "How do I get support?",
    "What are the features?",
]

results = []
for query in queries:
    answer = pipeline.generate(query)
    results.append({"query": query, "answer": answer})

# Save results
with open("answers.jsonl", "w") as f:
    for result in results:
        f.write(json.dumps(result) + "\n")
```

## Supported LLM Models

### OpenAI
- `gpt-4` (recommended)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Anthropic
- `claude-3-opus-20240229` (most capable)
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### Open Source (via OpenRouter)
- `openrouter/deepseek-chat`
- `openrouter/mistral-7b`
- `openrouter/neural-chat-7b`

### Local (Ollama)
- `ollama/llama2`
- `ollama/mistral`
- `ollama/neural-chat`

See [LiteLLM models](https://docs.litellm.ai/docs/providers) for complete list.

## Embedding Models

Available sentence-transformers models:

- `all-MiniLM-L6-v2` (fast, 384 dims, recommended)
- `all-mpnet-base-v2` (accurate, 768 dims, slower)
- `distiluse-base-multilingual-cased-v2` (multilingual)

## Troubleshooting

### "Qdrant connection refused"
```bash
# Ensure Qdrant is running
docker compose up -d qdrant
# Check status
docker compose ps
```

### "OpenAI API key not set"
```bash
export OPENAI_API_KEY="sk-..."
python3 rag_pipeline.py
```

### "No module named 'sentence_transformers'"
```bash
uv pip install --system sentence-transformers
```

### "Firecrawl API key not configured"
Scraping will be disabled. Use `.add_documents()` instead or set `FIRECRAWL_API_KEY`.

### Memory usage high
- Use smaller embedding model: `all-MiniLM-L6-v2` (default)
- Reduce Qdrant `limit` when searching
- Clear collection: `pipeline.qdrant.delete_collection(pipeline.collection_name)`

## Performance Tips

1. **Batch processing**: Add multiple documents at once rather than one by one
2. **Smaller embedding model**: Use `all-MiniLM-L6-v2` for speed
3. **Limit context**: Search for fewer documents (default 5) to speed up LLM
4. **Cache embeddings**: Store embeddings in Qdrant, don't recompute
5. **Use cheaper models**: Start with GPT-3.5-turbo, switch to GPT-4 if needed

## Next Steps

- Add Slack/Discord bot integration
- Build web UI with Streamlit or FastAPI
- Deploy as microservice
- Add document versioning
- Implement citation tracking
- Add semantic chunking for better context
