"""
修复ChromaDB索引问题
"""
import chromadb
import json
from pathlib import Path

project_root = Path("Q:/aeXiv论文检索系统/arxiv-rag")
chroma_dir = project_root / "data" / "embeddings" / "chroma"

print("=" * 50)
print("  修复ChromaDB索引")
print("=" * 50)

# 删除旧索引
print("\n🗑️ 清理旧索引...")
if chroma_dir.exists():
    import shutil
    shutil.rmtree(chroma_dir)
    print("  已删除旧索引目录")

chroma_dir.mkdir(parents=True, exist_ok=True)

# 加载论文数据
print("\n📄 加载论文数据...")
papers_file = project_root / "data" / "raw" / "cs_all_papers.json"
with open(papers_file, 'r', encoding='utf-8') as f:
    papers = json.load(f)
print(f"  加载 {len(papers)} 篇论文")

# 创建新集合（不使用HNSW索引）
print("\n🔄 创建新集合...")
client = chromadb.PersistentClient(path=str(chroma_dir))

# 尝试使用简单的集合配置
try:
    collection = client.create_collection(
        name="arxiv_papers",
        metadata={"hnsw:space": "cosine", "hnsw:M": 16}
    )
    print("  集合创建成功")
except Exception as e:
    print(f"  创建失败: {e}")
    # 尝试获取现有集合
    collection = client.get_or_create_collection(
        name="arxiv_papers",
        metadata={"hnsw:space": "cosine"}
    )

# 准备数据
print("\n📝 准备数据...")
documents = []
ids = []
metadatas = []

for paper in papers:
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    categories = ", ".join(paper.get("categories", []))
    
    content = f"标题: {title}\n\n分类: {categories}\n\n摘要: {abstract}"
    
    categories_list = paper.get("categories", [])
    primary_category = paper.get("primary_category", categories_list[0] if categories_list else "")
    
    metadata = {
        "title": title,
        "primary_category": primary_category,
        "published": paper.get("published", ""),
        "authors": ", ".join(paper.get("authors", []))
    }
    
    documents.append(content)
    ids.append(paper.get("id", ""))
    metadatas.append(metadata)

print(f"  准备 {len(documents)} 条记录")

# 向量化
print("\n🔄 加载嵌入模型...")
from sentence_transformers import SentenceTransformer

local_model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
model = SentenceTransformer(local_model_path, device="cpu")
print("  模型加载完成")

print("\n🔄 向量化...")
batch_size = 64
all_embeddings = []

for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    batch_embeddings = model.encode(batch, show_progress_bar=True, batch_size=batch_size)
    all_embeddings.extend(batch_embeddings.tolist())
    
    if (i + batch_size) % 1000 == 0:
        print(f"  进度: {min(i + batch_size, len(documents))}/{len(documents)}")

print(f"  向量化完成，维度: {len(all_embeddings[0])}")

# 写入ChromaDB
print("\n💾 写入ChromaDB...")
write_batch = 100
for i in range(0, len(documents), write_batch):
    batch_ids = ids[i:i+write_batch]
    batch_docs = documents[i:i+write_batch]
    batch_embeds = all_embeddings[i:i+write_batch]
    batch_metas = metadatas[i:i+write_batch]
    
    try:
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=batch_embeds,
            metadatas=batch_metas
        )
        if (i + write_batch) % 1000 == 0:
            print(f"  写入进度: {min(i + write_batch, len(documents))}/{len(documents)}")
    except Exception as e:
        print(f"  写入失败: {e}")

# 验证
print(f"\n📊 最终统计:")
print(f"  论文数量: {collection.count()}")
print(f"  存储目录: {chroma_dir}")

print("\n✅ 完成！")
