"""
Advanced Data Ingestion with Enhanced Metadata Extraction
==========================================================
Features:
- Smart content type detection
- Rich metadata extraction
- Document quality scoring
- Optimized chunking strategies
"""

import os
import json
import time
import re
from typing import List, Dict, Any
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import hashlib

# Get the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Settings
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "chunks_new.json")
COLLECTION_NAME = "Uk_docs"
EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v4"

print("=" * 80)
print("🚀 ADVANCED DATA INGESTION SYSTEM")
print("=" * 80)
print(f"📁 Data File: {DATA_PATH}")
print(f"💾 Collection: {COLLECTION_NAME}")
print(f"🤖 Model: {EMBEDDING_MODEL_NAME}")
print("=" * 80)


class DocumentAnalyzer:
    """Analyze and extract rich metadata from documents"""
    
    @staticmethod
    def detect_doc_type(content: str) -> str:
        """Detect document type based on content patterns"""
        content_lower = content.lower()
        
        # Check for specific patterns
        if any(keyword in content_lower for keyword in ['visa', 'application', 'immigration']):
            return 'immigration'
        elif any(keyword in content_lower for keyword in ['study', 'university', 'course', 'degree']):
            return 'education'
        elif any(keyword in content_lower for keyword in ['work', 'employment', 'job', 'salary']):
            return 'employment'
        elif any(keyword in content_lower for keyword in ['health', 'medical', 'nhs', 'doctor']):
            return 'healthcare'
        elif any(keyword in content_lower for keyword in ['tax', 'payment', 'fee', 'cost']):
            return 'financial'
        else:
            return 'general'
    
    @staticmethod
    def detect_language(content: str) -> str:
        """Simple language detection"""
        # Check for Arabic characters
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        if arabic_pattern.search(content):
            return 'ar'
        return 'en'
    
    @staticmethod
    def extract_entities(content: str) -> Dict[str, List[str]]:
        """Extract key entities from content"""
        entities = {
            'dates': [],
            'urls': [],
            'emails': [],
            'phone_numbers': []
        }
        
        # Extract dates (simple patterns)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        entities['dates'] = re.findall(date_pattern, content)
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        entities['urls'] = re.findall(url_pattern, content)
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, content)
        
        # Extract phone numbers (UK format)
        phone_pattern = r'\b(?:\+44|0)[\d\s-]{9,13}\b'
        entities['phone_numbers'] = re.findall(phone_pattern, content)
        
        return entities
    
    @staticmethod
    def calculate_quality_score(content: str, metadata: Dict) -> float:
        """
        Calculate document quality score (0-1)
        Higher score = better document quality
        """
        score = 0.0
        
        # Length score (optimal 100-2000 chars)
        length = len(content)
        if 100 <= length <= 2000:
            score += 0.3
        elif 50 <= length < 100 or 2000 < length <= 3000:
            score += 0.15
        
        # Structure score (has lists, bold text, etc.)
        if re.search(r'\*\*.*?\*\*', content):  # Bold text
            score += 0.1
        if re.search(r'^\d+\.|\*|-', content, re.MULTILINE):  # Lists
            score += 0.1
        if re.search(r'#{1,6}\s', content):  # Headers
            score += 0.1
        
        # Information density (has numbers, dates, specifics)
        if re.search(r'\d+', content):
            score += 0.1
        
        # Has useful metadata
        if metadata.get('filename'):
            score += 0.1
        if metadata.get('section'):
            score += 0.1
        
        # Completeness (not truncated)
        if not content.endswith('...'):
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def extract_section_info(content: str) -> Dict[str, str]:
        """Extract section and subsection information"""
        section_info = {
            'section': '',
            'subsection': '',
            'has_title': False
        }
        
        # Look for markdown headers
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        h2_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        
        if h1_match:
            section_info['section'] = h1_match.group(1).strip()
            section_info['has_title'] = True
        
        if h2_match:
            section_info['subsection'] = h2_match.group(1).strip()
        
        return section_info


class OptimizedJinaEmbeddings:
    """Optimized Jina Embeddings with GPU acceleration"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        print(f"🚀 Loading Jina Embeddings model...")
        start_time = time.time()
        
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device='cuda',
            model_kwargs={'default_task': 'retrieval'}
        )
        
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        self.batch_times = []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents"""
        if not texts:
            return []
        
        batch_start = time.time()
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
                task='retrieval',
                batch_size=8  # Optimized for GPU
            )
            
            batch_time = time.time() - batch_start
            self.batch_times.append(batch_time)
            
            return embeddings.tolist()
            
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            raise


def process_documents_with_metadata(data: List[Dict]) -> List[Dict]:
    """
    Process documents and extract rich metadata
    """
    print(f"\n📊 Processing {len(data)} documents with advanced metadata extraction...")
    
    analyzer = DocumentAnalyzer()
    processed_docs = []
    
    stats = {
        'by_type': {},
        'by_language': {},
        'quality_scores': []
    }
    
    for idx, item in enumerate(tqdm(data, desc="🔍 Analyzing documents")):
        content = item.get("content", "")
        if not content:
            continue
        
        # Convert content to cleaner Markdown
        content = re.sub(r'\[(.*?): (.*?)\]', r'**\1:** \2', content)
        
        # Get original metadata
        original_metadata = item.get("metadata", {})
        
        # === ADVANCED METADATA EXTRACTION ===
        
        # 1. Document type detection
        doc_type = analyzer.detect_doc_type(content)
        
        # 2. Language detection
        language = analyzer.detect_language(content)
        
        # 3. Extract section information
        section_info = analyzer.extract_section_info(content)
        
        # 4. Extract entities
        entities = analyzer.extract_entities(content)
        
        # 5. Calculate quality score
        quality_score = analyzer.calculate_quality_score(content, original_metadata)
        
        # 6. Generate content hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        
        # === BUILD ENHANCED METADATA ===
        enhanced_metadata = {
            # Original metadata
            **{k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
               for k, v in original_metadata.items()},
            
            # Basic info
            'content_length': len(content),
            'word_count': len(content.split()),
            'source_index': idx,
            'content_hash': content_hash,
            
            # Document classification
            'doc_type': doc_type,
            'language': language,
            
            # Section information
            'section': section_info.get('section', ''),
            'subsection': section_info.get('subsection', ''),
            'has_title': section_info.get('has_title', False),
            
            # Quality metrics
            'quality_score': round(quality_score, 2),
            
            # Entity counts
            'has_dates': len(entities['dates']) > 0,
            'has_urls': len(entities['urls']) > 0,
            'date_count': len(entities['dates']),
            'url_count': len(entities['urls']),
            
            # Processing metadata
            'ingestion_date': datetime.now().isoformat(),
        }
        
        # Update stats
        stats['by_type'][doc_type] = stats['by_type'].get(doc_type, 0) + 1
        stats['by_language'][language] = stats['by_language'].get(language, 0) + 1
        stats['quality_scores'].append(quality_score)
        
        processed_docs.append({
            'content': content,
            'metadata': enhanced_metadata,
            'id': f"doc_{idx}"
        })
    
    # Print statistics
    print(f"\n📈 Document Statistics:")
    print(f"  📚 Total documents: {len(processed_docs)}")
    print(f"  📊 By type: {dict(stats['by_type'])}")
    print(f"  🌍 By language: {dict(stats['by_language'])}")
    print(f"  ⭐ Avg quality score: {sum(stats['quality_scores'])/len(stats['quality_scores']):.2f}")
    
    return processed_docs


def read_and_process_json():
    """Read and process JSON data"""
    print(f"\n📖 Reading data from: {DATA_PATH}")
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ File not found: {DATA_PATH}")
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("❌ Invalid JSON format. Expected a list of objects.")
        return []

    print(f"✅ Loaded {len(data)} raw items")
    
    # Process with advanced metadata extraction
    processed_docs = process_documents_with_metadata(data)
    
    return processed_docs


def main():
    """Main ingestion pipeline"""
    print("\n" + "=" * 80)
    print("🚀 STARTING ADVANCED DATA INGESTION PIPELINE")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    try:
        # 1. Load embedding model
        embedding_model = OptimizedJinaEmbeddings()
        
        # 2. Connect to ChromaDB
        print("\n📡 Connecting to ChromaDB...")
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        try:
            client.heartbeat()
            print("✅ Connected to ChromaDB")
        except Exception as e:
            print(f"❌ Could not connect to ChromaDB: {e}")
            return
        
        # 3. Recreate collection
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"🗑️  Deleted old collection: {COLLECTION_NAME}")
        except:
            print("🔹 No old collection found")
        
        collection = client.create_collection(name=COLLECTION_NAME)
        print(f"✅ Created new collection: {COLLECTION_NAME}")
        
        # 4. Read and process documents
        docs_data = read_and_process_json()
        if not docs_data:
            print("❌ No documents to process!")
            return
        
        # 5. Prepare for upload
        documents = [d['content'] for d in docs_data]
        metadatas = [d['metadata'] for d in docs_data]
        ids = [d['id'] for d in docs_data]
        
        # 6. Upload to ChromaDB in batches
        print(f"\n" + "=" * 80)
        print(f"📤 UPLOADING {len(documents)} DOCUMENTS TO CHROMADB")
        print("=" * 80)
        
        BATCH_SIZE = 16
        total_uploaded = 0
        failed_batches = 0
        
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        
        with tqdm(total=total_batches, desc="📦 Uploading batches") as pbar:
            for i in range(0, len(documents), BATCH_SIZE):
                batch_docs = documents[i:i+BATCH_SIZE]
                batch_ids = ids[i:i+BATCH_SIZE]
                batch_metas = metadatas[i:i+BATCH_SIZE]
                
                try:
                    # Generate embeddings
                    embeddings = embedding_model.embed_documents(batch_docs)
                    
                    # Upload to ChromaDB
                    collection.add(
                        ids=batch_ids,
                        documents=batch_docs,
                        metadatas=batch_metas,
                        embeddings=embeddings
                    )
                    
                    total_uploaded += len(batch_docs)
                    pbar.update(1)
                    pbar.set_postfix({
                        'uploaded': total_uploaded,
                        'failed': failed_batches
                    })
                    
                except Exception as e:
                    print(f"\n❌ Batch {i//BATCH_SIZE + 1} failed: {e}")
                    failed_batches += 1
        
        # 7. Final statistics
        total_time = time.time() - start_time
        
        print(f"\n" + "=" * 80)
        print("🎉 INGESTION COMPLETE!")
        print("=" * 80)
        print(f"⏱️  Total time: {total_time/60:.2f} minutes")
        print(f"✅ Successfully uploaded: {total_uploaded} documents")
        print(f"❌ Failed batches: {failed_batches}")
        print(f"📊 Final collection count: {collection.count()}")
        print(f"⚡ Average embedding time: {sum(embedding_model.batch_times)/len(embedding_model.batch_times):.3f}s per batch")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ INGESTION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
