import chromadb

print("测试ChromaDB查询...")
client = chromadb.PersistentClient(path="Q:/aeXiv论文检索系统/arxiv-rag/data/embeddings/chroma")

try:
    collection = client.get_collection("arxiv_papers")
    print(f"集合数量: {collection.count()}")
    
    # 尝试使用get方法
    print("\n尝试get方法...")
    results = collection.get(limit=5)
    print(f"get返回 {len(results['ids'])} 条记录")
    
    # 显示前3条
    for i in range(min(3, len(results['ids']))):
        print(f"  {i+1}. {results['ids'][i]}")
        
except Exception as e:
    print(f"错误: {e}")
    print("\n尝试其他方法...")
    
    # 尝试删除并重建
    try:
        client.delete_collection("arxiv_papers")
        print("已删除旧集合")
    except:
        pass
