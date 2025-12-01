import chromadb

# الاتصال بالسيرفر اللي شغال على الكونتينر
client = chromadb.HttpClient(host='localhost', port=8000)

# احصل على الكولكشن
collection_name = "Uk_docs"

try:
    collection = client.get_collection(collection_name)
    # حذف الكولكشن بالكامل
    client.delete_collection(collection_name)
    print(f"Collection '{collection_name}' deleted successfully.")
except Exception as e:
    print(f"Error: {e}")
