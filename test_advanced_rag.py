"""
Test Advanced RAG System
========================
Test the new hybrid search, hierarchical retrieval, and re-ranking
"""

import sys
import os
import logging
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.advanced_retrieval import AdvancedKnowledgeBase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_search_methods():
    """Test different search methods and compare results"""
    
    print("=" * 80)
    print("🧪 TESTING ADVANCED RAG SYSTEM")
    print("=" * 80)
    
    # Initialize knowledge base
    print("\n1️⃣ Initializing Advanced Knowledge Base...")
    kb = AdvancedKnowledgeBase(collection_name="Uk_docs")
    
    # Test queries
    test_queries = [
        "How can I apply for a UK student visa?",
        "What are the requirements for work visa?",
        "visa application process",
        "UK immigration requirements"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"🔍 Test Query {i}: {query}")
        print("=" * 80)
        
        # Test 1: Hybrid Search without re-ranking
        print("\n📊 Method 1: Hybrid Search (No Re-ranking)")
        print("-" * 80)
        start_time = time.time()
        results_no_rerank = kb.search(
            query, 
            n_results=5,
            use_reranking=False
        )
        time_no_rerank = time.time() - start_time
        
        print(f"⏱️  Time: {time_no_rerank:.3f}s")
        print(f"📄 Results: {len(results_no_rerank)}")
        
        if results_no_rerank:
            print("\n🔝 Top Result:")
            top = results_no_rerank[0]
            print(f"  📝 Content preview: {top['content'][:200]}...")
            print(f"  🏷️  Metadata: {top.get('metadata', {})}")
        
        # Test 2: Hierarchical Retrieval with re-ranking
        print("\n📊 Method 2: Hierarchical Retrieval + Re-ranking")
        print("-" * 80)
        start_time = time.time()
        results_with_rerank = kb.search(
            query,
            n_results=5,
            use_reranking=True
        )
        time_with_rerank = time.time() - start_time
        
        print(f"⏱️  Time: {time_with_rerank:.3f}s")
        print(f"📄 Results: {len(results_with_rerank)}")
        
        if results_with_rerank:
            print("\n🔝 Top Result:")
            top = results_with_rerank[0]
            print(f"  📝 Content preview: {top['content'][:200]}...")
            print(f"  🏷️  Metadata: {top.get('metadata', {})}")
        
        # Compare
        print(f"\n📈 Performance Comparison:")
        print(f"  ⚡ Speed difference: {(time_with_rerank - time_no_rerank):.3f}s ({(time_with_rerank/time_no_rerank - 1)*100:+.1f}%)")
        print(f"  🎯 Re-ranking overhead: {time_with_rerank - time_no_rerank:.3f}s")
        
        # Test 3: With metadata filter
        print("\n📊 Method 3: With Metadata Filter")
        print("-" * 80)
        start_time = time.time()
        results_filtered = kb.search(
            query,
            n_results=5,
            metadata_filter={'doc_type': 'immigration'}
        )
        time_filtered = time.time() - start_time
        
        print(f"⏱️  Time: {time_filtered:.3f}s")
        print(f"📄 Results: {len(results_filtered)}")
        
        if len(results_filtered) > 0:
            print("✅ Metadata filtering works!")
        
        print("\n" + "-" * 80)
        input("Press Enter to continue to next query...")


def test_quality_metrics():
    """Test metadata quality metrics"""
    print("\n" + "=" * 80)
    print("📊 TESTING METADATA & QUALITY METRICS")
    print("=" * 80)
    
    kb = AdvancedKnowledgeBase(collection_name="Uk_docs")
    
    # Search for any query
    results = kb.search("UK visa", n_results=10, use_reranking=False)
    
    print(f"\n📈 Analyzing {len(results)} documents:")
    print("-" * 80)
    
    quality_scores = []
    doc_types = {}
    languages = {}
    
    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        
        quality = metadata.get('quality_score', 0)
        doc_type = metadata.get('doc_type', 'unknown')
        language = metadata.get('language', 'unknown')
        
        quality_scores.append(quality)
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        languages[language] = languages.get(language, 0) + 1
        
        print(f"\n{i}. Document #{metadata.get('source_index', '?')}")
        print(f"   ⭐ Quality: {quality}")
        print(f"   📁 Type: {doc_type}")
        print(f"   🌍 Language: {language}")
        print(f"   📏 Length: {metadata.get('content_length', 0)} chars")
        print(f"   📝 Words: {metadata.get('word_count', 0)}")
        print(f"   🏷️  Has title: {metadata.get('has_title', False)}")
        print(f"   📍 Section: {metadata.get('section', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print(f"⭐ Average Quality Score: {sum(quality_scores)/len(quality_scores):.2f}")
    print(f"📁 Document Types: {doc_types}")
    print(f"🌍 Languages: {languages}")


def main():
    """Run all tests"""
    try:
        # Test 1: Search methods
        test_search_methods()
        
        # Test 2: Quality metrics
        test_quality_metrics()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
