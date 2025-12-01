import chromadb
from typing import List, Dict
import logging
import os
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("src.knowledge_base")

EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v4"

class JinaEmbedding:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        logger.info(f"🚀 Loading Jina Embeddings: {model_name}")
        try:
            self.model = SentenceTransformer(
                model_name,
                trust_remote_code=True,
                device='cpu',
                model_kwargs={'default_task': 'retrieval'}
            )
            logger.info("✅ Jina embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Jina model: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            task='retrieval'
        )
        return embedding[0].tolist()

class KnowledgeBase:
    def __init__(self, collection_name: str = "Uk_docs"):
        try:
            # Connect to ChromaDB
            self.client = chromadb.HttpClient(host='localhost', port=8000)
            self.collection = self.client.get_collection(name=collection_name)
            self.embedding_fn = JinaEmbedding()
            logger.info(f"✅ Knowledge base connected to ChromaDB collection: {collection_name}")
            logger.info(f"📊 Document count: {self.collection.count()}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise e

    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        try:
            query_embedding = self.embedding_fn.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            formatted_results = []
            for i in range(len(documents)):
                formatted_results.append({
                    "content": documents[i],
                    "metadata": metadatas[i]
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"❌ Error searching knowledge base: {e}")
            return []

def get_formatted_context(query: str, kb: KnowledgeBase) -> str:
    results = kb.search(query)
    if not results:
        return ""
        
    context_parts = []
    for res in results:
        # You might want to include metadata like filename if available
        filename = res['metadata'].get('filename', 'Unknown')
        context_parts.append(f"Source ({filename}): {res['content']}")
        
    return "\n\n".join(context_parts)
