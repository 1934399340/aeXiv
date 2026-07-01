import chromadb

print("正在加载ChromaDB...")
client = chromadb.PersistentClient(path="Q:/aeXiv论文检索系统/arxiv-rag/data/embeddings/chroma")

print("获取集合...")
try:
    collection = client.get_collection("arxiv_papers")
    count = collection.count()
    print(f"论文数量: {count}")
    
    # 测试查询
    print("\n测试查询...")
    results = collection.get(limit=3)
    print(f"返回结果: {len(results['ids'])} 篇")
    for i, doc_id in enumerate(results['ids'][:3]):
        print(f"  {i+1}. {doc_id}")
        
except Exception as e:
    print(f"错误: {e}")
