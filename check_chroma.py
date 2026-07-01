import sqlite3
import chromadb

# Check ChromaDB collection
client = chromadb.PersistentClient(path="Q:/aeXiv论文检索系统/arxiv-rag/data/embeddings/chroma")
try:
    collection = client.get_collection("arxiv_papers")
    count = collection.count()
    print(f"ChromaDB论文数量: {count}")
except Exception as e:
    print(f"ChromaDB状态: {e}")
    # Try to list collections
    try:
        collections = client.list_collections()
        print(f"可用集合: {collections}")
    except:
        pass
