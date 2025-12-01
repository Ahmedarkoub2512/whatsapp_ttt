import os
import json
import time
import re
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Get the project root directory (parent of src/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Settings
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "chunks_new.json")
COLLECTION_NAME = "Uk_docs"
EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v4"

print("--- GENERAL DOCUMENTS Processing ---")
print(f"Data File: {DATA_PATH}")
print(f"Collection: {COLLECTION_NAME}")
print("=" * 60)

class OptimizedJinaEmbeddings:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        print(f"🚀 Loading Jina Embeddings...")
        start_time = time.time()
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device='cuda',  # استخدام GPU
            model_kwargs={'default_task': 'retrieval'}
        )
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.1f} seconds")
        self.batch_times = []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        batch_start = time.time()
        # print(f"� Processing {len(texts)} texts...")
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
                task='retrieval',
                batch_size=2
            )
            
            batch_time = time.time() - batch_start
            self.batch_times.append(batch_time)
            
            return embeddings.tolist()
            
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            raise

def read_and_process_json():
    print(f"📖 Reading {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        print(f"❌ File not found: {DATA_PATH}")
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("❌ Invalid JSON format. Expected a list of objects.")
        return []

    print(f"📁 Found {len(data)} items")
    
    documents_data = []
    
    for idx, item in enumerate(data):
        content = item.get("content", "")
        if not content:
            continue
            
        # Convert content to Markdown
        # Replace [KEY: Value] with **KEY:** Value
        content = re.sub(r'\[(.*?): (.*?)\]', r'**\1:** \2', content)
        
        original_metadata = item.get("metadata", {})
        
        # Ensure metadata values are strings or simple types for ChromaDB
        clean_metadata = {}
        for k, v in original_metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            else:
                clean_metadata[k] = str(v)
        
        # Add extra metadata
        clean_metadata['content_length'] = len(content)
        clean_metadata['source_index'] = idx
        
        documents_data.append({
            'content': content,
            'metadata': clean_metadata,
            'id': f"doc_{idx}"
        })
        
    return documents_data

def main():
    print("🚀 Starting Data Ingestion...\n")
    start_time = time.time()
    
    try:
        # Load embeddings model
        embedding_model = OptimizedJinaEmbeddings()
        
        # Connect to ChromaDB
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        try:
            client.heartbeat()
            print("✅ Connected to ChromaDB")
        except Exception as e:
            print(f"⚠️ Could not connect to ChromaDB: {e}")
            return
        
        # Recreate collection
        try:
            client.delete_collection(COLLECTION_NAME)
            print("🗑️ Deleted old collection")
        except:
            print("🔹 No old collection found")
        
        collection = client.create_collection(name=COLLECTION_NAME)
        print(f"✅ Created collection: {COLLECTION_NAME}")

        # Read and process files
        docs_data = read_and_process_json()
        if not docs_data:
            print("❌ No data to process!")
            return

        # Prepare data for upload
        print("\n--- Preparing data for upload ---")
        
        documents = [d['content'] for d in docs_data]
        metadatas = [d['metadata'] for d in docs_data]
        ids = [d['id'] for d in docs_data]

        # Upload data
        print(f"\n--- Uploading {len(documents)} documents to ChromaDB ---")
        
        BATCH_SIZE = 16  # استخدام batch size أكبر مع GPU
        total_uploaded = 0
        failed_batches = 0
        
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        batch_pbar = tqdm(total=total_batches, desc="🔄 Processing batches")
        
        for i in range(0, len(documents), BATCH_SIZE):
            batch_docs = documents[i:i+BATCH_SIZE]
            batch_ids = ids[i:i+BATCH_SIZE]
            batch_metas = metadatas[i:i+BATCH_SIZE]
            
            try:
                embeddings = embedding_model.embed_documents(batch_docs)
                
                collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas,
                    embeddings=embeddings
                )
                total_uploaded += len(batch_docs)
                batch_pbar.update(1)
                batch_pbar.set_postfix({
                    'uploaded': total_uploaded,
                    'failed': failed_batches
                })
                    
            except Exception as e:
                print(f"❌ Batch {i//BATCH_SIZE + 1} failed: {e}")
                failed_batches += 1
        
        batch_pbar.close()
        
        total_time = time.time() - start_time
        print(f"\n🎉 Processing completed in {total_time/60:.1f} minutes!")
        print(f"📊 Results:")
        print(f"  ✅ Successfully uploaded: {total_uploaded} documents")
        print(f"  ❌ Failed batches: {failed_batches}")
        print(f"  📈 Total in collection: {collection.count()}")
            
    except Exception as e:
        print(f"❌ Process failed: {e}")

if __name__ == "__main__":
    main()
