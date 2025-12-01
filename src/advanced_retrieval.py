"""
Advanced RAG Retrieval System
==============================
Features:
- Hybrid Search (BM25 + Vector Search with RRF)
- Hierarchical Retrieval (3-stage)
- Cross-Encoder Re-ranking
- Advanced Metadata Filtering
"""

import chromadb
from typing import List, Dict, Optional, Tuple
import logging
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import time
from collections import defaultdict

logger = logging.getLogger("src.advanced_retrieval")

EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v4"
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class JinaEmbedding:
    """Jina Embeddings v4 wrapper"""
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        logger.info(f"🚀 Loading Jina Embeddings: {model_name}")
        try:
            self.model = SentenceTransformer(
                model_name,
                trust_remote_code=True,
                device='cuda',
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


class HybridRetriever:
    """
    Hybrid Search combining BM25 (keyword) and Vector Search (semantic)
    using Reciprocal Rank Fusion (RRF)
    """
    
    def __init__(self, collection, embedding_fn: JinaEmbedding):
        self.collection = collection
        self.embedding_fn = embedding_fn
        self.bm25_index = None
        self.doc_ids = []
        self.documents = []
        self._build_bm25_index()
        
    def _build_bm25_index(self):
        """Build BM25 index from ChromaDB collection"""
        logger.info("🔨 Building BM25 index...")
        start_time = time.time()
        
        try:
            # Get all documents from collection
            all_docs = self.collection.get(include=['documents', 'metadatas'])
            
            self.doc_ids = all_docs['ids']
            self.documents = all_docs['documents']
            
            # Tokenize documents for BM25
            tokenized_docs = [doc.lower().split() for doc in self.documents]
            self.bm25_index = BM25Okapi(tokenized_docs)
            
            build_time = time.time() - start_time
            logger.info(f"✅ BM25 index built in {build_time:.2f}s with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to build BM25 index: {e}")
            raise
    
    def _bm25_search(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """BM25 keyword search"""
        if not self.bm25_index:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(self.doc_ids[i], scores[i]) for i in top_indices if scores[i] > 0]
        
        return results
    
    def _vector_search(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """Semantic vector search"""
        try:
            query_embedding = self.embedding_fn.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['distances']
            )
            
            # Convert distances to similarity scores (1 - distance for normalized embeddings)
            doc_ids = results['ids'][0] if results['ids'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            # For cosine distance, similarity = 1 - distance
            similarities = [1 - dist for dist in distances]
            
            return list(zip(doc_ids, similarities))
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self, 
        bm25_results: List[Tuple[str, float]], 
        vector_results: List[Tuple[str, float]], 
        k: int = 60
    ) -> List[str]:
        """
        Reciprocal Rank Fusion (RRF) to combine BM25 and Vector Search
        RRF Score = sum(1 / (k + rank)) for each retrieval method
        """
        rrf_scores = defaultdict(float)
        
        # Add BM25 scores
        for rank, (doc_id, score) in enumerate(bm25_results, 1):
            rrf_scores[doc_id] += 1 / (k + rank)
        
        # Add Vector scores
        for rank, (doc_id, score) in enumerate(vector_results, 1):
            rrf_scores[doc_id] += 1 / (k + rank)
        
        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [doc_id for doc_id, score in sorted_docs]
    
    def hybrid_search(
        self, 
        query: str, 
        top_k: int = 50,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and Vector Search
        """
        logger.info(f"🔍 Hybrid search for: '{query[:50]}...'")
        
        # Stage 1: Get candidates from both methods
        bm25_results = self._bm25_search(query, top_k=100)
        vector_results = self._vector_search(query, top_k=100)
        
        logger.info(f"📊 BM25 found {len(bm25_results)} results, Vector found {len(vector_results)}")
        
        # Stage 2: Reciprocal Rank Fusion
        fused_doc_ids = self._reciprocal_rank_fusion(bm25_results, vector_results)
        
        # Stage 3: Get top-k documents with metadata
        final_results = []
        for doc_id in fused_doc_ids[:top_k]:
            try:
                doc_data = self.collection.get(
                    ids=[doc_id],
                    include=['documents', 'metadatas']
                )
                
                if doc_data['documents']:
                    metadata = doc_data['metadatas'][0] if doc_data['metadatas'] else {}
                    
                    # Apply metadata filter if provided
                    if metadata_filter:
                        if not all(metadata.get(k) == v for k, v in metadata_filter.items()):
                            continue
                    
                    final_results.append({
                        'id': doc_id,
                        'content': doc_data['documents'][0],
                        'metadata': metadata
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to get doc {doc_id}: {e}")
                continue
        
        logger.info(f"✅ Hybrid search returned {len(final_results)} results")
        return final_results


class HierarchicalRetriever:
    """
    3-Stage Hierarchical Retrieval:
    1. Document-level retrieval (top 50)
    2. Chunk-level retrieval within top documents (top 100)
    3. Re-ranking with cross-encoder (top 10)
    """
    
    def __init__(self, hybrid_retriever: HybridRetriever, reranker_model: str = RERANKER_MODEL_NAME):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = None
        self._load_reranker(reranker_model)
        
    def _load_reranker(self, model_name: str):
        """Load cross-encoder for re-ranking"""
        logger.info(f"🚀 Loading Re-ranker: {model_name}")
        try:
            self.reranker = CrossEncoder(model_name, max_length=512, device='cuda')
            logger.info("✅ Re-ranker loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load re-ranker, continuing without it: {e}")
            self.reranker = None
    
    def _rerank_results(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """Re-rank results using cross-encoder"""
        if not self.reranker or len(results) <= top_k:
            return results[:top_k]
        
        logger.info(f"🎯 Re-ranking {len(results)} results...")
        
        try:
            # Prepare query-document pairs
            pairs = [[query, result['content']] for result in results]
            
            # Get relevance scores
            scores = self.reranker.predict(pairs)
            
            # Sort by score
            scored_results = list(zip(results, scores))
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            reranked = [result for result, score in scored_results[:top_k]]
            
            logger.info(f"✅ Re-ranking complete, top score: {scored_results[0][1]:.3f}")
            return reranked
            
        except Exception as e:
            logger.error(f"❌ Re-ranking failed: {e}")
            return results[:top_k]
    
    def retrieve(
        self, 
        query: str, 
        stage1_k: int = 50,
        stage2_k: int = 100, 
        final_k: int = 10,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        3-Stage Hierarchical Retrieval
        """
        start_time = time.time()
        
        # Stage 1: Hybrid search for top candidates
        logger.info(f"📍 Stage 1: Hybrid search (top {stage1_k})")
        candidates = self.hybrid_retriever.hybrid_search(
            query, 
            top_k=stage1_k,
            metadata_filter=metadata_filter
        )
        
        if not candidates:
            logger.warning("⚠️ No candidates found in Stage 1")
            return []
        
        # Stage 2: Expand to more chunks if needed
        # (في حالة البيانات الحالية، ما عندناش document hierarchy، 
        #  لكن يمكن نضيف logic هنا لو كان عندنا PDFs كبيرة)
        logger.info(f"📍 Stage 2: Chunk expansion (keeping top {min(stage2_k, len(candidates))})")
        expanded_results = candidates[:stage2_k]
        
        # Stage 3: Re-ranking
        logger.info(f"📍 Stage 3: Re-ranking (top {final_k})")
        final_results = self._rerank_results(query, expanded_results, top_k=final_k)
        
        total_time = time.time() - start_time
        logger.info(f"✅ Hierarchical retrieval complete in {total_time:.3f}s")
        
        return final_results


class AdvancedKnowledgeBase:
    """
    Advanced Knowledge Base with:
    - Hybrid Search (BM25 + Vector)
    - Hierarchical Retrieval
    - Cross-Encoder Re-ranking
    - Metadata Filtering
    """
    
    def __init__(self, collection_name: str = "Uk_docs"):
        try:
            # Connect to ChromaDB
            self.client = chromadb.HttpClient(host='localhost', port=8000)
            self.collection = self.client.get_collection(name=collection_name)
            
            # Initialize embedding function
            self.embedding_fn = JinaEmbedding()
            
            # Initialize Hybrid Retriever
            self.hybrid_retriever = HybridRetriever(self.collection, self.embedding_fn)
            
            # Initialize Hierarchical Retriever
            self.hierarchical_retriever = HierarchicalRetriever(self.hybrid_retriever)
            
            logger.info(f"✅ Advanced Knowledge Base initialized")
            logger.info(f"📊 Collection: {collection_name}")
            logger.info(f"📊 Document count: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Advanced Knowledge Base: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        n_results: int = 10,
        metadata_filter: Optional[Dict] = None,
        use_reranking: bool = True
    ) -> List[Dict]:
        """
        Advanced search with all optimizations
        """
        try:
            if use_reranking:
                # Use full hierarchical retrieval with re-ranking
                results = self.hierarchical_retriever.retrieve(
                    query,
                    stage1_k=50,
                    stage2_k=100,
                    final_k=n_results,
                    metadata_filter=metadata_filter
                )
            else:
                # Use hybrid search only (faster)
                results = self.hybrid_retriever.hybrid_search(
                    query,
                    top_k=n_results,
                    metadata_filter=metadata_filter
                )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []


def get_formatted_context(query: str, kb: AdvancedKnowledgeBase, n_results: int = 3) -> str:
    """Format search results as context for LLM"""
    results = kb.search(query, n_results=n_results)
    
    if not results:
        return ""
    
    context_parts = []
    for i, res in enumerate(results, 1):
        filename = res.get('metadata', {}).get('filename', 'Unknown')
        content = res.get('content', '')
        context_parts.append(f"[Source {i} - {filename}]:\n{content}")
    
    return "\n\n".join(context_parts)
