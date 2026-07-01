"""
只执行ChromaDB写入（跳过向量化）
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings

def main():
    print("=" * 50)
    print("  只执行ChromaDB写入")
    print("=" * 50)
    
    # 加载论文数据
    papers_file = project_root / "data" / "raw" / "cs_all_papers.json"
    print(f"\n📄 加载论文: {papers_file}")
    
    with open(papers_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    print(f"✅ 加载 {len(papers)} 篇论文")
    
    # 准备文档内容
    documents = []
    for paper in papers:
        title = paper.get("title", "")
        title_zh = paper.get("title_zh", "")
        abstract = paper.get("abstract", "")
        abstract_zh = paper.get("abstract_zh", "")
        categories = ", ".join(paper.get("categories", []))
        
        if title_zh:
            content = f"标题: {title_zh} ({title})\n\n"
        else:
            content = f"标题: {title}\n\n"
        
        content += f"分类: {categories}\n\n"
        
        if abstract_zh:
            content += f"摘要: {abstract_zh}\n\n"
            content += f"Abstract: {abstract}"
        else:
            content += f"摘要: {abstract}"
        
        categories_list = paper.get("categories", [])
        primary_category = paper.get("primary_category", categories_list[0] if categories_list else "")
        
        metadata = {
            "id": paper.get("id", ""),
            "title": paper.get("title", ""),
            "title_zh": paper.get("title_zh", paper.get("title", "")),
            "authors": ", ".join(paper.get("authors", [])),
            "categories": categories_list,
            "primary_category": primary_category,
            "published": paper.get("published", ""),
            "pdf_url": paper.get("pdf_url", ""),
            "abstract_length": len(paper.get("abstract", ""))
        }
        
        documents.append({
            "id": paper.get("id", ""),
            "content": content,
            "metadata": metadata
        })
    
    # 加载嵌入模型
    print("\n🔄 加载嵌入模型...")
    from sentence_transformers import SentenceTransformer
    
    local_model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
    model = SentenceTransformer(local_model_path, device="cpu")
    print("✅ 模型加载完成")
    
    # 向量化
    print(f"\n🔄 向量化 {len(documents)} 篇论文...")
    texts = [doc["content"] for doc in documents]
    
    batch_size = 32
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=True, batch_size=batch_size)
        all_embeddings.extend(batch_embeddings.tolist())
        
        current = min(i + batch_size, len(texts))
        if current % 500 == 0:
            print(f"  进度: {current}/{len(texts)}")
    
    print(f"✅ 向量化完成，维度: {len(all_embeddings[0])}")
    
    # 写入ChromaDB
    print("\n🔄 写入ChromaDB...")
    import chromadb
    
    chroma_dir = project_root / "data" / "embeddings" / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name="arxiv_papers",
        metadata={"hnsw:space": "cosine"}
    )
    
    # 分批写入
    ids = [doc["id"] for doc in documents]
    contents = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    
    write_batch_size = 100
    for i in range(0, len(documents), write_batch_size):
        batch_ids = ids[i:i+write_batch_size]
        batch_contents = contents[i:i+write_batch_size]
        batch_embeddings = all_embeddings[i:i+write_batch_size]
        batch_metadatas = metadatas[i:i+write_batch_size]
        
        try:
            collection.add(
                ids=batch_ids,
                documents=batch_contents,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas
            )
            current = min(i + write_batch_size, len(documents))
            print(f"  写入进度: {current}/{len(documents)}")
        except Exception as e:
            print(f"  ❌ 批次写入失败: {e}")
            # 尝试逐条写入
            for j in range(len(batch_ids)):
                try:
                    collection.add(
                        ids=[batch_ids[j]],
                        documents=[batch_contents[j]],
                        embeddings=[batch_embeddings[j]],
                        metadatas=[batch_metadatas[j]]
                    )
                except Exception as e2:
                    print(f"    单条失败: {e2}")
    
    # 验证
    print(f"\n📊 最终统计:")
    print(f"  论文数量: {collection.count()}")
    print(f"  存储目录: {chroma_dir}")
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
