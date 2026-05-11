#!/usr/bin/env python3
"""
Complete RAG Pipeline: Firecrawl + Qdrant + LiteLLM
Scrapes websites, embeds content, stores in vector DB, and generates responses with LLM.
"""

import os
import sys
from typing import Optional
from firecrawl import FirecrawlApp
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from litellm import completion
import hashlib


class RAGPipeline:
    def __init__(
        self,
        firecrawl_api_key: Optional[str] = None,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "web_documents",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_model: str = "gpt-4",
    ):
        """Initialize RAG pipeline with all components."""
        self.firecrawl_api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY")
        self.collection_name = collection_name
        self.llm_model = llm_model
        
        # Initialize Firecrawl
        if self.firecrawl_api_key:
            self.firecrawl = FirecrawlApp(api_key=self.firecrawl_api_key)
            print("✅ Firecrawl initialized (cloud API)")
        else:
            self.firecrawl = None
            print("⚠️  Firecrawl API key not set - scraping disabled")
        
        # Initialize Qdrant
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        print(f"✅ Qdrant connected at {qdrant_host}:{qdrant_port}")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        print(f"✅ Embedding model loaded: {embedding_model}")
        
        # Setup Qdrant collection
        self._setup_collection()
    
    def _setup_collection(self):
        """Create or verify Qdrant collection."""
        try:
            self.qdrant.get_collection(self.collection_name)
            print(f"✅ Collection '{self.collection_name}' exists")
        except Exception:
            print(f"📦 Creating collection '{self.collection_name}'...")
            self.qdrant.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            print(f"✅ Collection created")
    
    def _url_to_id(self, url: str, content: str = "") -> int:
        """Convert URL to consistent hash ID."""
        key = f"{url}:{content[:100]}"
        return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
    
    def scrape_and_store(self, url: str, limit: int = 10) -> int:
        """Scrape website and store in Qdrant."""
        if not self.firecrawl:
            print("❌ Firecrawl API key not configured")
            return 0
        
        print(f"🔄 Scraping {url}...")
        try:
            # Crawl website
            crawl_result = self.firecrawl.crawl_url(
                url=url,
                params={
                    "limit": limit,
                    "allowBackendCrawls": False,
                    "onlyMainContent": True,
                }
            )
            
            if not crawl_result:
                print(f"❌ No content scraped from {url}")
                return 0
            
            # Process and store documents
            points = []
            for i, page in enumerate(crawl_result):
                if not page.get("markdown"):
                    continue
                
                # Create embedding
                embedding = self.embedding_model.encode(page["markdown"]).tolist()
                
                # Create point
                point_id = self._url_to_id(page.get("url", url), page["markdown"])
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "url": page.get("url", url),
                            "title": page.get("title", ""),
                            "content": page["markdown"][:5000],  # Store first 5k chars
                            "source": "firecrawl",
                        }
                    )
                )
            
            if not points:
                print(f"❌ No content to store")
                return 0
            
            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"✅ Stored {len(points)} documents from {url}")
            return len(points)
        
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return 0
    
    def add_documents(self, documents: list[dict]) -> int:
        """Add custom documents to Qdrant."""
        print(f"📝 Adding {len(documents)} custom documents...")
        points = []
        
        for i, doc in enumerate(documents):
            content = doc.get("content", doc.get("text", ""))
            if not content:
                continue
            
            embedding = self.embedding_model.encode(content).tolist()
            point_id = self._url_to_id(doc.get("url", f"doc_{i}"), content)
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "url": doc.get("url", f"custom_{i}"),
                        "title": doc.get("title", ""),
                        "content": content[:5000],
                        "source": "custom",
                    }
                )
            )
        
        if points:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"✅ Added {len(points)} documents")
            return len(points)
        return 0
    
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search Qdrant for similar documents."""
        # Embed query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search
        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
        ).points
        
        # Format results
        documents = []
        for result in results:
            documents.append({
                "score": result.score,
                "title": result.payload.get("title", ""),
                "url": result.payload.get("url", ""),
                "content": result.payload.get("content", ""),
            })
        
        return documents
    
    def generate(self, query: str, search_limit: int = 5) -> str:
        """Generate response using LLM with RAG context."""
        print(f"\n🔍 Query: {query}")
        
        # Search for relevant documents
        documents = self.search(query, limit=search_limit)
        
        if not documents:
            print("❌ No relevant documents found")
            return "No relevant information found in the knowledge base."
        
        # Build context
        context = "\n\n".join([
            f"[{i+1}] Source: {doc['url']}\nTitle: {doc['title']}\nContent:\n{doc['content']}"
            for i, doc in enumerate(documents)
        ])
        
        print(f"✅ Found {len(documents)} relevant documents")
        
        # Generate with LLM
        print(f"🤖 Generating response with {self.llm_model}...")
        
        try:
            response = completion(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer the user's question based on the provided context. If the context doesn't contain relevant information, say so."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}"
                    }
                ],
                temperature=0.7,
            )
            
            answer = response.get("choices", [{}])[0].get("message", {}).get("content", "No response generated")
            print(f"✅ Response generated")
            return answer
        
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return f"Error generating response: {e}"
    
    def stats(self) -> dict:
        """Get pipeline statistics."""
        collection = self.qdrant.get_collection(self.collection_name)
        return {
            "collection": self.collection_name,
            "documents_count": collection.points_count,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": self.llm_model,
        }


def main():
    """Example usage."""
    import json
    
    # Initialize pipeline
    pipeline = RAGPipeline(
        llm_model="gpt-4",
    )
    
    print("\n" + "="*60)
    print("RAG PIPELINE: Firecrawl + Qdrant + LiteLLM")
    print("="*60)
    
    # Example 1: Add custom documents
    print("\n[Example 1] Adding custom documents...")
    custom_docs = [
        {
            "url": "internal://doc1",
            "title": "Docker Basics",
            "content": "Docker is a containerization platform. Containers are lightweight and portable. Use `docker run` to start a container, `docker compose` for multi-container apps."
        },
        {
            "url": "internal://doc2",
            "title": "Qdrant Guide",
            "content": "Qdrant is a vector database for similarity search. You can store embeddings and search by vector similarity. It supports fast approximate nearest neighbor (ANN) search."
        },
        {
            "url": "internal://doc3",
            "title": "RAG Pipelines",
            "content": "Retrieval-Augmented Generation (RAG) combines document retrieval with LLM generation. RAG improves accuracy by providing context from a knowledge base."
        }
    ]
    pipeline.add_documents(custom_docs)
    
    # Example 2: Search
    print("\n[Example 2] Searching documents...")
    query = "How does Docker work?"
    results = pipeline.search(query, limit=3)
    print(f"\nSearch results for: '{query}'")
    for i, doc in enumerate(results, 1):
        print(f"  {i}. {doc['title']} (score: {doc['score']:.3f})")
    
    # Example 3: Generate with RAG
    print("\n[Example 3] Generating response with RAG...")
    query = "What is Qdrant and how is it used?"
    answer = pipeline.generate(query)
    print(f"\nAnswer:\n{answer}")
    
    # Example 4: Scrape website (requires API key)
    print("\n[Example 4] Website scraping (requires FIRECRAWL_API_KEY)...")
    if pipeline.firecrawl:
        # Uncomment to scrape real websites
        # pipeline.scrape_and_store("https://docs.docker.com", limit=5)
        print("⏭️  Skipped (set FIRECRAWL_API_KEY to enable)")
    else:
        print("⏭️  Firecrawl not configured")
    
    # Example 5: Another question
    print("\n[Example 5] Another query...")
    query = "Tell me about RAG pipelines"
    answer = pipeline.generate(query)
    print(f"\nAnswer:\n{answer}")
    
    # Stats
    print("\n[Stats]")
    stats = pipeline.stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
