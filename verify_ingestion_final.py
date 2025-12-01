import chromadb

client = chromadb.HttpClient(host='localhost', port=8000)
collection = client.get_collection("Uk_docs")
print(f"Collection count: {collection.count()}")

