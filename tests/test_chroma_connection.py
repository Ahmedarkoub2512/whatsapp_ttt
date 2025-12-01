import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tests.test_chroma")

def test_connection():
    try:
        client = chromadb.HttpClient(host='localhost', port=8000)
        logger.info("✅ Successfully connected to ChromaDB")
        logger.info(f"Heartbeat: {client.heartbeat()}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to ChromaDB: {e}")
        return False

if __name__ == "__main__":
    test_connection()
